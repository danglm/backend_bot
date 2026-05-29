from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid
import datetime

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)      # ID dự án liên kết (Không khóa ngoại cứng)
    
    # Thông tin giấy tờ / hồ sơ gốc
    title = Column(String, nullable=False)                         # Tên giấy tờ (VD: "Đăng ký xe 59U1-12345")
    document_code = Column(String, nullable=True)                  # Số hiệu giấy tờ (VD: "CCCD: 079...")
    category = Column(String, nullable=True)                       # Phân loại (Giấy tờ xe, CCCD, Hợp đồng, Giấy phép, v.v.)
    owner_name = Column(String, nullable=True)                     # Người sở hữu / Đứng tên
    description = Column(Text, nullable=True)                      # Ghi chú, mô tả chi tiết
    issue_date = Column(Date, nullable=True)                       # Ngày cấp
    expiry_date = Column(Date, nullable=True)                      # Ngày hết hạn
    
    status = Column(String, default="ACTIVE")                      # Trạng thái: ACTIVE, ARCHIVED
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class DocumentReminder(Base):
    __tablename__ = "document_reminder"

    id = Column(UUID(as_uuid=True), primary_key=True)
    document_id = Column(String, nullable=True)        # ID liên kết giấy tờ (Không khóa ngoại cứng)
    
    # Cấu hình thông báo & lịch hẹn
    telegram_group_id = Column(String, nullable=True)              # Chat ID nhóm Telegram nhận thông báo
    reminder_days_before = Column(Integer, nullable=True)          # Nhắc nhở trước X ngày khi giấy tờ hết hạn (Nếu tính theo expiry_date)
    
    reminder_date = Column(Date, nullable=True)                    # Ngày hẹn thông báo cụ thể
    reminder_time = Column(String, default="09:00")                # Giờ gửi thông báo (định dạng "HH:MM")
    recurring_interval = Column(String, default="ONCE")            # Chu kỳ: ONCE (Một lần), DAILY (Hàng ngày), WEEKLY (Hàng tuần), MONTHLY (Hàng tháng), YEARLY (Hàng năm)
    reminder_content = Column(Text, nullable=True)                 # Nội dung thông báo tùy chỉnh gửi qua Telegram
    
    is_notified = Column(Boolean, default=False)                   # Đánh dấu đã thông báo chưa (cho ONCE)
    last_notified_at = Column(DateTime, nullable=True)             # Lần gửi thông báo gần nhất (tránh gửi lặp trong ngày)
    
    status = Column(String, default="ACTIVE")                      # ACTIVE, INACTIVE
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
