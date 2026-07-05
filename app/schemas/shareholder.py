from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime

class ShareholderBase(BaseModel):
    shareholder_code: str
    fullname: Optional[str] = None
    investment_id: Optional[UUID] = None
    investment_amount: Optional[float] = 0.0
    start_date: Optional[date] = None
    username: Optional[str] = None
    telegram_group: Optional[str] = None
    notes: Optional[str] = None

class ShareholderCreate(ShareholderBase):
    id: Optional[UUID] = None

class ShareholderUpdate(BaseModel):
    id: UUID
    shareholder_code: Optional[str] = None
    fullname: Optional[str] = None
    investment_id: Optional[UUID] = None
    investment_amount: Optional[float] = None
    start_date: Optional[date] = None
    username: Optional[str] = None
    telegram_group: Optional[str] = None
    notes: Optional[str] = None

class ShareholderResponse(ShareholderBase):
    id: UUID
    created_at: Optional[datetime] = None
    investment_name: Optional[str] = None

    class Config:
        from_attributes = True
