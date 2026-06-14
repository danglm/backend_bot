from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class ProductTransactionResponse(BaseModel):
    id: UUID
    product_code: Optional[str] = None
    transaction_date: Optional[date] = None
    customer_id: Optional[str] = None
    transaction_type: Optional[str] = None
    material_type: Optional[str] = None
    storage_id: Optional[UUID] = None
    storage_name: Optional[str] = None
    quantity: float
    unit_price: float
    total_amount: float
    debt: float
    note: Optional[str] = None

    class Config:
        from_attributes = True


class ProductTransactionCreate(BaseModel):
    product_code: Optional[str] = None
    transaction_date: Optional[date] = None
    customer_id: Optional[str] = None
    transaction_type: str  # "Nhập" / "import" / "Xuất" / "export"
    material_type: str
    storage_id: Optional[UUID] = None
    storage_name: str
    quantity: float = 0.0
    unit_price: float = 0.0
    total_amount: float = 0.0
    debt: float = 0.0
    note: Optional[str] = None

