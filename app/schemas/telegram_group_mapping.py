from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class TelegramGroupMappingBase(BaseModel):
    mapping_type: str # Factory_Group_Mapping, Harvest_Group_Mapping, Fund_Group_Mapping, Inventory_Group_Mapping
    source_name: str
    group_name: str
    chat_id: Optional[str] = None
    is_active: Optional[bool] = True

class TelegramGroupMappingCreate(TelegramGroupMappingBase):
    pass

class TelegramGroupMappingUpdate(BaseModel):
    mapping_type: Optional[str] = None
    source_name: Optional[str] = None
    group_name: Optional[str] = None
    chat_id: Optional[str] = None
    is_active: Optional[bool] = None

class TelegramGroupMappingResponse(TelegramGroupMappingBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
