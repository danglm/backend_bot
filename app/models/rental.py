from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid
import enum


class RentalStatus(str, enum.Enum):
    ACTIVE = "active"          # Đang thuê
    EXPIRED = "expired"        # Hết hạn
    CANCELLED = "cancelled"    # Đã hủy
    BAD_DEBT = "bad_debt"      # Nợ xấu (Blacklist)


class RentalCustomer(Base):
    __tablename__ = "rental_customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_name = Column(String)           # Tên Nhóm
    customer_name = Column(String)        # Tên Khách Hàng
    contact_info = Column(String)         # Liên Hệ Khách Hàng (telegram_username)
    number_phone = Column(String)         # Số Điện Thoại

class Rental(Base):
    __tablename__ = "rentals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True))

    contract_id = Column(String)          # Mã Hợp Đồng
    real_estate_id = Column(String)       # Mã Bất Động Sản
    type_contract = Column(String)        # Loại Hợp Đồng
    start_rental = Column(Date)           # Ngày Bắt Đầu Thuê
    end_rental = Column(Date)             # Ngày Kết Thúc Thuê
    deposit = Column(Float)               # Tiền Cọc
    monthly_rental = Column(Float)        # Tiền Thuê
    rental_debt = Column(Float, default=0.0)  # Công Nợ
    status = Column(String)               # Trạng Thái  

class RentalPayment(Base):
    __tablename__ = "rental_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(String)              # Mã Hợp Đồng
    payment_date = Column(Date)               # Ngày Thanh Toán
    payment_time = Column(DateTime)           # Thời Gian Thanh Toán
    payment_amount = Column(Float)            # Số Tiền Đã Đóng


class RealEstate(Base):
    __tablename__ = "real_estates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    real_estate_id = Column(String)              # Mã Bất Động Sản
    address = Column(String)                     # Địa Chỉ
    start_buy = Column(Date)                     # Ngày Bắt Đầu Mua
    end_buy = Column(Date)                       # Ngày Kết Thúc Mua
    total_cost = Column(Float)                   # Tổng Đầu Tư
    real_estate_cost = Column(Float)             # Tiền Bất Động Sản
    construction_cost = Column(Float)            # Tiền Xây Dựng
    furniture_cost = Column(Float)               # Tiền Nội Thất
    sale_cost = Column(Float)                    # Tiền Bán Ra
    contributed_cost = Column(Float)             # Tiền Đã Góp
    monthly_interest_rate = Column(Float)        # Lãi Xuất / Tháng
    mining_profit = Column(Float)                # Lợi Nhuận Khai Thác
    rental_profit = Column(Float)                # Lợi Nhuận Cho Thuê
    start_sale = Column(Date)                    # Ngày Bắt Đầu Bán
    end_sale = Column(Date)                      # Ngày Kết Thúc Bán
    profit_after_tax = Column(Float)             # Bán Ra Sau Thuế
    profit_after_sale = Column(Float)            # Lợi Nhuận Sau Bán
    status = Column(String)                      # Tình Trạng
    note = Column(String)                        # Ghi Chú
    current_estimated = Column(Float)            # Giá Tạm Tính Hiện Tại
