from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from uuid import UUID

class DocumentBase(BaseModel):
    title: str
    document_code: Optional[str] = None
    category: Optional[str] = None
    owner_name: Optional[str] = None
    description: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = "ACTIVE"

class DocumentCreate(DocumentBase):
    id: Optional[str] = None

class DocumentUpdate(DocumentBase):
    pass

class DocumentBulkUpdate(BaseModel):
    id: str
    title: Optional[str] = None
    document_code: Optional[str] = None
    category: Optional[str] = None
    owner_name: Optional[str] = None
    description: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# --- DocumentReminder Schemas ---

class DocumentReminderBase(BaseModel):
    document_id: Optional[str] = None
    telegram_group_id: Optional[str] = None
    reminder_days_before: Optional[int] = None
    reminder_date: Optional[date] = None
    reminder_time: Optional[str] = "09:00"
    recurring_interval: Optional[str] = "ONCE"
    reminder_content: Optional[str] = None
    is_notified: Optional[bool] = False
    last_notified_at: Optional[datetime] = None
    status: Optional[str] = "ACTIVE"

class DocumentReminderCreate(DocumentReminderBase):
    id: Optional[UUID] = None

class DocumentReminderUpdate(DocumentReminderBase):
    pass

class DocumentReminderBulkUpdate(BaseModel):
    id: UUID
    document_id: Optional[str] = None
    telegram_group_id: Optional[str] = None
    reminder_days_before: Optional[int] = None
    reminder_date: Optional[date] = None
    reminder_time: Optional[str] = None
    recurring_interval: Optional[str] = None
    reminder_content: Optional[str] = None
    is_notified: Optional[bool] = None
    last_notified_at: Optional[datetime] = None
    status: Optional[str] = None

class DocumentReminderResponse(DocumentReminderBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
