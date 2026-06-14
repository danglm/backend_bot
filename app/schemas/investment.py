from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class InvestmentResponse(BaseModel):
    id: UUID
    investment_code: str
    name: str
    initial_capital: float
    start_date: date
    end_date: Optional[date] = None
    total_income: float
    total_expense: float
    profit: float
    notes: Optional[str] = None
    status: str
    parent_id: Optional[UUID] = None
    role: str

    class Config:
        from_attributes = True


class InvestmentCreate(BaseModel):
    id: Optional[UUID] = None
    investment_code: str
    name: str
    initial_capital: Optional[float] = 0.0
    start_date: date
    end_date: Optional[date] = None
    total_income: Optional[float] = 0.0
    total_expense: Optional[float] = 0.0
    profit: Optional[float] = 0.0
    notes: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    parent_id: Optional[UUID] = None
    role: Optional[str] = "MAIN"


class InvestmentUpdate(BaseModel):
    id: UUID
    investment_code: Optional[str] = None
    name: Optional[str] = None
    initial_capital: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_income: Optional[float] = None
    total_expense: Optional[float] = None
    profit: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    parent_id: Optional[UUID] = None
    role: Optional[str] = None

