from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


# ── NotifyConfig Schemas ──────────────────────────────────────────────────────

class NotifyConfigBase(BaseModel):
    module_key: str
    module_name: str
    project_name: Optional[str] = None
    chat_id: str
    group_name: Optional[str] = None
    actions: str                          # "CREATE,UPDATE,DELETE"
    enable_send_notify: bool = True

class NotifyConfigCreate(NotifyConfigBase):
    id: Optional[UUID] = None

class NotifyConfigUpdate(BaseModel):
    id: UUID
    module_key: Optional[str] = None
    module_name: Optional[str] = None
    project_name: Optional[str] = None
    chat_id: Optional[str] = None
    group_name: Optional[str] = None
    actions: Optional[str] = None
    enable_send_notify: Optional[bool] = None

class NotifyConfigResponse(NotifyConfigBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── NotifyLog Schemas ─────────────────────────────────────────────────────────

class NotifyLogResponse(BaseModel):
    id: UUID
    config_id: Optional[UUID] = None
    action: str
    module_key: str
    module_name: str
    project_name: Optional[str] = None
    chat_id: str
    group_name: Optional[str] = None
    performer: str
    details: str
    message_id: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Notify Request (API endpoint) ────────────────────────────────────────────

class TelegramNotifyRequest(BaseModel):
    action: str                           # CREATE / UPDATE / DELETE / PROCESS
    module_key: str                       # customers, daily_purchases...
    details: str                          # Chi tiết hành vi
