from pydantic import BaseModel, UUID4
from datetime import date, datetime
from typing import Optional
import enum


class RealEstateStatus(str, enum.Enum):
    LIVING = "living"
    RENTED = "rented"
    SELF_EXPLOITED = "self_exploited"
    VACANT = "vacant"
    INSTALLMENT = "installment"
    LEGAL_ISSUES = "legal_issues"
    SOLD = "sold"


class RealEstateBase(BaseModel):
    real_estate_id: Optional[str] = None
    address: Optional[str] = None
    start_buy: Optional[date] = None
    end_buy: Optional[date] = None
    total_cost: Optional[float] = None
    real_estate_cost: Optional[float] = None
    construction_cost: Optional[float] = None
    furniture_cost: Optional[float] = None
    sale_cost: Optional[float] = None
    contributed_cost: Optional[float] = None
    monthly_interest_rate: Optional[float] = None
    mining_profit: Optional[float] = None
    rental_profit: Optional[float] = None
    start_sale: Optional[date] = None
    end_sale: Optional[date] = None
    profit_after_tax: Optional[float] = None
    profit_after_sale: Optional[float] = None
    status: Optional[str] = None
    note: Optional[str] = None
    current_estimated: Optional[float] = None


class RealEstateCreate(RealEstateBase):
    pass

class RealEstateUpdate(RealEstateBase):
    id: UUID4

class RealEstate(RealEstateBase):
    id: UUID4

    class Config:
        from_attributes = True


class RentalCustomerBase(BaseModel):
    customer_id: Optional[str] = None
    group_name: Optional[str] = None
    customer_name: Optional[str] = None
    contact_info: Optional[str] = None
    number_phone: Optional[str] = None
    chat_id: Optional[str] = None


class RentalCustomerCreate(RentalCustomerBase):
    pass


class RentalCustomerUpdate(RentalCustomerBase):
    id: UUID4


class RentalCustomer(RentalCustomerBase):
    id: UUID4

    class Config:
        from_attributes = True


class RentalBase(BaseModel):
    customer_id: Optional[UUID4] = None
    contract_id: Optional[str] = None
    real_estate_id: Optional[str] = None
    type_contract: Optional[str] = None
    start_rental: Optional[date] = None
    end_rental: Optional[date] = None
    deposit: Optional[float] = None
    monthly_rental: Optional[float] = None
    rental_debt: Optional[float] = 0.0
    status: Optional[str] = None
    notes: Optional[str] = None


class RentalCreate(RentalBase):
    pass


class RentalUpdate(RentalBase):
    id: UUID4


class Rental(RentalBase):
    id: UUID4

    class Config:
        from_attributes = True


class RentalResponse(BaseModel):
    id: UUID4
    customer_id: Optional[UUID4] = None
    customer_code: Optional[str] = None
    customer_name: Optional[str] = None
    group_name: Optional[str] = None
    contact_info: Optional[str] = None
    number_phone: Optional[str] = None
    chat_id: Optional[str] = None
    contract_id: Optional[str] = None
    real_estate_id: Optional[str] = None
    type_contract: Optional[str] = None
    start_rental: Optional[date] = None
    end_rental: Optional[date] = None
    deposit: Optional[float] = None
    monthly_rental: Optional[float] = None
    rental_debt: Optional[float] = 0.0
    status: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class RentalPaymentBase(BaseModel):
    contract_id: str
    payment_date: Optional[date] = None
    payment_time: Optional[datetime] = None
    payment_amount: Optional[float] = None


class RentalPaymentCreate(RentalPaymentBase):
    pass


class RentalPaymentUpdate(BaseModel):
    id: UUID4
    contract_id: Optional[str] = None
    payment_date: Optional[date] = None
    payment_time: Optional[datetime] = None
    payment_amount: Optional[float] = None


class RentalPayment(RentalPaymentBase):
    id: UUID4

    class Config:
        from_attributes = True


class RentalPaymentResponse(BaseModel):
    id: UUID4
    contract_id: str
    payment_date: Optional[date] = None
    payment_time: Optional[datetime] = None
    payment_amount: Optional[float] = None
    
    # Contract details
    real_estate_id: Optional[str] = None
    type_contract: Optional[str] = None
    start_rental: Optional[date] = None
    end_rental: Optional[date] = None
    deposit: Optional[float] = None
    monthly_rental: Optional[float] = None
    rental_debt: Optional[float] = 0.0
    status: Optional[str] = None
    
    # Customer details
    customer_code: Optional[str] = None
    customer_name: Optional[str] = None
    group_name: Optional[str] = None
    contact_info: Optional[str] = None
    number_phone: Optional[str] = None
    chat_id: Optional[str] = None

    class Config:
        from_attributes = True
