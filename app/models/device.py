from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid
import enum


# ===================== ENUMS =====================

class SmartphoneStatus(str, enum.Enum):
    AVAILABLE = "available"        # Sẵn sàng sử dụng
    ASSIGNED = "assigned"          # Đã giao cho nhân viên
    MAINTENANCE = "maintenance"    # Đang bảo trì/sửa chữa
    BROKEN = "broken"              # Hỏng, không sử dụng được


class LaptopStatus(str, enum.Enum):
    AVAILABLE = "available"        # Sẵn sàng sử dụng
    ASSIGNED = "assigned"          # Đã giao cho nhân viên
    MAINTENANCE = "maintenance"    # Đang bảo trì/sửa chữa


class SimCardStatus(str, enum.Enum):
    ACTIVE = "active"              # Đang hoạt động
    BLOCKED = "blocked"            # Đã bị khóa
    EXPIRED = "expired"            # Hết hạn


class AppCategory(str, enum.Enum):
    STREAMING = "streaming"
    SOCIAL = "social"
    EDUCATION = "education"
    DESIGN = "design"
    OTHER = "other"


class AppBillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class AppStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


# ===================== MODELS =====================

class Smartphone(Base):
    __tablename__ = "smartphones"

    id = Column(String, primary_key=True)
    model_name = Column(String)          # Tên model (iPhone 15 Pro, Galaxy S24...)
    brand = Column(String)               # Thương hiệu (Apple, Samsung...)
    imei_1 = Column(String, unique=True) # Mã IMEI 1 (Định danh vật lý)
    imei_2 = Column(String)              # Mã IMEI 2
    serial_number = Column(String)       # Số Serial của nhà sản xuất
    os_version = Column(String)          # Phiên bản hệ điều hành (iOS 17.4, Android 14)
    storage_capacity = Column(String)    # Dung lượng bộ nhớ (128GB, 256GB...)
    battery_health = Column(Integer)     # Tình trạng pin hiện tại (%)
    purchase_date = Column(Date)         # Ngày mua thiết bị
    status = Column(String, default=SmartphoneStatus.AVAILABLE.value)  # Trạng thái
    notes = Column(Text)                 # Ghi chú thêm (máy trầy xước, mất hộp...)
    accessories = Column(String)         # Phụ kiện kèm theo (sạc, tai nghe, ốp lưng...)


class Laptop(Base):
    __tablename__ = "laptops"

    id = Column(String, primary_key=True)
    model_name = Column(String)          # Tên laptop (MacBook Pro M3, Dell XPS 13)
    processor_cpu = Column(String)       # Thông số CPU (M3 Max, i7-13700H)
    ram_size = Column(String)            # Dung lượng RAM (16GB, 32GB)
    storage_specs = Column(String)       # Loại và dung lượng ổ cứng (SSD 512GB)
    gpu_card = Column(String)            # Card đồ họa (RTX 4060, Integrated)
    service_tag = Column(String)         # Mã Service Tag (đặc thù dòng Dell/HP)
    mac_address = Column(String)         # Địa chỉ MAC (để quản lý mạng nội bộ)
    warranty_expiry = Column(Date)       # Ngày hết hạn bảo hành
    status = Column(String, default=LaptopStatus.AVAILABLE.value)  # Trạng thái
    accessories = Column(String)         # Phụ kiện kèm theo (sạc, chuột, túi...)


class SimCard(Base):
    __tablename__ = "sim_cards"

    id = Column(String, primary_key=True)
    phone_number = Column(String)        # Số điện thoại
    carrier = Column(String)             # Nhà mạng (Viettel, Vinaphone, Mobi)
    iccid = Column(String)               # Mã số seri in trên phôi SIM (20 số)
    puk_code = Column(String)            # Mã PUK để mở khóa SIM
    plan_name = Column(String)           # Tên gói cước (V120, ST90K...)
    status = Column(String, default=SimCardStatus.ACTIVE.value)  # Trạng thái
    sim_type = Column(String)            # Loại SIM (eSIM, SIM vật lý, trả trước, trả sau...)
    smartphone_id = Column(String)       # Liên kết: SIM này đang nằm ở máy nào


class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True)
    app_name = Column(String)            # Tên ứng dụng (YouTube, Netflix...)
    package_name = Column(String)        # Tên gói app (com.google.android.youtube)
    service_category = Column(String)    # Phân loại
    account_email = Column(String)       # Email đăng ký
    password = Column(String)            # Mật khẩu
    subscription_plan = Column(String)   # Gói dịch vụ
    monthly_fee = Column(Integer)        # Phí duy trì hàng tháng (VND)
    billing_cycle = Column(String)       # Chu kỳ thanh toán
    concurrent_limit = Column(Integer)   # Giới hạn máy dùng chung
    is_premium = Column(Integer)         # Có phải tài khoản trả phí không (luôn lưu là 1/0)
    renewal_date = Column(Date)          # Ngày gia hạn
    status = Column(String, default=AppStatus.ACTIVE.value)  # Trạng thái


class DeviceAssignment(Base):
    __tablename__ = "device_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String)            # Tên username Telegram
    device_type = Column(String)         # Loại thiết bị (smartphone, laptop...)
    device_id = Column(String)           # ID thiết bị
    assigned_at = Column(DateTime)       # Thời gian nhận
    returned_at = Column(DateTime)       # Thời gian trả
    initial_condition = Column(String)   # Tình trạng lúc giao
    final_condition = Column(String)     # Tình trạng lúc trả


class InstalledApp(Base):
    __tablename__ = "installed_apps"

    device_id = Column(String, primary_key=True)   # ID thiết bị
    app_id = Column(String, primary_key=True)       # ID ứng dụng
    install_at = Column(Date)                        # Ngày cài đặt
