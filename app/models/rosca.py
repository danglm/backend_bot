import enum
import uuid
from sqlalchemy import Column, Integer, String, Float, Time, Date, DateTime, Text, Enum
from app.db.base import Base

class RoscaPeriodType(str, enum.Enum):
    DAILY = "Hụi ngày"
    WEEKLY = "Hụi tuần"
    BIWEEKLY = "Hụi 2 tuần"
    MONTHLY = "Hụi Tháng"


class UserRosca(Base):
    """Bảng lưu trữ thông tin Hồ sơ người dùng tham gia Hụi"""
    __tablename__ = "user_roscas"

    id = Column(String, primary_key=True)                                   # Khóa chính
    full_name = Column(String, nullable=True)                               # Họ và tên người chơi/chủ hụi
    username = Column(String, nullable=True)                                # Username trên Telegram
    phone_number = Column(String, nullable=True)                            # Số điện thoại liên hệ
    cccd = Column(String, nullable=True)                                    # Số căn cước công dân
    role = Column(String, nullable=True)                                    # Vai trò: Owner (Chủ hụi), Player (Người chơi)
    status = Column(String, nullable=True)                                  # Trạng thái: Pending (Chờ duyệt), Active (Hoạt động), Left (Đã rời)

class Rosca(Base):
    """Bảng lưu trữ thông tin cấu hình của Dây hụi / Bát hụi"""
    __tablename__ = "roscas"

    id = Column(String, primary_key=True)                                   # Khóa chính định danh dây hụi
    code = Column(String, nullable=True)                                    # Mã số dây hụi
    user_id = Column(String, nullable=True)                                 # ID Chủ hụi (trỏ tới UserRosca)
    base_amount = Column(Float, nullable=True)                              # Số tiền gốc 1 phần/chân (VD: Hụi 10 triệu)
    min_bid_amount = Column(Float, nullable=True)                           # Mức kêu giá/bỏ hụi thấp nhất
    max_bid_amount = Column(Float, nullable=True)                           # Mức kêu giá/bỏ hụi cao nhất (trần)
    total_parts = Column(Integer, nullable=True)                            # Tổng số lượng chân hụi tham gia
    commission_fee = Column(Float, nullable=True)                           # Mức tiền chủ hụi lấy mỗi kỳ khui (Tiền thảo)
    start_date = Column(Date, nullable=True)                                # Ngày bắt đầu dây hụi
    end_date = Column(Date, nullable=True)                                  # Ngày dự kiến kết thúc dây hụi
    payment_day = Column(Integer, nullable=True)                            # Ngày đóng hụi cố định hàng tháng
    bidding_time = Column(Time, nullable=True)                              # Giờ bỏ thăm / khui hụi hàng kỳ
    period_type = Column(Enum(RoscaPeriodType), nullable=True)              # Loại hụi (Hụi Ngày, Hụi Tháng...)
    status = Column(String, nullable=True)                                  # Trạng thái: Draft (Nháp), Active (Đang chạy), Closed (Đã đóng)
    note = Column(Text, nullable=True)                                      # Ghi chú chung

class RoscaMember(Base):
    """Bảng lưu trữ danh sách Chân hụi / Người chơi tham gia vào Dây hụi"""
    __tablename__ = "rosca_members"

    id = Column(String, primary_key=True)                                   # Khóa chính
    rosca_id = Column(String, nullable=True)                                # Dây hụi đang tham gia (trỏ tới Rosca)
    user_id = Column(String, nullable=True)                                 # ID Người chơi (trỏ tới UserRosca)
    parts_count = Column(Integer, nullable=True)                            # Số lượng chân chơi (VD: 1 người chơi 2 chân)
    total_contributed = Column(Float, default=0.0)                          # Tổng tiền đã đóng từ đầu dây đến hiện tại
    total_received = Column(Float, default=0.0)                             # Tổng tiền đã nhận (nếu đã hốt hụi)
    total_profit = Column(Float, default=0.0)                               # Tổng lợi nhuận sinh ra
    profit_rate = Column(Float, default=0.0)                                # Tỷ suất lợi nhuận (%)
    status = Column(String, nullable=True)                                  # Trạng thái: Playing (Đang chơi), Defaulted (Bể hụi)
    note = Column(Text, nullable=True)                                      # Ghi chú riêng

class RoscaRound(Base):
    """Bảng lưu trữ chi tiết các Kỳ khui hụi"""
    __tablename__ = "rosca_rounds"

    id = Column(String, primary_key=True)                                   # Khóa chính
    rosca_id = Column(String, nullable=True)                                # Kỳ khui của dây hụi nào
    round_number = Column(Integer, nullable=True)                           # Kỳ thứ mấy (Kỳ 1, Kỳ 2...)
    bidding_date = Column(Date, nullable=True)                              # Ngày thực hiện khui hụi
    winner_member_id = Column(String, nullable=True)                        # Ai là người trúng/hốt hụi
    bid_amount = Column(Float, nullable=True)                               # Giá người thắng đã kêu/bỏ
    withdrawn_amount = Column(Float, nullable=True)                         # Số tiền rút hụi thực nhận sau khi trừ thảo & hụi chết
    commission_taken = Column(Float, nullable=True)                         # Số tiền thảo thực tế chủ hụi đã thu kỳ này
    living_fee = Column(Float, nullable=True)                               # Tiền Hụi sống (Người chưa hốt cần đóng)
    dead_fee = Column(Float, nullable=True)                                 # Tiền Hụi chết (Người đã hốt cần đóng)
    status = Column(String, nullable=True)                                  # Trạng thái: Pending (Đang chờ), Completed (Hoàn tất)

class RoscaContribution(Base):
    """Bảng lưu trữ Lịch sử đóng tiền / Giao dịch hụi của từng người chơi"""
    __tablename__ = "rosca_contributions"

    id = Column(String, primary_key=True)                                   # Khóa chính
    rosca_id = Column(String, nullable=True)                                # Giao dịch thuộc dây hụi nào
    round_id = Column(String, nullable=True)                                # Thuộc kỳ khui hụi nào
    member_id = Column(String, nullable=True)                               # Người đóng tiền
    amount = Column(Float, nullable=True)                                   # Số tiền cần đóng (hụi sống hoặc hụi chết)
    actual_payment_date = Column(DateTime, nullable=True)                   # Ngày giờ đóng tiền thực tế
    status = Column(String, nullable=True)                                  # Trạng thái: Unpaid (Chưa đóng), Paid (Đã đóng), Late (Trễ)
    note = Column(Text, nullable=True)                                      # Ghi chú (nếu đóng thiếu, trễ...)
