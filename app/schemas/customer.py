from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class CustomerBase(BaseModel):
    id: str
    fullname: Optional[str] = None
    hoursehold_id: Optional[str] = None
    collection_point_id: Optional[UUID] = None
    number_phone: Optional[str] = None
    address: Optional[str] = None
    ingredient: Optional[str] = None
    amount_of_debt: Optional[int] = None
    cash_advance: Optional[int] = None
    cash_advance_monthly: Optional[int] = None
    total_debt: Optional[int] = None
    status: Optional[str] = "ACTIVE"
    username: Optional[str] = None
    telegram_group: Optional[str] = None
    number_bank: Optional[str] = None
    bank_name: Optional[str] = None
    is_subsidized: Optional[int] = None
    collection_name: Optional[str] = None

class CustomerResponse(CustomerBase):
    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    id: str
    fullname: Optional[str] = None
    hoursehold_id: Optional[str] = None
    collection_point_id: Optional[UUID] = None
    number_phone: Optional[str] = None
    address: Optional[str] = None
    ingredient: Optional[str] = None
    amount_of_debt: Optional[int] = None
    cash_advance: Optional[int] = None
    cash_advance_monthly: Optional[int] = None
    total_debt: Optional[int] = None
    status: Optional[str] = "ACTIVE"
    username: Optional[str] = None
    telegram_group: Optional[str] = None
    number_bank: Optional[str] = None
    bank_name: Optional[str] = None
    is_subsidized: Optional[int] = None


class CustomerUpdate(BaseModel):
    id: str
    fullname: Optional[str] = None
    hoursehold_id: Optional[str] = None
    collection_point_id: Optional[UUID] = None
    number_phone: Optional[str] = None
    address: Optional[str] = None
    ingredient: Optional[str] = None
    amount_of_debt: Optional[int] = None
    cash_advance: Optional[int] = None
    cash_advance_monthly: Optional[int] = None
    total_debt: Optional[int] = None
    status: Optional[str] = "ACTIVE"
    username: Optional[str] = None
    telegram_group: Optional[str] = None
    number_bank: Optional[str] = None
    bank_name: Optional[str] = None
    is_subsidized: Optional[int] = None


