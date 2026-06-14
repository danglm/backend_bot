from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class DailyPaymentResponse(BaseModel):
    id: UUID
    investment_id: UUID
    requester: Optional[str] = None
    executor: Optional[str] = None
    receiver: Optional[str] = None
    payment_type: str
    purpose: Optional[str] = None
    reason: Optional[str] = None
    amount: float
    day: date
    status: str
    notes: Optional[str] = None
    transaction_code: Optional[str] = None

    class Config:
        from_attributes = True


class DailyPaymentCreate(BaseModel):
    investment_id: UUID
    requester: Optional[str] = None
    executor: Optional[str] = None
    receiver: Optional[str] = None
    payment_type: str
    purpose: Optional[str] = None
    reason: Optional[str] = None
    amount: float = 0.0
    day: date
    status: str = "APPROVED"
    notes: Optional[str] = None
    transaction_code: Optional[str] = "K"
