from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class PayrollResponse(BaseModel):
    id: UUID
    employee_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    salary_id: Optional[UUID] = None
    penalty_rate: Optional[float] = None
    year: int
    month: int
    leave: Optional[int] = None
    unapproved_leave: Optional[int] = None
    base_salary_amount: Optional[float] = None
    overtime_salary_amount: Optional[float] = None
    late_penalty: Optional[float] = None
    total_salary: Optional[float] = None
    note: Optional[str] = None
    lunch_allowance: Optional[float] = None
    productivity_bonus: Optional[float] = None
    other_allowance: Optional[float] = None
    bhxh: Optional[float] = None

    class Config:
        from_attributes = True


class PayrollCreate(BaseModel):
    employee_id: str
    year: int
    month: int
    unapproved_leave: Optional[int] = 0
    base_salary_amount: Optional[float] = 0.0
    overtime_salary_amount: Optional[float] = 0.0
    total_salary: Optional[float] = 0.0
    # Actual pay period when the payroll was exported from a day range instead
    # of a whole month. Recorded in Payroll.note as a readable label.
    start_date: Optional[date] = None
    end_date: Optional[date] = None

