from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class PartnerBusinessResponse(BaseModel):
    id: UUID
    day: date
    partner_id: str
    partner_name: Optional[str] = None
    import_amount: float
    export_amount: float
    order_code: Optional[str] = None
    unit_price: float
    total_amount: float
    notes: Optional[str] = None
    product_type: Optional[str] = None
    actual_weight: float
    dry_rubber: float
    degree: float

    class Config:
        from_attributes = True


class PartnerBusinessCreate(BaseModel):
    day: date
    partner_id: str
    import_amount: Optional[float] = 0.0
    export_amount: Optional[float] = 0.0
    order_code: Optional[str] = None
    unit_price: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    notes: Optional[str] = None
    product_type: Optional[str] = None
    actual_weight: Optional[float] = 0.0
    dry_rubber: Optional[float] = 0.0
    degree: Optional[float] = 0.0


class PartnerBusinessUpdate(BaseModel):
    id: UUID
    day: Optional[date] = None
    partner_id: Optional[str] = None
    import_amount: Optional[float] = None
    export_amount: Optional[float] = None
    order_code: Optional[str] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None
    notes: Optional[str] = None
    product_type: Optional[str] = None
    actual_weight: Optional[float] = None
    dry_rubber: Optional[float] = None
    degree: Optional[float] = None

