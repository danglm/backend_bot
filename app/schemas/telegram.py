from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

# Telegram Project Member Schemas
class TelegramProjectMemberBase(BaseModel):
    project_id: UUID4
    chat_id: str
    group_name: Optional[str] = None
    user_id: str
    user_name: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    slot_name: Optional[str] = None
    is_bot: Optional[bool] = False
    member_status: str
    custom_title: Optional[str] = None
    parent_id: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    last_seen_by: Optional[str] = None

class TelegramProjectMemberCreate(TelegramProjectMemberBase):
    pass

class TelegramProjectMember(TelegramProjectMemberBase):
    id: UUID4

    class Config:
        from_attributes = True

class TelegramProjectMemberUpdate(BaseModel):
    id: UUID4
    project_id: Optional[UUID4] = None
    chat_id: Optional[str] = None
    group_name: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    slot_name: Optional[str] = None
    is_bot: Optional[bool] = None
    member_status: Optional[str] = None
    custom_title: Optional[str] = None
    parent_id: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    last_seen_by: Optional[str] = None


# Telegram Group Info Schema (for get-telegram-groups API)
class TelegramGroupInfo(BaseModel):
    chat_id: str
    group_name: Optional[str] = None
    member_count: int = 0
    custom_title: Optional[str] = None
