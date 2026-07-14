from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid
import datetime


class NotifyConfig(Base):
    """Cấu hình gửi thông báo Telegram cho từng tính năng."""
    __tablename__ = "notify_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_key = Column(String, nullable=False, index=True)      # customers, daily_purchases...
    module_name = Column(String, nullable=False)                  # Quản lý Khách hàng
    project_name = Column(String, nullable=True)                  # Tiến Nga
    chat_id = Column(String, nullable=False)                      # -1003991830930
    group_name = Column(String, nullable=True)                    # Test - Nhóm TN02
    actions = Column(String, nullable=False)                      # CREATE,UPDATE,DELETE
    enable_send_notify = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class NotifyLog(Base):
    """Log lịch sử gửi thông báo Telegram."""
    __tablename__ = "notify_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), nullable=True)        # FK → notify_configs.id
    action = Column(String, nullable=False)                       # CREATE / UPDATE / DELETE / PROCESS
    module_key = Column(String, nullable=False, index=True)
    module_name = Column(String, nullable=False)
    project_name = Column(String, nullable=True)
    chat_id = Column(String, nullable=False)
    group_name = Column(String, nullable=True)
    performer = Column(String, nullable=False)                    # Credential.employee_id (VD: TN001)
    details = Column(Text, nullable=False)
    message_id = Column(Integer, nullable=True)                   # ID tin nhắn Telegram (null nếu FAILED)
    status = Column(String, nullable=False)                       # SUCCESS / FAILED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
