import uuid
import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class PmBoard(Base):
    """Bảng dự án / board Kanban"""
    __tablename__ = "pm_boards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_name = Column(String, nullable=False)
    board_key = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    owner_id = Column(String, nullable=False)
    default_assignee_id = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class PmColumn(Base):
    """Cột trạng thái trong board Kanban"""
    __tablename__ = "pm_columns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("pm_boards.id", ondelete="CASCADE"), nullable=False, index=True)
    column_name = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    column_type = Column(String, default="TODO")  # TODO, IN_PROGRESS, DONE, CANCELLED
    wip_limit = Column(Integer, nullable=True)
    color = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)


class PmLabel(Base):
    """Nhãn (tag) phân loại task"""
    __tablename__ = "pm_labels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("pm_boards.id", ondelete="CASCADE"), nullable=False, index=True)
    label_name = Column(String, nullable=False)
    color = Column(String, nullable=False)


class PmTask(Base):
    """Bảng công việc (Task)"""
    __tablename__ = "pm_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_code = Column(String, nullable=False, unique=True, index=True)
    board_id = Column(UUID(as_uuid=True), ForeignKey("pm_boards.id", ondelete="CASCADE"), nullable=False, index=True)
    column_id = Column(UUID(as_uuid=True), ForeignKey("pm_columns.id", ondelete="RESTRICT"), nullable=False, index=True)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("pm_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW
    task_type = Column(String, default="TASK")   # TASK, BUG, STORY, EPIC, SUB_TASK
    assignee_id = Column(String, nullable=True, index=True)
    reporter_id = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    position = Column(Integer, default=0)
    status = Column(String, default="OPEN")  # OPEN, IN_PROGRESS, DONE, CANCELLED, BLOCKED
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class PmTaskLabel(Base):
    """Liên kết giữa Task và Label (Many-to-Many)"""
    __tablename__ = "pm_task_labels"
    __table_args__ = (UniqueConstraint("task_id", "label_id", name="uq_pm_task_label"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("pm_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    label_id = Column(UUID(as_uuid=True), ForeignKey("pm_labels.id", ondelete="CASCADE"), nullable=False, index=True)


class PmTaskComment(Base):
    """Bình luận trong Task"""
    __tablename__ = "pm_task_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("pm_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("pm_task_comments.id", ondelete="CASCADE"), nullable=True)
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class PmTaskAttachment(Base):
    """File đính kèm trong Task"""
    __tablename__ = "pm_task_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("pm_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_id = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.now)


class PmTaskActivityLog(Base):
    """Lịch sử hoạt động trên Task"""
    __tablename__ = "pm_task_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("pm_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # CREATED, UPDATED, STATUS_CHANGED, ASSIGNED, COMMENTED, ATTACHMENT_ADDED, ATTACHMENT_REMOVED, LABEL_ADDED, LABEL_REMOVED, MOVED
    field_name = Column(String, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
