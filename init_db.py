import logging
from app.db.session import engine
from app.db.base import Base

# Import tất cả các model để SQLAlchemy metadata nhận diện được
from app.models import business
from app.models import credit
from app.models import device
from app.models import employee
from app.models import finance
from app.models import rental
from app.models import task
from app.models import telegram
from app.models import vehicle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    try:
        logger.info("Bắt đầu tạo các bảng trong database...")
        # Lệnh này sẽ tạo tất cả các bảng chưa tồn tại
        Base.metadata.create_all(bind=engine)
        logger.info("Hoàn tất tạo bảng thành công!")
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi khi tạo bảng: {e}")

if __name__ == "__main__":
    init_db()
