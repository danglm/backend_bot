from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import datetime
import uuid


class TelegramChatMessage(Base):
    """Bảng lưu trữ thông tin chi tiết từng tin nhắn Telegram."""
    __tablename__ = "telegram_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(BigInteger, index=True, nullable=False)   # ID tin nhắn Telegram (message.id)
    chat_id = Column(String, index=True, nullable=False)          # ID nhóm Telegram (VD: "-1003478083865")
    group_name = Column(String, nullable=True)                    # Tên nhóm Telegram tại thời điểm gửi
    project_id = Column(UUID(as_uuid=True), nullable=True)        # FK tới Projects.id (nếu thuộc dự án)

    user_id = Column(String, index=True, nullable=True)           # Telegram User ID người gửi
    username = Column(String, nullable=True)                      # Telegram Username (@Tragiang110)
    full_name = Column(String, nullable=True)                     # Họ tên hiển thị (Li Ly)
    is_bot = Column(Boolean, default=False)                       # True nếu do Bot/Userbot gửi

    message_type = Column(String, nullable=False, default="text") # text, photo, document, voice, video, sticker, service...
    text_content = Column(Text, nullable=True)                    # Nội dung tin nhắn hoặc Caption ảnh/file

    reply_to_message_id = Column(BigInteger, nullable=True)       # ID tin nhắn được trả lời (Reply)
    reply_to_user_id = Column(String, nullable=True)              # ID người dùng được Reply
    thread_id = Column(Integer, nullable=True)                    # Topic/Thread ID (dành cho nhóm Forum)

    has_media = Column(Boolean, default=False)                    # True nếu có đính kèm file/ảnh/voice
    is_edited = Column(Boolean, default=False)                     # True nếu tin nhắn đã bị chỉnh sửa trên Telegram
    edited_at = Column(DateTime, nullable=True)                   # Thời điểm sửa gần nhất
    is_deleted = Column(Boolean, default=False)                    # True nếu tin nhắn bị xóa trên Telegram
    deleted_at = Column(DateTime, nullable=True)                  # Thời điểm bị xóa

    date = Column(DateTime, index=True, nullable=False, default=datetime.datetime.now)  # Thời gian gửi tin nhắn gốc
    created_at = Column(DateTime, default=datetime.datetime.now)  # Thời gian tạo bản ghi CSDL


class TelegramChatMessageEdit(Base):
    """Bảng lưu lịch sử các lần chỉnh sửa nội dung tin nhắn."""
    __tablename__ = "telegram_chat_message_edits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_db_id = Column(UUID(as_uuid=True), ForeignKey("telegram_chat_messages.id", ondelete="CASCADE"), nullable=False)
    old_text_content = Column(Text, nullable=False)               # Nội dung cũ trước khi chỉnh sửa
    edited_at = Column(DateTime, default=datetime.datetime.now)   # Thời điểm thực hiện chỉnh sửa


class TelegramChatAttachment(Base):
    """Bảng lưu chi tiết các file/ảnh/media đính kèm và đường dẫn lưu trữ đĩa trên Server."""
    __tablename__ = "telegram_chat_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_db_id = Column(UUID(as_uuid=True), ForeignKey("telegram_chat_messages.id", ondelete="CASCADE"), nullable=False)

    file_type = Column(String, nullable=False)                    # photo, document, voice, video, audio, sticker
    file_id = Column(String, nullable=False)                      # File ID của Telegram API
    file_unique_id = Column(String, nullable=True)                # Unique File ID của Telegram
    file_name = Column(String, nullable=True)                     # Tên file gốc (VD: BaoCao.xlsx, image.jpg)
    file_size = Column(BigInteger, nullable=True)                 # Dung lượng file (Bytes)
    mime_type = Column(String, nullable=True)                     # MIME Type (image/jpeg, application/pdf...)

    local_path = Column(String, nullable=True)                    # Đường dẫn lưu trữ vật lý trên Server (VD: uploads/chat_media/2026/07/abc.png)
    created_at = Column(DateTime, default=datetime.datetime.now)  # Thời gian lưu file
