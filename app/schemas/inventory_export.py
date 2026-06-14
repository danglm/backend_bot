from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class InventoryExportResponse(BaseModel):
    id: UUID
    export_date: Optional[date] = None
    performer_name: Optional[str] = None
    material_type: Optional[str] = None
    storage_name: Optional[str] = None
    export_weight: float
    remaining_weight: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class InventoryExportCreate(BaseModel):
    export_date: Optional[date] = None
    performer_name: Optional[str] = None
    material_type: Optional[str] = None
    storage_name: Optional[str] = None
    export_weight: float = 0.0
    notes: Optional[str] = None

