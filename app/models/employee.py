from sqlalchemy import Column, Integer, String, Date, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid
import datetime

class Employee(Base):
    __tablename__ = "employee"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)  # username Telegram
    telegram_group = Column(String)                     # Nhóm Telegram
    last_name = Column(String)
    first_name = Column(String)
    gender = Column(String)
    birthday = Column(Date)
    number_phone = Column(String)
    email = Column(String, unique=True, index=True)
    address = Column(String)
    identity_card = Column(String)
    place_of_issue = Column(String)
    nationality = Column(String)
    marital_status = Column(String)
    status = Column(String)
    experience = Column(String)
    company_id = Column(UUID(as_uuid=True))
    employee_photo = Column(String)
    bank_name = Column(String)
    bank_account_number = Column(String)
    code_payment = Column(String)
    emergency_phone = Column(String)
    emergency_contact = Column(String)
    education_level = Column(String)
    major = Column(String)
    certificates = Column(String)
    position = Column(String)
    department = Column(String)
    working_hours = Column(Float)
    performance_evaluation = Column(String)
    career_goal = Column(String)
    contract_type = Column(String)
    benefits = Column(String)
    bonus = Column(Float)
    base_salary = Column(Float)
    insurance = Column(String)
    monthly_salary = Column(Float)
    weekly_salary = Column(Float)
    daily_salary = Column(Float)
    hourly_salary = Column(Float)
    overtime_salary = Column(Float)
    rate_bhxh = Column(Float)
    leave_balance = Column(Integer)
    total_debt = Column(Integer, default=0)   ## Công nợ nhân sự
    start_time = Column(DateTime) ## Thời gian checkin
    end_time = Column(DateTime) ## Thời gian checkout
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

    def __repr__(self):
        return f"<Employee(id='{self.id}', username='{self.username}', last_name='{self.last_name}', first_name='{self.first_name}')>"

class Credential(Base):
    __tablename__ = "credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String, unique=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="employee")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())