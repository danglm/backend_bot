from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import datetime
import uuid

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String, nullable=True)                 # ID Nhân viên
    project_id = Column(UUID(as_uuid=True), nullable=True)     # UUID của dự án
    group_chat_id = Column(String, index=True)                 # ID Nhóm Telegram nhận task
    message_id = Column(Integer, nullable=True)                # ID tin nhắn bot gửi trong nhóm (để update/xóa)
    
    assigner = Column(String)                                  # Người giao việc (Tên quản lý)
    assignee = Column(String)                                  # Người được giao (Nhân viên)
    content = Column(Text)                                     # Nội dung công việc
    start_date = Column(String)                                # Ngày bắt đầu
    end_date = Column(String)                                  # Ngày kết thúc
    cycle = Column(String)                                     # Chu kỳ (VD: 1 tháng, 1 tuần)
    
    status = Column(String, default="PENDING")                 # Trạng thái: PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
