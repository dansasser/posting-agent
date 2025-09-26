import time
from typing import Set

from app.adapters.facebook_client import FacebookClient
from app.safety.moderation import Moderator
from app.safety.rate_limiter import PerUserRateLimiter
from app.agent.protocol_enforcer import ProtocolEnforcer
from app.telemetry.logger import get_logger

logger = get_logger(__name__)

class EngagementManager:
    """
    Manages the engagement loop for monitoring and responding to comments.
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
            max_actions=1,  # Max 1 DM per user
            period_hours=dm_policy.get("per_user_dm_limit_hours", 24),
        )

        reply_limit = self.protocol_enforcer.get_max_replies_per_user()
        self.reply_limiter = PerUserRateLimiter(
            max_actions=reply_limit,
            period_hours=24, # Limit replies over a 24-hour period
        )

        self.processed_comment_ids: Set[str] = set()

    def scan_and_engage(self, post_id: str):
        """
        Scans a post for new comments and engages based on the protocol.

        Args:
            post_id: The ID of the Facebook post to monitor.
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

            # Skip if comment is already processed or has no user info
            if not user_id or comment_id in self.processed_comment_ids:
                continue

            # Avoid replying to our own page
            if user_id == self.fb_client.page_id:
                self.processed_comment_ids.add(comment_id)
                continue

            logger.info(f"Processing new comment {comment_id} from user {user_id}.")

            # 1. Decide if a DM should be sent
            dm_policy = self.protocol_enforcer.get_dm_policy()
            if self.moderator.should_dm_user(comment_text, dm_policy):
                if self.dm_limiter.can_perform_action(user_id):
                    # NOTE: The Graph API does not allow Pages to initiate DMs.
                    # This is a placeholder for a future implementation where
                    # this might be possible (e.g., via Instagram DMs).
                    # For now, we just log the intent.
                    logger.info(f"DM action triggered for user {user_id}. Logging intent.")
                    self.dm_limiter.record_action(user_id)
                    # Once a DM is sent, we typically don't also reply publicly.
                    self.processed_comment_ids.add(comment_id)
                    continue

            # 2. Decide if a public reply should be sent
            # Current policy is not to send automated replies to avoid being spammy.
            # This can be extended with more sophisticated logic, e.g., using an LLM
            # to generate a relevant reply if the comment asks a question.
            # For now, we just log that we processed it.

            self.processed_comment_ids.add(comment_id)
            logger.info(f"Finished processing comment {comment_id}. No action taken.")

    def run_engagement_loop(self, tracked_post_ids: list[str], interval_seconds: int = 60):
        """
        Runs a continuous loop to scan a list of posts for engagement.

        Args:
            tracked_post_ids: A list of post IDs to monitor.
            interval_seconds: The delay between each scan cycle.
        """
        logger.info(f"Starting engagement loop for posts: {tracked_post_ids}")
        while True:
            for post_id in tracked_post_ids:
                try:
                    self.scan_and_engage(post_id)
                except Exception as e:
                    logger.error(f"Error during engagement scan for post {post_id}: {e}", exc_info=True)

            logger.info(f"Engagement scan complete. Waiting {interval_seconds} seconds.")
            time.sleep(interval_seconds)