from sqlalchemy import Column, Integer, String, DateTime, func, Boolean, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    facebook_post_id = Column(String, unique=True, index=True, nullable=False)
    topic = Column(String, nullable=False)
    post_type = Column(String, nullable=False) # "thread" or "longform"
    is_active_for_engagement = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Post(id={self.id}, facebook_post_id='{self.facebook_post_id}')>"


class UserAction(Base):
    __tablename__ = "user_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    action_type = Column(String, nullable=False) # e.g., "dm", "reply"
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<UserAction(id={self.id}, user_id='{self.user_id}', action_type='{self.action_type}')>"


class DirectMessageAudit(Base):
    __tablename__ = "direct_message_audit"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    comment_id = Column(String, nullable=False)
    keyword = Column(String, nullable=False)
    template_id = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    platform_message_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return (
            "<DirectMessageAudit(id={id}, user_id='{user_id}', keyword='{keyword}', "
            "template_id='{template_id}')>"
        ).format(
            id=self.id,
            user_id=self.user_id,
            keyword=self.keyword,
            template_id=self.template_id,
        )
