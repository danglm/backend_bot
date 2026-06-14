from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class MaterialPurchaseResponse(BaseModel):
    id: UUID
    transaction_date: date
    customer_id: str
    fullname: Optional[str] = None
    material_type: str
    storage_name: str
    trip_count: int
    weight: float
    unit_price: float
    total_amount: float
    advance_payment: float
    debt: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class MaterialPurchaseCreate(BaseModel):
    transaction_date: date
    customer_id: str
    material_type: str
    storage_name: str
    trip_count: Optional[int] = 1
    weight: Optional[float] = 0.0
    unit_price: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    advance_payment: Optional[float] = 0.0
    debt: Optional[float] = 0.0
    notes: Optional[str] = None
