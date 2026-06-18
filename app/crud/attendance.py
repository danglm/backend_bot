from sqlalchemy.orm import Session
from app.models.finance import Attendance
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate
from datetime import datetime

def get_attendance(db: Session, employee_id: str, year: int, month: int, day: int):
    return db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.year == year,
        Attendance.month == month,
        Attendance.day == day
    ).first()

def get_attendance_by_month(db: Session, employee_id: str, year: int, month: int):
    return db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.year == year,
        Attendance.month == month
    ).order_by(Attendance.day.asc()).all()

def create_attendance(db: Session, obj_in: AttendanceCreate):
    db_obj = Attendance(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_attendance(db: Session, db_obj: Attendance, obj_in: AttendanceUpdate):
    update_data = obj_in.model_dump(exclude_unset=True)
    update_data.pop("id", None)  # Do not update the primary key id
    
    for key, value in update_data.items():
        setattr(db_obj, key, value)
        
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
