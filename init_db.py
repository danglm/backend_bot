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

import os
from alembic.config import Config
from alembic import command

def init_db():
    try:
        logger.info("Bắt đầu tự động cập nhật database với Alembic...")
        # Lấy đường dẫn tới alembic.ini ở thư mục root
        root_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_cfg = Config(os.path.join(root_dir, "alembic.ini"))
        
        # Chỉ định đúng đường dẫn thư mục alembic
        alembic_cfg.set_main_option("script_location", os.path.join(root_dir, "alembic"))
        
        # Chạy lệnh upgrade head
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Hoàn tất cập nhật database thành công!")
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi khi cập nhật DB: {e}")

if __name__ == "__main__":
    init_db()
