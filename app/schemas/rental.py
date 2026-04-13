from pydantic import BaseModel, UUID4
from datetime import date, datetime
from typing import Optional


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


class RealEstate(RealEstateBase):
    id: UUID4

    class Config:
        from_attributes = True


class RentalCustomerBase(BaseModel):
    group_name: Optional[str] = None
    customer_name: Optional[str] = None
    contact_info: Optional[str] = None
    number_phone: Optional[str] = None


class RentalCustomerCreate(RentalCustomerBase):
    pass


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


class RentalCreate(RentalBase):
    pass


class Rental(RentalBase):
    id: UUID4

    class Config:
        from_attributes = True


class RentalPaymentBase(BaseModel):
    contract_id: str
    payment_date: Optional[date] = None
    payment_time: Optional[datetime] = None
    payment_amount: Optional[float] = None


class RentalPaymentCreate(RentalPaymentBase):
    pass


class RentalPayment(RentalPaymentBase):
    id: UUID4

    class Config:
        from_attributes = True
