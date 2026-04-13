from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

# Telegram Project Member Schemas
class TelegramProjectMemberBase(BaseModel):
    project_id: UUID4
    chat_id: str
    user_id: str
    user_name: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    slot_name: Optional[str] = None
    is_bot: Optional[bool] = False
    member_status: str
    custom_title: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    last_seen_by: Optional[str] = None

class TelegramProjectMemberCreate(TelegramProjectMemberBase):
    pass

class TelegramProjectMember(TelegramProjectMemberBase):
    id: UUID4

    class Config:
        from_attributes = True
