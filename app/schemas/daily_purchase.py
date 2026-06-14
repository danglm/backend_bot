from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID


class DailyPurchaseResponse(BaseModel):
    id: Optional[UUID] = None
    hoursehold_id: Optional[str] = None
    fullname: Optional[str] = None
    collection_name: Optional[str] = None
    day: Optional[date] = None
    is_subsidized: Optional[int] = 0
    weight: Optional[float] = 0.0
    tare_weight: Optional[float] = 0.0
    actual_weight: Optional[float] = 0.0
    degree: Optional[float] = 0.0
    dry_rubber: Optional[float] = 0.0
    unit_price: Optional[float] = 0.0
    subsidy_price: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    paid_amount: Optional[float] = 0.0
    saved_amount: Optional[float] = 0.0
    product_code: Optional[str] = None

    class Config:
        from_attributes = True


class DailyPurchaseCreate(BaseModel):
    hoursehold_id: str
    collection_point_id: UUID
    product_code: str
    week: int
    day: date
    is_subsidized: int
    weight: float
    tare_weight: float
    actual_weight: float
    degree: float
    dry_rubber: float
    unit_price: float
    subsidy_price: float
    total_amount: float
    paid_amount: float
    saved_amount: float


class DailyPurchaseUpdate(BaseModel):
    id: UUID
    hoursehold_id: Optional[str] = None
    collection_point_id: Optional[UUID] = None
    product_code: Optional[str] = None
    week: Optional[int] = None
    day: Optional[date] = None
    is_subsidized: Optional[int] = None
    weight: Optional[float] = None
    tare_weight: Optional[float] = None
    actual_weight: Optional[float] = None
    degree: Optional[float] = None
    dry_rubber: Optional[float] = None
    unit_price: Optional[float] = None
    subsidy_price: Optional[float] = None
    total_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    saved_amount: Optional[float] = None


