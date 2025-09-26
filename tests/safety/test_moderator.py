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
                "trigger_keywords": ["help", "more info", "details"],
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
    """Tests that a comment with a DM trigger keyword returns True."""
    dm_policy = sample_protocol["engagement_rules"]["dm_policy"]
    assert moderator.should_dm_user("Could you send me more info?", dm_policy) is True
    assert moderator.should_dm_user("I need help with my account.", dm_policy) is True

def test_should_dm_user_no_trigger_keyword(moderator, sample_protocol):
    """Tests that a comment without a DM trigger keyword returns False."""
    dm_policy = sample_protocol["engagement_rules"]["dm_policy"]
    assert moderator.should_dm_user("This is just a regular comment.", dm_policy) is False

def test_should_dm_user_case_insensitivity(moderator, sample_protocol):
    """Tests that the DM trigger keyword check is case-insensitive."""
    dm_policy = sample_protocol["engagement_rules"]["dm_policy"]
    assert moderator.should_dm_user("Can I get some DETAILS?", dm_policy) is True