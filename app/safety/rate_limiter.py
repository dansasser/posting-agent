import time
from collections import deque
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.telemetry.logger import get_logger
from app.database.models import UserAction

logger = get_logger(__name__)

class RateLimiter:
    """
    A simple in-memory rate limiter to control the frequency of actions.
    Used for staggering comments within a single job execution.
    """

    def __init__(self, max_calls: int, period_seconds: int):
        """
        Initializes the rate limiter.

        Args:
            max_calls: Maximum number of calls allowed within the period.
            period_seconds: The time period in seconds.
        """
        self.calls = deque()
        self.max_calls = max_calls
        self.period_seconds = period_seconds

    def wait(self):
        """
        Blocks until a call can be made without exceeding the rate limit.
        """
        while True:
            now = time.time()
            # Remove calls that are outside the current time window
            while self.calls and self.calls[0] <= now - self.period_seconds:
                self.calls.popleft()

            if len(self.calls) < self.max_calls:
                break

            # Calculate sleep time until the oldest call expires
            sleep_time = self.calls[0] + self.period_seconds - now
            logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)

        self.calls.append(time.time())
        logger.debug("Rate limit check passed.")


class PerUserRateLimiter:
    """
    Manages rate limits on a per-user basis using the database.
    """

    def __init__(self, max_actions: int, period_hours: int, action_type: str):
        """
        Initializes the per-user rate limiter.

        Args:
            max_actions: Maximum number of actions per user in the period.
            period_hours: The time period in hours.
            action_type: The type of action being limited (e.g., "dm", "reply").
        """
        self.max_actions = max_actions
        self.period_seconds = period_hours * 3600
        self.action_type = action_type
        logger.info(
            f"PerUserRateLimiter for action '{self.action_type}' configured: "
            f"max {self.max_actions} actions per {period_hours} hours."
        )

    def can_perform_action(self, user_id: str, db: Session) -> bool:
        """
        Checks if a user can perform an action based on their history in the database.

        Args:
            user_id: The unique identifier for the user.
            db: The database session.

        Returns:
            True if the action is allowed, False otherwise.
        """
        period_start = datetime.utcnow() - timedelta(seconds=self.period_seconds)

        action_count = (
            db.query(UserAction)
            .filter(
                UserAction.user_id == user_id,
                UserAction.action_type == self.action_type,
                UserAction.created_at >= period_start,
            )
            .count()
        )

        if action_count < self.max_actions:
            return True

        logger.warning(
            f"Rate limit exceeded for user {user_id} for action '{self.action_type}'. "
            f"Found {action_count} actions in the last {self.period_seconds / 3600} hours."
        )
        return False

    def record_action(self, user_id: str, db: Session):
        """
        Records that an action was performed by a user in the database.
        The caller is responsible for committing the transaction.

        Args:
            user_id: The unique identifier for the user.
            db: The database session.
        """
        if self.can_perform_action(user_id, db):
            new_action = UserAction(user_id=user_id, action_type=self.action_type)
            db.add(new_action)
            logger.info(f"Action '{self.action_type}' for user {user_id} added to session. Awaiting commit.")
        else:
            logger.error(f"Attempted to record action for user {user_id} who is rate-limited.")