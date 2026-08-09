from sqlalchemy import Column, Integer, String, Float, Time, Date, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import datetime
import uuid

class Salary(Base):
    __tablename__ = "salaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String)
    monthly_salary = Column(Float)
    weekly_salary = Column(Float)
    daily_salary = Column(Float)
    hourly_salary = Column(Float)
    overtime_salary = Column(Float)
    rate_bhxh = Column(Float)
    leave_balance = Column(Integer)
    start_time = Column(Time)
    end_time = Column(Time)

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String)
    year = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)
    date_str = Column(String)  # (Thứ)
    work_hours = Column(Float)
    off_hours = Column(Time)
    check_in_time = Column(DateTime, nullable=True) # Changed to DateTime for precision if needed, or Time
    check_out_time = Column(DateTime, nullable=True)
    start_overtime = Column(DateTime, nullable=True)
    end_overtime = Column(DateTime, nullable=True)
    break_time = Column(Float)
    working_time = Column(Float)
    late_time = Column(Float)
    overtime = Column(Float)
    error = Column(String)
    is_half_day = Column(Boolean, default=False)  ## Nửa ngày công

class Payroll(Base):
    __tablename__ = "payrolls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String)
    salary_id = Column(UUID(as_uuid=True))
    penalty_rate = Column(Float)
    year = Column(Integer)
    month = Column(Integer)
    ## Kỳ lương. Dòng cũ để NULL và vẫn tra theo (year, month) như trước.
    ## Kỳ chéo tháng (vd 05/07 - 04/08) thì year/month lấy theo end_date.
    start_date = Column(Date)
    end_date = Column(Date)
    leave = Column(Integer)
    unapproved_leave = Column(Integer)
    base_salary_amount = Column(Float)
    overtime_salary_amount = Column(Float)
    late_penalty = Column(Float)
    total_salary = Column(Float)
    note = Column(String)


