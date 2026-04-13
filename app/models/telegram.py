from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import datetime
import uuid


class MemberActivityLog(Base):
    __tablename__ = "member_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(String, index=True)
    group_name = Column(String)
    user_id = Column(String, index=True)
    username = Column(String)
    action = Column(String) # JOIN, LEAVE, KICK
    admin_id = Column(String, nullable=True) # ID of the user who performed the action (e.g., KICK)
    admin_username = Column(String, nullable=True) # Username/Name of the admin/user
    timestamp = Column(DateTime, default=datetime.datetime.now)


class TelegramProjectMember(Base):
    __tablename__ = "telegram_project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True))
    chat_id = Column(String)
    group_name = Column(String, nullable=True)
    user_id = Column(String)
    user_name = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    role = Column(String) # main, member
    slot_name = Column(String, nullable=True) # admin_01, member_12, etc.
    is_bot = Column(Boolean, default=False)
    member_status = Column(String) # OWNER, ADMINISTRATOR, MEMBER, LEFT, KICKED
    custom_title = Column(String, nullable=True)
    first_seen_at = Column(DateTime, default=datetime.datetime.now)
    last_seen_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    last_seen_by = Column(String, nullable=True)
