from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CashAdvanceLogResponse(BaseModel):
    id: UUID
    hoursehold_id: Optional[str] = None
    collection_point_id: Optional[UUID] = None
    collection_name: Optional[str] = None      # Join từ collection_points
    fullname: Optional[str] = None             # Join từ customers
    entry_type: Optional[str] = None           # ADVANCE / DEDUCT
    advance_type: Optional[str] = None         # SEASON_END / IN_MONTH
    amount: Optional[int] = None
    balance_before: Optional[int] = None
    balance_after: Optional[int] = None
    is_over_limit: Optional[bool] = None
    debt_applied: Optional[bool] = None         # Thao tác có trừ/cộng vào công nợ không
    debt_before: Optional[int] = None           # Công nợ trước thao tác
    debt_after: Optional[int] = None            # Công nợ sau thao tác
    approved_by: Optional[str] = None
    created_by: Optional[str] = None
    chat_id: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CashAdvanceHouseholdSummary(BaseModel):
    """Tổng hợp biến động tiền ứng của một hộ dân."""
    hoursehold_id: str
    fullname: Optional[str] = None
    collection_point_id: Optional[UUID] = None
    collection_name: Optional[str] = None

    # Số dư hiện tại trên bảng customers
    cash_advance: int = 0                      # Ứng cuối mùa
    cash_advance_monthly: int = 0              # Ứng trong tháng
    total_advance: int = 0                     # Tổng hai loại

    # Cộng dồn từ nhật ký, trong khoảng thời gian đã lọc
    total_advanced_season: int = 0
    total_advanced_monthly: int = 0
    total_deducted_season: int = 0
    total_deducted_monthly: int = 0
    over_limit_count: int = 0
    entry_count: int = 0
    last_entry_at: Optional[datetime] = None


class CashAdvanceLogSummaryResponse(BaseModel):
    total_households: int
    total_advanced: int
    total_deducted: int
    total_outstanding: int                     # Tổng số dư đang ứng của các hộ trong kết quả
    items: List[CashAdvanceHouseholdSummary]
