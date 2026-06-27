from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class ProcessLossControlRequest(BaseModel):
    collection_point_id: Optional[str] = None  # UUID của điểm thu mua (None = tất cả)
    start_date: date
    end_date: date


class LossControlItem(BaseModel):
    product_code: str                              # Mã hàng (GA20260527)
    day: Optional[date] = None                     # Ngày thu mua
    estimated_completion: Optional[date] = None    # Dự kiến hoàn thành
    total_dry_rubber: float                        # Tổng mủ khô (Kg) từ LossControls
    total_import_quantity: float                   # Tổng nhập kho thực tế (Kg)
    loss_percentage: float                         # % Hao hụt
    total_amount: Optional[float] = None           # Tổng thành tiền
    avg_unit_price: Optional[float] = None         # Đơn giá TB
    processing_type: Optional[str] = None          # dry_production / wet_sale
    transaction_count: Optional[int] = None        # Số giao dịch thu mua


class ProcessLossControlResponse(BaseModel):
    collection_point_id: str
    collection_name: Optional[str] = None
    code_prefix: Optional[str] = None
    start_date: date
    end_date: date
    total_items: int
    items: List[LossControlItem]
