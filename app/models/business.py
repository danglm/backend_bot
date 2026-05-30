from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid

class Projects(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name = Column(String)


class Customers(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True)
    fullname = Column(String)
    hoursehold_id = Column(String)
    collection_point_id = Column(UUID(as_uuid=True))
    number_phone = Column(String)
    address = Column(String)
    ingredient = Column(String)
    amount_of_debt = Column(Integer)
    cash_advance = Column(Integer)
    total_debt = Column(Integer)
    status = Column(String, default="ACTIVE")
    username = Column(String)    ## Tài Khoản Telegram
    telegram_group = Column(String)                     # Nhóm Telegram
    number_bank = Column(String)                        # Số tài khoản ngân hàng
    bank_name = Column(String)                          # Tên ngân hàng
    is_subsidized = Column(Integer) ## Trợ giá

class CollectionPoint(Base):
    __tablename__ = "collection_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_name = Column(String)
    address = Column(String)
    code_prefix = Column(String)                            # Tiền tố mã hàng (VD: LT, P, GA)
    manager_name = Column(String, nullable=True)            # Người quản lý
    manager_phone = Column(String, nullable=True)           # SĐT liên lạc
    notes = Column(String, nullable=True)                   # Ghi chú

class DailyPurchases(Base):
    __tablename__ = "daily_purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hoursehold_id = Column(String)
    collection_point_id = Column(UUID(as_uuid=True))
    product_code = Column(String)                       # Mã hàng (VD: LT20260505)
    week = Column(Integer)
    day = Column(Date)
    is_subsidized = Column(Integer)                     # Trợ Giá
    weight = Column(Float)                              # Khối Lượng (kg)
    tare_weight = Column(Float)                         # Trừ Bì (kg)
    actual_weight = Column(Float)                       # Khối Lượng Mủ Thực Tế (kg)
    degree = Column(Float)                              # Số độ (%)
    dry_rubber = Column(Float)                          # Mủ Khô
    unit_price = Column(Float)                          # Đơn Giá (vnđ / kg)
    subsidy_price = Column(Float)                       # Giá Hỗ Trợ (vnđ / kg)
    total_amount = Column(Float)                        # Thành Tiền Mua Mủ Ngày (vnđ)
    paid_amount = Column(Float)                         # Đã Thanh Toán
    saved_amount = Column(Float)                        # Lưu Sổ
    advance_amount = Column(Float)                      # Tạm Ứng
    is_checked = Column(Boolean, default=False)         # Đã kiểm tra

class LossControls(Base):
    __tablename__ = "loss_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_code = Column(String, index=True)               # Mã hàng (LT20260505)
    day = Column(Date)                                       # Ngày thu mua
    estimated_completion = Column(Date)                      # Dự kiến hoàn thành lô hàng
    total_wet_rubber = Column(Float)                         # Tổng mủ nước (Kg)
    total_dry_rubber = Column(Float)                         # Tổng mủ khô (Kg)
    avg_degree = Column(Float)                               # Số độ trung bình (%)
    total_amount = Column(Float)                             # Tổng thành tiền (VNĐ)
    avg_unit_price = Column(Float)                           # Đơn giá trung bình (VNĐ)
    transaction_count = Column(Integer)                      # Số giao dịch
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String, nullable=True)               # User ID tạo
    processing_type = Column(String, default="dry_production")  # wet_sale (bán mủ nước) / dry_production (sản xuất mủ khô)

class FirewoodPurchases(Base):
    __tablename__ = "firewood_purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day = Column(Date)                                  # Ngày
    hoursehold_id = Column(String)                      # ID khách hàng củi
    trip_count = Column(Integer)                        # Số lượng chuyến
    vehicle_size = Column(String)                       # Kích thước xe
    firewood_weight = Column(Float)                     # Khối lượng củi (tấn/kg)
    unit_price = Column(Float)                          # Đơn giá
    total_amount = Column(Float)                        # Thành tiền
    advance_amount = Column(Float, default=0)           # Tạm ứng

class Partners(Base):
    __tablename__ = "partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(String, unique=True, index=True)   # Mã đối tác
    partner_name = Column(String)                          # Tên đối tác
    total_debt = Column(Float, default=0.0)                # Công nợ
    username = Column(String)                              # Username Telegram
    telegram_group = Column(String)                        # Nhóm Telegram
    bank_name = Column(String)                             # Tên Ngân Hàng
    bank_account = Column(String)                          # Số TK Ngân Hàng
    status = Column(String, default="ACTIVE")              # Trạng thái

class PartnerBusinesses(Base):
    __tablename__ = "partner_businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day = Column(Date)                                  # Ngày
    partner_id = Column(String)                         # Mã đối tác
    import_amount = Column(Float, default=0.0)          # Nhập
    export_amount = Column(Float, default=0.0)          # Xuất
    order_code = Column(String)                         # Mã đơn hàng
    unit_price = Column(Float, default=0.0)             # Đơn giá
    total_amount = Column(Float, default=0.0)           # Thành tiền
    notes = Column(String)                              # Ghi chú
    product_type = Column(String)                       # Loại sản phẩm
    actual_weight = Column(Float, default=0.0)          # Khối lượng Mủ nước
    dry_rubber = Column(Float, default=0.0)             # Khối lượng mủ khô
    degree = Column(Float, default=0.0)                 # Số độ

class Investment(Base):
    __tablename__ = "investments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investment_code = Column(String, unique=True, index=True)   # Mã đầu tư
    name = Column(String)                               # Tên đầu tư
    initial_capital = Column(Float, default=0.0)        # Vốn ban đầu
    start_date = Column(Date)                           # Ngày bắt đầu
    end_date = Column(Date)                             # Ngày kết thúc
    total_income = Column(Float, default=0.0)           # Tổng số tiền thu
    total_expense = Column(Float, default=0.0)          # Tổng số tiền chi
    profit = Column(Float, default=0.0)                 # Lợi nhuận
    notes = Column(String)                              # Ghi chú
    status = Column(String, default="ACTIVE")           # Trạng thái
    parent_id = Column(UUID(as_uuid=True), nullable=True) # Trỏ đến quỹ Cha
    role = Column(String, default="MAIN")               # MAIN hoặc MEMBER

class DailyPayment(Base):
    __tablename__ = "daily_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investment_id = Column(UUID(as_uuid=True))          # ID đầu tư
    requester = Column(String)                          # Người yêu cầu
    executor = Column(String)                           # Người thực hiện
    receiver = Column(String)                           # Người nhận
    payment_type = Column(String)                       # Loại (thu/chi)
    purpose = Column(String)                            # Mục đích
    reason = Column(String)                             # Lý do
    amount = Column(Float, default=0.0)                 # Số tiền
    day = Column(Date)                                  # Ngày giao dịch
    status = Column(String, default="APPROVED")         # Trạng thái duyệt
    notes = Column(String)                              # Ghi chú

class Shareholder(Base):
    __tablename__ = "shareholders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shareholder_code = Column(String, unique=True, index=True)  # Mã cổ đông
    fullname = Column(String)                                   # Tên cổ đông
    investment_id = Column(UUID(as_uuid=True))                  # Mã đầu tư (FK to investments.id)
    investment_amount = Column(Float, default=0.0)              # Số tiền đầu tư
    start_date = Column(Date)                                   # Ngày bắt đầu
    username = Column(String)                                   # Username Telegram
    telegram_group = Column(String)                             # Nhóm Telegram
    notes = Column(String)                                      # Ghi chú
    created_at = Column(DateTime, default=lambda: __import__('datetime').datetime.now())

class AgriculturalLand(Base):
    __tablename__ = "agricultural_lands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    land_code = Column(String, unique=True, index=True)     # Mã đất
    land_name = Column(String, nullable=True)                # Tên đất
    address = Column(String)                                 # Địa chỉ
    total_area = Column(Float, default=0.0)                  # Diện tích (ha)
    harvest_area = Column(Float, default=0.0)                 # Diện tích đang thu hoạch (ha)
    empty_area = Column(Float, default=0.0)                  # Diện tích trống (ha)
    planting_area = Column(Float, default=0.0)               # Diện tích đang trồng (ha)
    harvesting_trees = Column(Integer, default=0)             # Số lượng cây đang thu hoạch
    planting_trees = Column(Integer, default=0)               # Số lượng cây đang trồng
    affiliation = Column(String, nullable=True)              # Trực thuộc (Vĩnh Hà / Tiến Nga / ...)
    status = Column(String, default="ACTIVE")                # Trạng thái

class Households(Base):
    __tablename__ = "households"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    household_code = Column(String, unique=True, index=True) # Mã hộ dân (HD001)
    purchase_code = Column(String, unique=True, index=True)  # Mã hộ thu mua (TM001)
    land_code = Column(String, nullable=True)                # Mã đất trồng trọt
    fullname = Column(String)                                # Họ và tên
    username = Column(String, nullable=True)                  # Username Telegram
    telegram_group = Column(String, nullable=True)             # Nhóm Telegram
    phone = Column(String)                                   # SĐT
    address = Column(String)                                 # Địa chỉ
    total_debt = Column(Float, default=0.0)                  # Công nợ
    tapping_price = Column(Float, default=0.0)               # Đơn giá cạo mủ
    labor_price = Column(Float, default=0.0)                 # Tiền công
    bank_account = Column(String)                            # Số TK ngân hàng
    bank_name = Column(String)                               # Tên ngân hàng
    status = Column(String, default="ACTIVE")                # Trạng thái

class DailyHarvest(Base):
    __tablename__ = "daily_harvests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day = Column(Date)                                       # Ngày thu hoạch
    household_code = Column(String, index=True)              # Mã hộ dân
    land_code = Column(String, index=True)                   # Mã đất thu hoạch
    tree_count = Column(Integer, default=0)                  # Số lượng cây (cao su) / Số trái (sầu riêng)
    harvest_weight = Column(Float, default=0.0)              # Khối lượng thu hoạch (Kg) - mủ cao su / trái sầu riêng
    unit_price = Column(Float, default=0.0)                  # Đơn giá
    total_amount = Column(Float, default=0.0)                # Thành tiền
    crop_type = Column(String, default="cao_su")             # Loại cây: cao_su / sau_rieng
    created_at = Column(DateTime, default=lambda: __import__('datetime').datetime.now())

class CropTreeLog(Base):
    __tablename__ = "crop_tree_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day = Column(Date)                                       # Ngày thực hiện
    land_code = Column(String, index=True)                   # Mã đất trồng trọt
    action_type = Column(String)                             # Loại: PLANT (trồng mới) / CUT (chặt bỏ)
    quantity = Column(Integer, default=0)                    # Số lượng cây
    executor = Column(String)                                # Người thực hiện
    notes = Column(String, nullable=True)                    # Ghi chú
    crop_type = Column(String, default="cao_su")             # Loại cây: cao_su / sau_rieng
    created_at = Column(DateTime, default=lambda: __import__('datetime').datetime.now())


class SuppliesExpense(Base):
    __tablename__ = "supplies_expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day = Column(Date)                                       # Ngày mua / sử dụng
    land_code = Column(String, index=True, nullable=True)     # Mã đất trồng trọt (liên kết AgriculturalLand)
    supplies_name = Column(String)                           # Tên vật tư (Phân bón NPK, thuốc trừ sâu,...)
    supplier = Column(String, nullable=True)                 # Nhà cung cấp / Cửa hàng mua
    quantity = Column(Float, default=0.0)                    # Số lượng
    unit = Column(String)                                    # Đơn vị tính (Bao, Chai, Cái, Kg,...)
    unit_price = Column(Float, default=0.0)                  # Đơn giá
    total_amount = Column(Float, default=0.0)                # Thành tiền (Số lượng * Đơn giá)
    purpose = Column(String, nullable=True)                  # Mục đích sử dụng
    crop_type = Column(String, default="chung")              # Loại cây trồng: cao_su / sau_rieng / chung
    buyer = Column(String, nullable=True)                    # Người mua / Người thực hiện
    notes = Column(String, nullable=True)                    # Ghi chú thêm
    created_at = Column(DateTime, default=func.now())
