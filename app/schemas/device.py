from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID


# ===================== SMARTPHONE =====================

class SmartphoneBase(BaseModel):
    model_name: str
    brand: Optional[str] = None
    imei_1: str
    imei_2: Optional[str] = None
    serial_number: Optional[str] = None
    os_version: Optional[str] = None
    storage_capacity: Optional[str] = None
    battery_health: Optional[int] = None
    purchase_date: Optional[date] = None
    status: Optional[str] = "available"
    notes: Optional[str] = None
    accessories: Optional[str] = None


class SmartphoneCreate(SmartphoneBase):
    pass


class SmartphoneUpdate(SmartphoneBase):
    model_name: Optional[str] = None
    imei_1: Optional[str] = None


class Smartphone(SmartphoneBase):
    id: str
    class Config:
        orm_mode = True


# ===================== LAPTOP =====================

class LaptopBase(BaseModel):
    model_name: str
    processor_cpu: Optional[str] = None
    ram_size: Optional[str] = None
    storage_specs: Optional[str] = None
    gpu_card: Optional[str] = None
    service_tag: Optional[str] = None
    mac_address: Optional[str] = None
    warranty_expiry: Optional[date] = None
    status: Optional[str] = "available"


class LaptopCreate(LaptopBase):
    pass


class LaptopUpdate(LaptopBase):
    model_name: Optional[str] = None


class Laptop(LaptopBase):
    id: str
    class Config:
        orm_mode = True


# ===================== SIM CARD =====================

class SimCardBase(BaseModel):
    phone_number: str
    carrier: Optional[str] = None
    iccid: Optional[str] = None
    puk_code: Optional[str] = None
    plan_name: Optional[str] = None
    status: Optional[str] = "active"
    sim_type: Optional[str] = None
    smartphone_id: Optional[str] = None


class SimCardCreate(SimCardBase):
    pass


class SimCardUpdate(SimCardBase):
    phone_number: Optional[str] = None


class SimCard(SimCardBase):
    id: str
    class Config:
        orm_mode = True


# ===================== APPLICATION =====================

class ApplicationBase(BaseModel):
    id: str
    app_name: str
    package_name: Optional[str] = None
    service_category: Optional[str] = None
    account_email: Optional[str] = None
    password: Optional[str] = None
    subscription_plan: Optional[str] = None
    monthly_fee: Optional[int] = None
    billing_cycle: Optional[str] = None
    concurrent_limit: Optional[int] = None
    is_premium: Optional[int] = 0
    renewal_date: Optional[date] = None
    status: Optional[str] = "active"


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(ApplicationBase):
    app_name: Optional[str] = None


class Application(ApplicationBase):
    id: str
    class Config:
        orm_mode = True


# ===================== DEVICE ASSIGNMENT =====================

class DeviceAssignmentBase(BaseModel):
    username: str
    device_type: str
    device_id: str
    assigned_at: Optional[date] = None
    returned_at: Optional[date] = None
    initial_condition: Optional[str] = None
    final_condition: Optional[str] = None


class DeviceAssignmentCreate(DeviceAssignmentBase):
    pass


class DeviceAssignmentUpdate(DeviceAssignmentBase):
    username: Optional[str] = None
    device_type: Optional[str] = None
    device_id: Optional[str] = None


class DeviceAssignment(DeviceAssignmentBase):
    id: UUID
    class Config:
        orm_mode = True


# ===================== INSTALLED APP =====================

class InstalledAppBase(BaseModel):
    device_id: str
    app_id: str
    install_at: Optional[date] = None


class InstalledAppCreate(InstalledAppBase):
    pass


class InstalledApp(InstalledAppBase):
    class Config:
        orm_mode = True
