from pydantic import BaseModel
from typing import Optional
from datetime import date, time
from uuid import UUID

class SalaryBase(BaseModel):
    employee_id: str
    monthly_salary: Optional[float] = 0.0
    weekly_salary: Optional[float] = 0.0
    daily_salary: Optional[float] = 0.0
    hourly_salary: Optional[float] = 0.0
    overtime_salary: Optional[float] = 0.0
    rate_bhxh: Optional[float] = 0.0
    leave_balance: Optional[int] = 0
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class SalaryCreate(SalaryBase):
    pass

class SalaryUpdate(BaseModel):
    monthly_salary: Optional[float] = None
    weekly_salary: Optional[float] = None
    daily_salary: Optional[float] = None
    hourly_salary: Optional[float] = None
    overtime_salary: Optional[float] = None
    rate_bhxh: Optional[float] = None
    leave_balance: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class Salary(SalaryBase):
    id: UUID

    class Config:
        from_attributes = True


class GetSalaryResponse(BaseModel):
    employee_id: str
    employee_name: str
    standard_workdays: int
    actual_workdays: float
    base_salary: float
    overtime_salary: float
    other_allowance: float
    lunch_allowance: float
    productivity_bonus: float
    bonus: float
    bhxh: float
    penalty: float
    received_salary: float
    total_received: float
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    # Month the period is filed under — the month it starts in
    period_year: Optional[int] = None
    period_month: Optional[int] = None
    is_range: bool = False

    class Config:
        from_attributes = True

