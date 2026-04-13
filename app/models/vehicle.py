from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid
import datetime

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_plate = Column(String, unique=True, index=True)
    vehicle_type = Column(String)
    brand = Column(String)
    model = Column(String)
    color = Column(String)
    owner_name = Column(String)
    status = Column(String)
    created_time = Column(DateTime, default=datetime.datetime.now)

class VehicleActivityLog(Base):
    __tablename__ = "vehicle_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True))
    telegram_username = Column(String)
    action = Column(String) # "RECEIVE", "RETURN"
    timestamp = Column(DateTime, default=datetime.datetime.now)
