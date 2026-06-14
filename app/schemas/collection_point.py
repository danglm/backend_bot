from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class CollectionPointBase(BaseModel):
    id: UUID
    collection_name: Optional[str] = None
    address: Optional[str] = None
    code_prefix: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    notes: Optional[str] = None

class CollectionPointResponse(CollectionPointBase):
    class Config:
        from_attributes = True
