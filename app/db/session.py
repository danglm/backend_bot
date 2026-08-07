from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DB_Config.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    # Handler của bot là code đồng bộ chạy trong event loop: khi pool cạn thì
    # SessionLocal() block cả event loop, tức là treo toàn bộ bot. Nới pool ra và
    # hạ pool_timeout để trường hợp xấu nhất là báo lỗi nhanh thay vì đứng hình.
    pool_size=20,
    max_overflow=40,
    pool_timeout=10,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
