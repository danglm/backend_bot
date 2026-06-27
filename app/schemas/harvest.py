from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import date, datetime

class AgriculturalLandBase(BaseModel):
    land_code: Optional[str] = None
    land_name: Optional[str] = None
    address: Optional[str] = None
    total_area: Optional[float] = 0.0
    harvest_area: Optional[float] = 0.0
    empty_area: Optional[float] = 0.0
    planting_area: Optional[float] = 0.0
    harvesting_trees: Optional[int] = 0
    planting_trees: Optional[int] = 0
    affiliation: Optional[str] = None
    status: Optional[str] = "ACTIVE"

class AgriculturalLandCreate(AgriculturalLandBase):
    land_code: str

class AgriculturalLandUpdate(AgriculturalLandBase):
    id: UUID4

class AgriculturalLandResponse(AgriculturalLandBase):
    id: UUID4

    class Config:
        from_attributes = True


class HouseholdBase(BaseModel):
    household_code: Optional[str] = None
    purchase_code: Optional[str] = None
    land_code: Optional[str] = None
    fullname: Optional[str] = None
    username: Optional[str] = None
    telegram_group: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    total_debt: Optional[float] = 0.0
    tapping_price: Optional[float] = 0.0
    labor_price: Optional[float] = 0.0
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    status: Optional[str] = "ACTIVE"

class HouseholdCreate(HouseholdBase):
    household_code: str
    purchase_code: Optional[str] = None
    fullname: str

class HouseholdUpdate(HouseholdBase):
    id: UUID4

class HouseholdResponse(HouseholdBase):
    id: UUID4

    class Config:
        from_attributes = True


class DailyHarvestBase(BaseModel):
    day: Optional[date] = None
    household_code: Optional[str] = None
    land_code: Optional[str] = None
    tree_count: Optional[int] = 0
    harvest_weight: Optional[float] = 0.0
    unit_price: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    crop_type: Optional[str] = "cao_su"

class DailyHarvestCreate(DailyHarvestBase):
    day: date
    household_code: str
    land_code: str

class DailyHarvestUpdate(DailyHarvestBase):
    id: UUID4

class DailyHarvestResponse(DailyHarvestBase):
    id: UUID4
    household_name: Optional[str] = None  # Tên khách hàng (Households.fullname)
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SuppliesExpenseBase(BaseModel):
    day: Optional[date] = None
    land_code: Optional[str] = None
    supplies_name: Optional[str] = None
    supplier: Optional[str] = None
    quantity: Optional[float] = 0.0
    unit: Optional[str] = None
    unit_price: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    purpose: Optional[str] = None
    crop_type: Optional[str] = "chung"
    buyer: Optional[str] = None
    notes: Optional[str] = None

class SuppliesExpenseCreate(SuppliesExpenseBase):
    day: date
    supplies_name: str
    unit: str

class SuppliesExpenseUpdate(SuppliesExpenseBase):
    id: UUID4

class SuppliesExpenseResponse(SuppliesExpenseBase):
    id: UUID4
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
