from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time
from uuid import UUID

class AttendanceBase(BaseModel):
    employee_id: str
    year: int
    month: int
    day: int
    date_str: str
    work_hours: Optional[float] = None
    off_hours: Optional[time] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    break_time: Optional[float] = None
    working_time: Optional[float] = None
    late_time: Optional[float] = None
    overtime: Optional[float] = None
    error: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    check_out_time: Optional[datetime] = None
    work_hours: Optional[float] = None
    off_hours: Optional[time] = None
    break_time: Optional[float] = None
    working_time: Optional[float] = None
    late_time: Optional[float] = None
    overtime: Optional[float] = None
    error: Optional[str] = None

class AttendanceInDBBase(AttendanceBase):
    id: UUID

    class Config:
        from_attributes = True

class Attendance(AttendanceInDBBase):
    pass
