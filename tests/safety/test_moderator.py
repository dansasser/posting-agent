import pytest
from app.safety.moderation import Moderator


@pytest.fixture
def sample_protocol():
    """Returns a sample protocol for testing the moderator."""
    return {
        "global_rules": {
            "forbidden_topics": ["spam", "illegal activities"],
        },
        "engagement_rules": {
            "dm_policy": {
                "trigger_templates": {
                    "help": {
                        "template_id": "support_follow_up",
                        "message": "We're here to help!",
                    },
                    "more info": {
                        "template_id": "information_request",
                        "message": "We'll send you more information shortly.",
                    },
                    "details": {
                        "template_id": "information_request",
                        "message": "Details coming your way!",
                    },
                },
                "trigger_keywords": ["legacy"],
            }
        },
    }


@pytest.fixture
def moderator(sample_protocol):
    """Returns a Moderator instance initialized with the sample protocol."""
    return Moderator(sample_protocol)


def test_is_safe_valid_text(moderator):
    """Tests that safe text passes the moderation check."""
    assert moderator.is_safe("This is a perfectly fine message.") is True


def test_is_safe_forbidden_keyword(moderator):
    """Tests that text with a forbidden keyword fails the moderation check."""
    assert moderator.is_safe("This message is considered spam.") is False
    assert moderator.is_safe("Engaging in illegal activities is not allowed.") is False


def test_is_safe_case_insensitivity(moderator):
    """Tests that the keyword check is case-insensitive."""
    assert moderator.is_safe("This is SPAM.") is False


def test_should_dm_user_trigger_keyword(moderator, sample_protocol):
    """Tests that a comment with a DM trigger keyword returns template metadata."""
    dm_policy = sample_protocol["engagement_rules"]["dm_policy"]
    match = moderator.should_dm_user("Could you send me more info?", dm_policy)
    assert match is not None
    assert match["keyword"] == "more info"
    assert match["template_id"] == "information_request"
    assert match["message"] == "We'll send you more information shortly."

    help_match = moderator.should_dm_user("I need help with my account.", dm_policy)
    assert help_match is not None
    assert help_match["keyword"] == "help"


def test_should_dm_user_no_trigger_keyword(moderator, sample_protocol):
    """Tests that a comment without a DM trigger keyword returns None."""
    dm_policy = sample_protocol["engagement_rules"]["dm_policy"]
    assert moderator.should_dm_user("This is just a regular comment.", dm_policy) is None


def test_should_dm_user_case_insensitivity(moderator, sample_protocol):
    """Tests that the DM trigger keyword check is case-insensitive."""
    dm_policy = sample_protocol["engagement_rules"]["dm_policy"]
    match = moderator.should_dm_user("Can I get some DETAILS?", dm_policy)
    assert match is not None
    assert match["keyword"] == "details"


def test_should_dm_user_legacy_keyword_support(moderator, sample_protocol):
    """Tests that legacy trigger keyword lists still return a match payload."""
    dm_policy = sample_protocol["engagement_rules"]["dm_policy"]
    match = moderator.should_dm_user("This comment uses a LEGACY trigger.", dm_policy)
    assert match is not None
    assert match["keyword"] == "legacy"
    assert match["template_id"] is None
