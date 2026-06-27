from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class InventoryResponse(BaseModel):
    id: UUID
    material_name: str
    quantity: float
    storage_name: str
    storage_location: str
    capacity: float

    class Config:
        from_attributes = True

class InventoryCreate(BaseModel):
    material_name: str
    quantity: Optional[float] = 0.0
    storage_name: Optional[str] = None
    storage_location: Optional[str] = None
    capacity: Optional[float] = 0.0


class InventoryUpdate(BaseModel):
    id: UUID
    material_name: Optional[str] = None
    quantity: Optional[float] = None
    storage_name: Optional[str] = None
    storage_location: Optional[str] = None
    capacity: Optional[float] = None

