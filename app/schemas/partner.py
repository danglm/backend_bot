from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class PartnerResponse(BaseModel):
    id: UUID
    partner_id: str
    partner_name: str
    total_debt: float
    username: Optional[str] = None
    telegram_group: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class PartnerCreate(BaseModel):
    partner_id: str
    partner_name: str
    total_debt: Optional[float] = 0.0
    username: Optional[str] = None
    telegram_group: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    status: Optional[str] = "ACTIVE"


class PartnerUpdate(BaseModel):
    id: UUID
    partner_id: Optional[str] = None
    partner_name: Optional[str] = None
    total_debt: Optional[float] = None
    username: Optional[str] = None
    telegram_group: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    status: Optional[str] = None


