from typing import Dict, Any, List, Optional

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

    def get_dm_triggers(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns the mapping of DM trigger keywords to template metadata.
        """
        dm_policy = self.get_dm_policy()
        return dm_policy.get("trigger_templates", {})

    def match_dm_trigger(self, comment_text: str) -> Optional[Dict[str, Any]]:
        """
        Finds the DM template configuration that matches the user's comment.

        Args:
            comment_text: The text of the user's comment.

        Returns:
            A dictionary containing the matched keyword, template identifier, and
            message body when a trigger is found. Returns None if no trigger
            matches the comment.
        """
        comment_lower = comment_text.lower()
        for keyword, template_config in self.get_dm_triggers().items():
            if keyword.lower() in comment_lower:
                match_payload = {
                    "keyword": keyword,
                    "template_id": template_config.get("template_id"),
                    "message": template_config.get("message"),
                }
                logger.info(
                    "DM trigger matched.",
                    extra={"keyword": keyword, "template": match_payload},
                )
                return match_payload

        # Fallback to legacy trigger keywords if configured without templates.
        legacy_keywords = self.get_dm_policy().get("trigger_keywords", [])
        for keyword in legacy_keywords:
            if keyword.lower() in comment_lower:
                logger.info(
                    "Legacy DM trigger matched.",
                    extra={"keyword": keyword},
                )
                return {"keyword": keyword, "template_id": None, "message": None}

        return None
