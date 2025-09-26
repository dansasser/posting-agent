from typing import List, Dict, Any

from app.telemetry.logger import get_logger

logger = get_logger(__name__)

class Moderator:
    """
    A simple content moderation system.
    """

    def __init__(self, protocol: Dict[str, Any]):
        """
        Initializes the moderator with rules from a protocol.

        Args:
            protocol: A dictionary loaded from a protocol YAML file.
        """
        self.global_rules = protocol.get("global_rules", {})
        self.forbidden_keywords = [
            kw.lower() for kw in self.global_rules.get("forbidden_topics", [])
        ]
        logger.info("Moderator initialized.", extra={"forbidden_keywords": self.forbidden_keywords})

    def is_safe(self, text: str) -> bool:
        """
        Checks if a given text is safe according to the moderation rules.
        This is a basic implementation that checks for keywords.

        Args:
            text: The text to check.

        Returns:
            True if the text is deemed safe, False otherwise.
        """
        text_lower = text.lower()
        for keyword in self.forbidden_keywords:
            if keyword in text_lower:
                logger.warning(
                    f"Moderation check failed. Found forbidden keyword: '{keyword}'.",
                    extra={"text": text}
                )
                return False

        logger.info("Text passed moderation check.")
        return True

    def should_dm_user(self, comment_text: str, dm_policy: Dict[str, Any]) -> bool:
        """
        Determines whether a direct message should be sent based on comment content.

        Args:
            comment_text: The user's comment.
            dm_policy: The direct message policy from the protocol.

        Returns:
            True if a DM should be sent, False otherwise.
        """
        trigger_keywords = dm_policy.get("trigger_keywords", [])
        comment_lower = comment_text.lower()

        if any(keyword.lower() in comment_lower for keyword in trigger_keywords):
            logger.info("DM trigger keyword found in comment.", extra={"comment": comment_text})
            return True

        return False