from typing import Dict, Any, List

from app.telemetry.logger import get_logger

logger = get_logger(__name__)

class ProtocolEnforcer:
    """
    Enforces content rules based on a loaded protocol card.
    """

    def __init__(self, protocol: Dict[str, Any]):
        """
        Initializes the enforcer with a set of protocol rules.

        Args:
            protocol: A dictionary loaded from a protocol YAML file.
        """
        self.protocol = protocol
        self.global_rules = protocol.get("global_rules", {})
        self.engagement_rules = protocol.get("engagement_rules", {})
        logger.info("ProtocolEnforcer initialized with rules.", extra={"rules": protocol})

    def validate_content(self, text: str) -> bool:
        """
        Validates a piece of generated text against the global protocol rules.

        Args:
            text: The text content to validate.

        Returns:
            True if the content is valid, False otherwise.
        """
        # Rule: Check for forbidden topics (simple keyword check)
        forbidden_topics = self.global_rules.get("forbidden_topics", [])
        if any(topic.lower() in text.lower() for topic in forbidden_topics):
            logger.warning(f"Content failed validation: Contains forbidden topic.", extra={"text": text})
            return False

        # Rule: Check max character length
        max_len = self.global_rules.get("max_char_length")
        if max_len and len(text) > max_len:
            logger.warning(f"Content failed validation: Exceeds max length of {max_len}.", extra={"text_length": len(text)})
            return False

        # Rule: Check if content ends with a CTA (if required)
        # Note: This is usually handled by the prompt, but this is a fallback.
        must_have_cta = self.global_rules.get("must_end_with_cta", False)
        if must_have_cta and not (text.endswith("?") or text.endswith("!")):
             # A simple check for punctuation common in CTAs.
            logger.warning("Content failed validation: Does not end with a strong CTA.", extra={"text": text})
            return False

        logger.info("Content passed protocol validation.")
        return True

    def get_dm_policy(self) -> Dict[str, Any]:
        """
        Returns the policy for sending direct messages.
        """
        return self.engagement_rules.get("dm_policy", {})

    def get_max_replies_per_user(self) -> int:
        """
        Returns the maximum number of replies allowed per user in a thread.
        """
        return self.engagement_rules.get("max_replies_per_user", 2)