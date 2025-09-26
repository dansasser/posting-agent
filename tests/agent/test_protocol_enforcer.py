import pytest
from app.agent.protocol_enforcer import ProtocolEnforcer

@pytest.fixture
def sample_protocol():
    """Returns a sample protocol for testing."""
    return {
        "global_rules": {
            "forbidden_topics": ["hate speech", "violence"],
            "max_char_length": 100,
            "must_end_with_cta": True,
        },
        "engagement_rules": {
            "dm_policy": {"trigger_keywords": ["dm me"]},
            "max_replies_per_user": 3,
        },
    }

@pytest.fixture
def enforcer(sample_protocol):
    """Returns a ProtocolEnforcer instance initialized with the sample protocol."""
    return ProtocolEnforcer(sample_protocol)

def test_validate_content_valid(enforcer):
    """Tests that valid content passes validation."""
    assert enforcer.validate_content("This is a valid post!") is True
    assert enforcer.validate_content("What do you think?") is True

def test_validate_content_forbidden_topic(enforcer):
    """Tests that content with a forbidden topic fails validation."""
    assert enforcer.validate_content("This content contains violence.") is False
    assert enforcer.validate_content("A post about hate speech.") is False

def test_validate_content_exceeds_max_length(enforcer):
    """Tests that content exceeding the max character length fails validation."""
    long_text = "a" * 101
    assert enforcer.validate_content(long_text) is False

def test_validate_content_missing_cta(enforcer):
    """Tests that content missing a CTA fails validation when it's required."""
    assert enforcer.validate_content("This is just a statement.") is False

def test_validate_content_valid_without_cta_rule(sample_protocol):
    """Tests that content without a CTA is valid if the rule is disabled."""
    sample_protocol["global_rules"]["must_end_with_cta"] = False
    enforcer = ProtocolEnforcer(sample_protocol)
    assert enforcer.validate_content("This is just a statement.") is True

def test_get_dm_policy(enforcer):
    """Tests that the correct DM policy is returned."""
    expected_policy = {"trigger_keywords": ["dm me"]}
    assert enforcer.get_dm_policy() == expected_policy

def test_get_max_replies_per_user(enforcer):
    """Tests that the correct max replies per user is returned."""
    assert enforcer.get_max_replies_per_user() == 3