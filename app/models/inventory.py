from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid

class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_name = Column(String)                      # Tên nguyên liệu
    quantity = Column(Float, default=0.0)               # Số lượng tồn kho
    storage_name = Column(String)                       # Tên kho
    storage_location = Column(String)                   # Địa chỉ lưu trữ
    capacity = Column(Float, default=0.0)               # Sức chứa của kho

class MaterialPurchase(Base):
    __tablename__ = "material_purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_date = Column(Date)                     # Ngày giao dịch
    customer_id = Column(String)                        # Mã khách hàng
    material_type = Column(String)                      # Loại nguyên liệu
    storage_name = Column(String)                       # Tên kho nhập
    trip_count = Column(Integer, default=1)             # Số chuyến
    weight = Column(Float, default=0.0)                 # Khối lượng
    unit_price = Column(Float, default=0.0)             # Đơn giá
    total_amount = Column(Float, default=0.0)           # Thành tiền
    advance_payment = Column(Float, default=0.0)        # Tạm ứng
    debt = Column(Float, default=0.0)                   # Công nợ
    notes = Column(String)                              # Ghi chú

class InventoryExport(Base):
    __tablename__ = "inventory_exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    export_date = Column(Date)                          # Ngày
    performer_name = Column(String)                     # Người thực hiện
    material_type = Column(String)                      # Nguyên liệu
    storage_name = Column(String)                       # Tên kho xuất
    export_weight = Column(Float, default=0.0)          # Khối lượng
    remaining_weight = Column(Float, default=0.0)       # Khối lượng tồn kho còn lại
    notes = Column(String)                              # Ghi chú
