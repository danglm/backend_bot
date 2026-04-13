from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class VehicleBase(BaseModel):
    license_plate: str
    vehicle_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    owner_name: Optional[str] = None
    status: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(VehicleBase):
    license_plate: Optional[str] = None

class VehicleInDBBase(VehicleBase):
    id: UUID
    created_time: datetime

    class Config:
        orm_mode = True

class Vehicle(VehicleInDBBase):
    pass

class VehicleInDB(VehicleInDBBase):
    pass

class VehicleActivityLogBase(BaseModel):
    vehicle_id: UUID
    telegram_username: str
    action: str

class VehicleActivityLogCreate(VehicleActivityLogBase):
    pass

class VehicleActivityLog(VehicleActivityLogBase):
    id: UUID
    timestamp: datetime

    class Config:
        orm_mode = True
