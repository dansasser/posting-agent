import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent.protocol_enforcer import ProtocolEnforcer
from app.database.models import Base, DirectMessageAudit, UserAction
from app.orchestrator.engagement import EngagementManager
from app.safety.moderation import Moderator


@pytest.fixture
def protocol_card():
    return {
        "global_rules": {},
        "engagement_rules": {
            "dm_policy": {
                "trigger_templates": {
                    "help": {
                        "template_id": "support_follow_up",
                        "message": "Hi! We'll get you the help you need.",
                    }
                },
                "per_user_dm_limit_hours": 24,
            },
            "max_replies_per_user": 2,
        },
    }


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def engagement_manager(protocol_card, mocker):
    fb_client = mocker.Mock()
    fb_client.page_id = "page123"
    moderator = Moderator(protocol_card)
    enforcer = ProtocolEnforcer(protocol_card)
    manager = EngagementManager(fb_client, moderator, enforcer)
    return manager


def test_scan_and_engage_sends_dm(protocol_card, engagement_manager, db_session):
    engagement_manager.fb_client.get_comments.return_value = {
        "data": [
            {
                "id": "comment1",
                "message": "I really need help with this.",
                "from": {"id": "user123"},
            }
        ]
    }
    engagement_manager.fb_client.send_direct_message.return_value = "mid.1"

    engagement_manager.scan_and_engage("post123", db_session)

    engagement_manager.fb_client.send_direct_message.assert_called_once_with(
        "user123", "Hi! We'll get you the help you need."
    )

    actions = db_session.query(UserAction).all()
    assert len(actions) == 1
    assert actions[0].action_type == "dm"

    audits = db_session.query(DirectMessageAudit).all()
    assert len(audits) == 1
    assert audits[0].user_id == "user123"
    assert audits[0].keyword == "help"
    assert audits[0].template_id == "support_follow_up"


def test_scan_and_engage_respects_rate_limit(protocol_card, engagement_manager, db_session):
    db_session.add(UserAction(user_id="user123", action_type="dm"))
    db_session.commit()

    engagement_manager.fb_client.get_comments.return_value = {
        "data": [
            {
                "id": "comment1",
                "message": "Can you help again?",
                "from": {"id": "user123"},
            }
        ]
    }

    engagement_manager.scan_and_engage("post123", db_session)

    engagement_manager.fb_client.send_direct_message.assert_not_called()
    audits = db_session.query(DirectMessageAudit).all()
    assert len(audits) == 0
