from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime
from app.models.rosca import RoscaPeriodType

class UserRoscaBase(BaseModel):
    id: Optional[str] = None
    full_name: Optional[str] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None
    cccd: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = "Active"
    chat_id: Optional[str] = None

class UserRoscaCreate(UserRoscaBase):
    id: str
    full_name: str

class UserRoscaUpdate(UserRoscaBase):
    id: str

class UserRoscaResponse(UserRoscaBase):
    id: str

    class Config:
        from_attributes = True


class RoscaBase(BaseModel):
    code: Optional[str] = None
    user_id: Optional[str] = None
    base_amount: Optional[float] = None
    min_bid_amount: Optional[float] = 0.0
    max_bid_amount: Optional[float] = 0.0
    total_parts: Optional[int] = 0
    commission_fee: Optional[float] = 0.0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    payment_day: Optional[int] = None
    bidding_time: Optional[time] = None
    period_type: Optional[RoscaPeriodType] = RoscaPeriodType.MONTHLY
    status: Optional[str] = "Active"
    note: Optional[str] = None

class RoscaCreate(RoscaBase):
    code: str
    user_id: str
    base_amount: float

class RoscaUpdate(RoscaBase):
    id: str

class RoscaResponse(RoscaBase):
    id: str
    owner_name: Optional[str] = None

    class Config:
        from_attributes = True


class RoscaMemberBase(BaseModel):
    rosca_id: Optional[str] = None
    user_id: Optional[str] = None
    parts_count: Optional[int] = 1
    total_contributed: Optional[float] = 0.0
    total_received: Optional[float] = 0.0
    total_profit: Optional[float] = 0.0
    profit_rate: Optional[float] = 0.0
    status: Optional[str] = "Playing"
    note: Optional[str] = None
    telegram_group: Optional[str] = None
    chat_id: Optional[str] = None

class RoscaMemberCreate(RoscaMemberBase):
    rosca_id: str
    user_id: str
    parts_count: int

class RoscaMemberUpdate(RoscaMemberBase):
    id: str

class RoscaMemberResponse(RoscaMemberBase):
    id: str
    player_name: Optional[str] = None
    rosca_code: Optional[str] = None
    paid_rounds_count: Optional[int] = 0

    class Config:
        from_attributes = True


class RoscaContributionBase(BaseModel):
    rosca_id: Optional[str] = None
    round_id: Optional[str] = None
    round_number: Optional[int] = None
    member_id: Optional[str] = None
    amount: Optional[float] = None
    actual_payment_date: Optional[datetime] = None
    status: Optional[str] = "Unpaid"
    note: Optional[str] = None

class RoscaContributionCreate(RoscaContributionBase):
    rosca_id: str
    member_id: str
    amount: float

class RoscaContributionUpdate(RoscaContributionBase):
    id: str

class RoscaContributionResponse(RoscaContributionBase):
    id: str
    player_name: Optional[str] = None
    rosca_code: Optional[str] = None

    class Config:
        from_attributes = True
