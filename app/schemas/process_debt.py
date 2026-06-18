from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class ProcessDebtRequest(BaseModel):
    hoursehold_id: Optional[str] = None
    employee_id: Optional[str] = None
    partner_id: Optional[str] = None
    amount: float
    type_transaction: str  # "thu" hoặc "chi"


class DailyPurchaseAllocation(BaseModel):
    day: Optional[date] = None
    allocated: float
    new_saved: float


class ProcessDebtResponse(BaseModel):
    success: bool
    message: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    type_transaction: str
    amount: float
    old_debt: Optional[float] = None
    new_debt: Optional[float] = None
    allocations: Optional[List[DailyPurchaseAllocation]] = None
    unallocated_amount: Optional[float] = None
