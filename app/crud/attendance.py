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
    db_obj = Attendance(
        employee_id=obj_in.employee_id,
        year=obj_in.year,
        month=obj_in.month,
        day=obj_in.day,
        date_str=obj_in.date_str,
        check_in_time=obj_in.check_in_time
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_attendance(db: Session, db_obj: Attendance, obj_in: AttendanceUpdate):
    if obj_in.check_out_time:
        db_obj.check_out_time = obj_in.check_out_time
    if obj_in.work_hours is not None:
        db_obj.work_hours = obj_in.work_hours
    if obj_in.off_hours is not None:
        db_obj.off_hours = obj_in.off_hours
    if obj_in.break_time is not None:
        db_obj.break_time = obj_in.break_time
    if obj_in.working_time is not None:
        db_obj.working_time = obj_in.working_time
    if obj_in.late_time is not None:
        db_obj.late_time = obj_in.late_time
    if obj_in.overtime is not None:
        db_obj.overtime = obj_in.overtime
    if obj_in.error is not None:
        db_obj.error = obj_in.error
        
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
