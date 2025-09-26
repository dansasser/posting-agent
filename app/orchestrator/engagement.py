import time
from typing import Set

from sqlalchemy.orm import Session

from app.adapters.facebook_client import FacebookClient
from app.safety.moderation import Moderator
from app.safety.rate_limiter import PerUserRateLimiter
from app.agent.protocol_enforcer import ProtocolEnforcer
from app.telemetry.logger import get_logger
from app.database.models import Post, DirectMessageAudit
from app.database.engine import SessionLocal

logger = get_logger(__name__)

class EngagementManager:
    """
    Manages the engagement loop for monitoring and responding to comments.
    This version uses the database for stateful operations.
    """

    def __init__(
        self,
        fb_client: FacebookClient,
        moderator: Moderator,
        protocol_enforcer: ProtocolEnforcer,
    ):
        """
        Initializes the EngagementManager.

        Args:
            fb_client: The client for interacting with the Facebook API.
            moderator: The content moderation instance.
            protocol_enforcer: The enforcer for engagement rules.
        """
        self.fb_client = fb_client
        self.moderator = moderator
        self.protocol_enforcer = protocol_enforcer

        dm_policy = self.protocol_enforcer.get_dm_policy()
        self.dm_limiter = PerUserRateLimiter(
            max_actions=1,
            period_hours=dm_policy.get("per_user_dm_limit_hours", 24),
            action_type="dm",
        )

        reply_limit = self.protocol_enforcer.get_max_replies_per_user()
        self.reply_limiter = PerUserRateLimiter(
            max_actions=reply_limit,
            period_hours=24,
            action_type="reply",
        )

        self.processed_comment_ids: Set[str] = set()

    def scan_and_engage(self, post_id: str, db: Session):
        """
        Scans a post for new comments and engages based on the protocol.

        Args:
            post_id: The ID of the Facebook post to monitor.
            db: The database session.
        """
        logger.info(f"Scanning post {post_id} for new comments.")
        comments_data = self.fb_client.get_comments(post_id)

        if not comments_data or "data" not in comments_data:
            logger.info(f"No comments found for post {post_id}.")
            return

        for comment in comments_data["data"]:
            comment_id = comment.get("id")
            comment_text = comment.get("message", "")
            user_info = comment.get("from", {})
            user_id = user_info.get("id")

            if not user_id or comment_id in self.processed_comment_ids:
                continue

            if user_id == self.fb_client.page_id:
                self.processed_comment_ids.add(comment_id)
                continue

            logger.info(f"Processing new comment {comment_id} from user {user_id}.")

            dm_match = self.protocol_enforcer.match_dm_trigger(comment_text)
            if dm_match:
                if not dm_match.get("message"):
                    logger.warning(
                        "DM trigger matched but no message configured.",
                        extra={"comment_id": comment_id, "keyword": dm_match.get("keyword")},
                    )
                elif self.dm_limiter.can_perform_action(user_id, db):
                    logger.info(
                        f"DM action triggered for user {user_id}. Sending message.",
                        extra={"comment_id": comment_id, "keyword": dm_match.get("keyword")},
                    )
                    try:
                        message_id = self.fb_client.send_direct_message(
                            user_id, dm_match["message"]
                        )
                        if message_id:
                            self.dm_limiter.record_action(user_id, db)
                            audit_record = DirectMessageAudit(
                                user_id=user_id,
                                comment_id=comment_id,
                                keyword=dm_match.get("keyword"),
                                template_id=dm_match.get("template_id"),
                                message=dm_match.get("message", ""),
                                platform_message_id=message_id,
                            )
                            db.add(audit_record)
                            db.commit()
                            logger.info(
                                "DM sent and recorded.",
                                extra={
                                    "user_id": user_id,
                                    "comment_id": comment_id,
                                    "message_id": message_id,
                                },
                            )
                            self.processed_comment_ids.add(comment_id)
                            continue
                        logger.error(
                            "Failed to send DM despite trigger match.",
                            extra={"user_id": user_id, "comment_id": comment_id},
                        )
                    except Exception as exc:
                        logger.error(
                            "Exception occurred while sending DM.",
                            extra={"user_id": user_id, "comment_id": comment_id, "error": str(exc)},
                            exc_info=True,
                        )
                        db.rollback()
                        self.processed_comment_ids.add(comment_id)
                        continue
                else:
                    logger.info(
                        "User is rate limited for DMs.",
                        extra={"user_id": user_id, "comment_id": comment_id},
                    )
                    self.processed_comment_ids.add(comment_id)
                    continue

            self.processed_comment_ids.add(comment_id)
            logger.info(f"Finished processing comment {comment_id}. No action taken.")

    def run_engagement_loop(self, interval_seconds: int = 60):
        """
        Runs a continuous loop to scan active posts for engagement.

        Args:
            interval_seconds: The delay between each scan cycle.
        """
        logger.info("Starting persistent engagement loop.")
        while True:
            db = SessionLocal()
            try:
                active_posts = db.query(Post).filter(Post.is_active_for_engagement == True).all()
                if not active_posts:
                    logger.info("No active posts to monitor for engagement.")
                else:
                    logger.info(f"Found {len(active_posts)} active posts to scan.")

                for post in active_posts:
                    try:
                        self.scan_and_engage(post.facebook_post_id, db)
                    except Exception as e:
                        logger.error(f"Error during engagement scan for post {post.facebook_post_id}: {e}", exc_info=True)
            finally:
                db.close()

            logger.info(f"Engagement scan complete. Waiting {interval_seconds} seconds.")
            time.sleep(interval_seconds)
