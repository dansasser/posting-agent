import time
from collections import deque
from typing import Dict

from app.telemetry.logger import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """
    A simple rate limiter to control the frequency of actions.
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
    Manages rate limits on a per-user basis.
    """

    def __init__(self, max_actions: int, period_hours: int):
        """
        Initializes the per-user rate limiter.

        Args:
            max_actions: Maximum number of actions per user in the period.
            period_hours: The time period in hours.
        """
        self.user_actions: Dict[str, deque] = {}
        self.max_actions = max_actions
        self.period_seconds = period_hours * 3600

    def can_perform_action(self, user_id: str) -> bool:
        """
        Checks if a user can perform an action based on their history.

        Args:
            user_id: The unique identifier for the user.

        Returns:
            True if the action is allowed, False otherwise.
        """
        now = time.time()
        if user_id not in self.user_actions:
            self.user_actions[user_id] = deque()

        user_deque = self.user_actions[user_id]
        # Clean up old actions
        while user_deque and user_deque[0] <= now - self.period_seconds:
            user_deque.popleft()

        if len(user_deque) < self.max_actions:
            return True

        logger.warning(f"Rate limit exceeded for user {user_id}.")
        return False

    def record_action(self, user_id: str):
        """
        Records that an action was performed by a user.

        Args:
            user_id: The unique identifier for the user.
        """
        if self.can_perform_action(user_id):
            self.user_actions[user_id].append(time.time())
            logger.info(f"Action recorded for user {user_id}.")
        else:
            logger.error(f"Attempted to record action for user {user_id} who is rate-limited.")