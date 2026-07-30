import enum
import uuid
import datetime
from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class ScheduleType(str, enum.Enum):
    DAILY = "daily"                      # Hàng ngày
    WEEKLY = "weekly"                    # Hàng tuần
    MONTHLY = "monthly"                  # Hàng tháng
    YEARLY = "yearly"                    # Hàng năm
    SPECIFIC_DATE = "specific_date"      # Ngày cụ thể


class ScheduledNotifyConfig(Base):
    """Cấu hình thông báo lên lịch gửi đến nhóm Telegram."""
    __tablename__ = "scheduled_notify_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Module binding ────────────────────
    module_key = Column(String, nullable=False, index=True)       # "credit", "rental", "rosca", "general"
    module_name = Column(String, nullable=False)                  # "Tín Dụng", "Cho Thuê", "Hụi", "Chung"
    notify_type = Column(String, nullable=False, index=True)      # "credit_interest", "rental_payment", ...

    # ── Target ────────────────────────────
    chat_id = Column(String, nullable=False)                      # Chat ID nhóm Telegram đích
    group_name = Column(String, nullable=True)                    # Tên nhóm (hiển thị)

    # ── Schedule ──────────────────────────
    schedule_type = Column(Enum(ScheduleType), nullable=False)
    schedule_hour = Column(Integer, default=8)                    # Giờ gửi (0-23)
    schedule_minute = Column(Integer, default=0)                  # Phút gửi (0-59)
    schedule_day_of_week = Column(Integer, nullable=True)         # 0=Mon..6=Sun (cho weekly)
    schedule_day_of_month = Column(Integer, nullable=True)        # 1-31 (cho monthly)
    schedule_month = Column(Integer, nullable=True)               # 1-12 (cho yearly)
    schedule_specific_date = Column(Date, nullable=True)          # Ngày cụ thể

    # ── Message template ──────────────────
    message_template = Column(Text, nullable=True)                # Template tùy chỉnh (optional, hỗ trợ placeholder)

    # ── Control ───────────────────────────
    is_enabled = Column(Boolean, default=True)
    max_retry_days = Column(Integer, default=7)                   # Số ngày nhắc lại tối đa
    escalate_to_chat_id = Column(String, nullable=True)           # Chat ID leo thang (main group)
    escalate_after_days = Column(Integer, default=7)              # Leo thang sau N ngày

    # ── Filter conditions (JSON) ──────────
    filter_conditions = Column(Text, nullable=True)               # JSON: {"status": "active", ...}

    # ── Reference binding ─────────────────
    reference_id = Column(String, nullable=True, index=True)      # contract_id, real_estate_id, rosca_code...
    reference_name = Column(String, nullable=True)                # Tên KH, tên BĐS, tên dây hụi (hiển thị)

    # ── Metadata ──────────────────────────
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class ScheduledNotifyLog(Base):
    """Log lịch sử gửi thông báo lên lịch."""
    __tablename__ = "scheduled_notify_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), nullable=True)

    module_key = Column(String, nullable=False, index=True)
    notify_type = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    group_name = Column(String, nullable=True)

    # ── Reference ─────────────────────────
    reference_id = Column(String, nullable=True)                  # contract_id, rosca_code, etc.
    reference_name = Column(String, nullable=True)                # Tên khách hàng, tên dây hụi

    # ── Result ────────────────────────────
    message_id = Column(Integer, nullable=True)                   # Telegram message ID
    message_content = Column(Text, nullable=True)                 # Nội dung đã gửi
    status = Column(String, nullable=False)                       # SUCCESS / FAILED / SKIPPED
    error_message = Column(Text, nullable=True)

    # ── Timing ────────────────────────────
    scheduled_at = Column(DateTime, nullable=True)                # Thời gian lên lịch
    sent_at = Column(DateTime, default=datetime.datetime.now)     # Thời gian gửi thực tế
