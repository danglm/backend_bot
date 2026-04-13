from pydantic import BaseModel, UUID4
from datetime import date, datetime
from typing import Optional
from app.models.credit import CreditStatus

class CreditCustomerBase(BaseModel):
    group_name: Optional[str] = None
    customer_name: Optional[str] = None
    contact_info: Optional[str] = None
    total_credit_limit: Optional[float] = None
    remaining_credit_limit: Optional[float] = None
    total_principal_outstanding: Optional[float] = None

class CreditCustomerCreate(CreditCustomerBase):
    pass

class CreditCustomer(CreditCustomerBase):
    id: UUID4

    class Config:
        from_attributes = True

class CreditBase(BaseModel):
    customer_id: Optional[UUID4] = None
    contract_id: Optional[str] = None
    loan_type: Optional[str] = None
    initial_principal: Optional[float] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    interest_start_date: Optional[date] = None
    monthly_interest_rate: Optional[float] = None
    monthly_interest_amount: Optional[float] = None
    total_principal_paid: Optional[float] = None
    remaining_principal: Optional[float] = None
    notes: Optional[str] = None
    send_message_arise: Optional[bool] = False
    message_content: Optional[str] = None
    credit_status: Optional[CreditStatus] = CreditStatus.ACTIVE

class CreditCreate(CreditBase):
    pass

class Credit(CreditBase):
    id: UUID4

    class Config:
        from_attributes = True

class CreditInterestBase(BaseModel):
    contract_id: str
    interest_payment_date: Optional[date] = None
    payment_time: Optional[datetime] = None
    interest_amount: Optional[float] = None

class CreditInterestCreate(CreditInterestBase):
    pass

class CreditInterest(CreditInterestBase):
    id: UUID4

    class Config:
        from_attributes = True
