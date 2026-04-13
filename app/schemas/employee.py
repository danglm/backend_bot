from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

# Credential Schemas
class CredentialBase(BaseModel):
    username: str
    role: Optional[str] = "employee"
    is_active: Optional[bool] = True

class CredentialCreate(CredentialBase):
    password: str

class Credential(CredentialBase):
    id: UUID
    employee_id: str

    class Config:
        from_attributes = True

# Employee Schemas
class EmployeeBase(BaseModel):
    id: str
    username: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    number_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    identity_card: Optional[str] = None
    place_of_issue: Optional[str] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    status: Optional[str] = None
    experience: Optional[str] = None
    company_id: Optional[UUID] = None
    employee_photo: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    code_payment: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    education_level: Optional[str] = None
    major: Optional[str] = None
    certificates: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    working_hours: Optional[float] = None
    performance_evaluation: Optional[str] = None
    career_goal: Optional[str] = None
    contract_type: Optional[str] = None
    benefits: Optional[str] = None
    bonus: Optional[float] = None
    base_salary: Optional[float] = None
    insurance: Optional[str] = None
    monthly_salary: Optional[float] = None
    weekly_salary: Optional[float] = None
    daily_salary: Optional[float] = None
    hourly_salary: Optional[float] = None
    overtime_salary: Optional[float] = None
    rate_bhxh: Optional[float] = None
    leave_balance: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    username: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    number_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    identity_card: Optional[str] = None
    place_of_issue: Optional[str] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    status: Optional[str] = None
    experience: Optional[str] = None
    company_id: Optional[UUID] = None
    employee_photo: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    code_payment: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    education_level: Optional[str] = None
    major: Optional[str] = None
    certificates: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    working_hours: Optional[float] = None
    performance_evaluation: Optional[str] = None
    career_goal: Optional[str] = None
    contract_type: Optional[str] = None
    benefits: Optional[str] = None
    bonus: Optional[float] = None
    base_salary: Optional[float] = None
    insurance: Optional[str] = None
    monthly_salary: Optional[float] = None
    weekly_salary: Optional[float] = None
    daily_salary: Optional[float] = None
    hourly_salary: Optional[float] = None
    overtime_salary: Optional[float] = None
    rate_bhxh: Optional[float] = None
    leave_balance: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class EmployeeResponse(EmployeeBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
