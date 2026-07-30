from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime


# ── ScheduledNotifyConfig Schemas ─────────────────────────────────────────────

class ScheduledNotifyConfigBase(BaseModel):
    module_key: str                                    # "credit", "rental", "rosca", "general"
    module_name: str                                   # "Tín Dụng", "Cho Thuê", "Hụi", "Chung"
    notify_type: str                                   # "credit_interest", "rental_payment", ...
    chat_id: str                                       # Chat ID nhóm Telegram đích
    group_name: Optional[str] = None
    schedule_type: str                                 # "daily", "weekly", "monthly", "yearly", "specific_date"
    schedule_hour: int = 8
    schedule_minute: int = 0
    schedule_day_of_week: Optional[int] = None         # 0=Mon..6=Sun
    schedule_day_of_month: Optional[int] = None        # 1-31
    schedule_month: Optional[int] = None               # 1-12
    schedule_specific_date: Optional[date] = None
    message_template: Optional[str] = None
    is_enabled: bool = True
    max_retry_days: int = 7
    escalate_to_chat_id: Optional[str] = None
    escalate_after_days: int = 7
    filter_conditions: Optional[str] = None            # JSON string
    reference_id: Optional[str] = None                 # contract_id, real_estate_id, rosca_code...
    reference_name: Optional[str] = None               # Tên KH, tên BĐS, tên dây hụi (hiển thị)
    created_by: Optional[str] = None


class ScheduledNotifyConfigCreate(ScheduledNotifyConfigBase):
    id: Optional[UUID] = None


class ScheduledNotifyConfigUpdate(BaseModel):
    id: UUID
    module_key: Optional[str] = None
    module_name: Optional[str] = None
    notify_type: Optional[str] = None
    chat_id: Optional[str] = None
    group_name: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_hour: Optional[int] = None
    schedule_minute: Optional[int] = None
    schedule_day_of_week: Optional[int] = None
    schedule_day_of_month: Optional[int] = None
    schedule_month: Optional[int] = None
    schedule_specific_date: Optional[date] = None
    message_template: Optional[str] = None
    is_enabled: Optional[bool] = None
    max_retry_days: Optional[int] = None
    escalate_to_chat_id: Optional[str] = None
    escalate_after_days: Optional[int] = None
    filter_conditions: Optional[str] = None
    reference_id: Optional[str] = None
    reference_name: Optional[str] = None
    created_by: Optional[str] = None


class ScheduledNotifyConfigResponse(ScheduledNotifyConfigBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── ScheduledNotifyLog Schemas ────────────────────────────────────────────────

class ScheduledNotifyLogResponse(BaseModel):
    id: UUID
    config_id: Optional[UUID] = None
    module_key: str
    notify_type: str
    chat_id: str
    group_name: Optional[str] = None
    reference_id: Optional[str] = None
    reference_name: Optional[str] = None
    message_id: Optional[int] = None
    message_content: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True
