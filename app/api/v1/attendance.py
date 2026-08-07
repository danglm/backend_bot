from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.api import deps
from app.api.deps import require_permission
from app.models.employee import Employee, Credential
from app.crud import attendance as crud_attendance
from app.models.finance import Attendance, Payroll
from app.schemas.attendance import AttendanceResponse, AttendanceCreate, AttendanceUpdate, Attendance as schema_Attendance
from app.schemas import PayrollResponse, PayrollCreate
from bot.utils.logger import LogInfo, LogError
from app.services.notification import notify_telegram_group
import re
import calendar
import datetime
from uuid import UUID
from typing import List, Optional
from bot.utils.scheduler import _is_working_day

router = APIRouter()

@router.get("/get-attendance", response_model=AttendanceResponse)
def get_attendance(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: str = Query(..., description="ID of the employee"),
    date: str = Query(..., description="Date in mm/yyyy format"),
    current_user: Credential = Depends(require_permission("attendance"))
):
    """
    Get all attendance information for a specific employee in a given month.
    """
    LogInfo(f"[Attendance API] Request to get attendance for employee {employee_id} and date {date}")
    
    # Parse month and year from date string (mm/yyyy or m/yyyy)
    match = re.match(r"^(\d{1,2})/(\d{4})$", date.strip())
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Expected mm/yyyy or m/yyyy."
        )
        
    month = int(match.group(1))
    year = int(match.group(2))
    
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="Invalid month. Must be between 1 and 12."
        )
        
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )
        
    # Query attendance records
    attendance_records = crud_attendance.get_attendance_by_month(
        db, employee_id=employee_id, year=year, month=month
    )
    
    return {
        "employee_id": employee.id,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "attendance": attendance_records
    }


@router.post("/add-attendance", response_model=schema_Attendance, status_code=status.HTTP_201_CREATED)
def add_attendance(
    *,
    db: Session = Depends(deps.get_db),
    attendance_in: AttendanceCreate,
    current_user: Credential = Depends(require_permission("attendance"))
):
    """
    Create a new attendance record.
    """
    LogInfo(f"[Attendance API] Request to add attendance for employee {attendance_in.employee_id} on {attendance_in.day}/{attendance_in.month}/{attendance_in.year}")
    
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == attendance_in.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )
        
    # Check if attendance record already exists for this date
    existing_record = crud_attendance.get_attendance(
        db, 
        employee_id=attendance_in.employee_id, 
        year=attendance_in.year, 
        month=attendance_in.month, 
        day=attendance_in.day
    )
    if existing_record:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance record for this employee on this date already exists."
        )
        
    # Create the record
    db_obj = crud_attendance.create_attendance(db, obj_in=attendance_in)
    return db_obj


@router.post("/update-attendance", response_model=schema_Attendance)
def update_attendance(
    *,
    db: Session = Depends(deps.get_db),
    attendance_in: AttendanceUpdate,
    current_user: Credential = Depends(require_permission("attendance"))
):
    """
    Update an existing attendance record.
    """
    LogInfo(f"[Attendance API] Request to update attendance for employee {attendance_in.employee_id} on {attendance_in.day}/{attendance_in.month}/{attendance_in.year}")
    
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == attendance_in.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )
        
    # Find the existing attendance record
    db_obj = None
    if attendance_in.id:
        db_obj = db.query(Attendance).filter(Attendance.id == attendance_in.id).first()
        
    if not db_obj:
        db_obj = crud_attendance.get_attendance(
            db,
            employee_id=attendance_in.employee_id,
            year=attendance_in.year,
            month=attendance_in.month,
            day=attendance_in.day
        )
        
    if not db_obj:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found"
        )
        
    # Update the record
    updated_obj = crud_attendance.update_attendance(db, db_obj=db_obj, obj_in=attendance_in)
    return updated_obj


@router.delete("/delete-attendance", response_model=List[schema_Attendance])
def delete_attendance(
    *,
    db: Session = Depends(deps.get_db),
    attendance_ids: List[UUID] = Body(..., description="List of attendance IDs to delete"),
    current_user: Credential = Depends(require_permission("attendance"))
):
    """
    Delete attendance records by list of IDs.
    """
    LogInfo(f"[Attendance API] Request to delete attendance records: {attendance_ids}")
    try:
        # Check for duplicates in input list itself
        if len(attendance_ids) != len(set(attendance_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate attendance IDs found in the request input."
            )
            
        # Check if all attendance IDs exist in the database
        existing_records = db.query(Attendance).filter(Attendance.id.in_(attendance_ids)).all()
        existing_ids = {r.id for r in existing_records}
        
        missing_ids = [str(aid) for aid in attendance_ids if aid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance records with IDs {missing_ids} not found in the database."
            )
            
        deleted_records = []
        for record in existing_records:
            deleted_records.append(record)
            db.delete(record)
            
        db.commit()
        return deleted_records
    except HTTPException:
        raise
    except Exception as e:
        LogInfo(f"[Attendance API] Error in delete-attendance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _parse_day(date_str: str, field: str) -> datetime.date:
    """Parse a yyyy-mm-dd string into a date."""
    try:
        return datetime.date.fromisoformat(date_str.strip())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field} format. Expected yyyy-mm-dd."
        )


def _months_between(start: datetime.date, end: datetime.date) -> List[tuple]:
    """List the (year, month) pairs touched by the [start, end] range."""
    months = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append((year, month))
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return months


@router.get("/get-payrolls", response_model=List[PayrollResponse])
def get_payrolls(
    *,
    db: Session = Depends(deps.get_db),
    date: Optional[str] = Query(None, description="Date in mm/yyyy format. If not provided, fetch all dates."),
    start_date: Optional[str] = Query(None, description="Range start in yyyy-mm-dd format. Must be paired with end_date. Takes precedence over date."),
    end_date: Optional[str] = Query(None, description="Range end in yyyy-mm-dd format. Must be paired with start_date. Takes precedence over date."),
    employee_id: Optional[str] = Query(None, description="ID of the employee. If not provided, fetch all."),
    current_user: Credential = Depends(require_permission("attendance"))
):
    """
    Get payroll records for a specific employee or all employees, filtered by a
    month (`date`) or by every month touched by a day range
    (`start_date` + `end_date`).
    """
    LogInfo(
        f"[Attendance API] Request to get payrolls for employee_id={employee_id}, "
        f"date={date}, start_date={start_date}, end_date={end_date}"
    )

    # Base query joining Payroll and Employee to get the names, allowances/bonuses, and BHXH
    query = db.query(
        Payroll,
        Employee.first_name,
        Employee.last_name,
        Employee.lunch_allowance,
        Employee.productivity_bonus,
        Employee.other_allowance,
        Employee.rate_bhxh
    ).join(
        Employee, 
        Payroll.employee_id == Employee.id
    )

    has_range = bool(start_date and start_date.strip()) or bool(end_date and end_date.strip())

    if has_range:
        if not (start_date and start_date.strip()) or not (end_date and end_date.strip()):
            raise HTTPException(
                status_code=400,
                detail="Both start_date and end_date are required when filtering by range."
            )
        range_start = _parse_day(start_date, "start_date")
        range_end = _parse_day(end_date, "end_date")
        if range_start > range_end:
            raise HTTPException(
                status_code=400,
                detail="start_date must not be after end_date."
            )
        query = query.filter(
            or_(*[
                and_(Payroll.year == y, Payroll.month == m)
                for y, m in _months_between(range_start, range_end)
            ])
        )
    elif date and date.strip():
        # Parse month and year from date string (mm/yyyy or m/yyyy)
        match = re.match(r"^(\d{1,2})/(\d{4})$", date.strip())
        if not match:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Expected mm/yyyy or m/yyyy."
            )

        month = int(match.group(1))
        year = int(match.group(2))

        if month < 1 or month > 12:
            raise HTTPException(
                status_code=400,
                detail="Invalid month. Must be between 1 and 12."
            )
        query = query.filter(Payroll.year == year, Payroll.month == month)

    if employee_id and employee_id.strip():
        # Check if employee exists
        employee_exists = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee_exists:
            raise HTTPException(
                status_code=404,
                detail="Employee not found"
            )
        query = query.filter(Payroll.employee_id == employee_id)

    results = query.all()

    response_list = []
    for payroll, first_name, last_name, lunch_allowance, productivity_bonus, other_allowance, rate_bhxh in results:
        response_list.append(
            PayrollResponse(
                id=payroll.id,
                employee_id=payroll.employee_id,
                first_name=first_name,
                last_name=last_name,
                salary_id=payroll.salary_id,
                penalty_rate=payroll.penalty_rate,
                year=payroll.year,
                month=payroll.month,
                leave=payroll.leave,
                unapproved_leave=payroll.unapproved_leave,
                base_salary_amount=payroll.base_salary_amount,
                overtime_salary_amount=payroll.overtime_salary_amount,
                late_penalty=payroll.late_penalty,
                total_salary=payroll.total_salary,
                note=payroll.note,
                lunch_allowance=lunch_allowance,
                productivity_bonus=productivity_bonus,
                other_allowance=other_allowance,
                bhxh=rate_bhxh
            )
        )
    return response_list


@router.post("/add-payrolls", response_model=List[PayrollResponse], status_code=status.HTTP_201_CREATED)
async def add_payrolls(
    *,
    db: Session = Depends(deps.get_db),
    payrolls_in: List[PayrollCreate],
    current_user: Credential = Depends(require_permission("attendance"))
):
    """
    Create bulk new payroll records.
    """
    LogInfo(f"[Attendance API] Request to add bulk payrolls. Total records: {len(payrolls_in)}")
    
    added_payrolls = []
    for payroll_in in payrolls_in:
        # 1. Check if employee exists
        employee = db.query(Employee).filter(Employee.id == payroll_in.employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee {payroll_in.employee_id} not found"
            )
            
        # 2. Check if payroll record already exists for this employee, month, and year
        existing_payroll = db.query(Payroll).filter(
            Payroll.employee_id == payroll_in.employee_id,
            Payroll.month == payroll_in.month,
            Payroll.year == payroll_in.year
        ).first()
        if existing_payroll:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Payroll record for employee {payroll_in.employee_id} in {payroll_in.month}/{payroll_in.year} already exists."
            )

        # 3. Query Attendance to calculate leave count, narrowed to the pay
        #    period when the payroll was exported from a day range
        leave_query = db.query(Attendance).filter(
            Attendance.employee_id == payroll_in.employee_id,
            Attendance.year == payroll_in.year,
            Attendance.month == payroll_in.month,
            Attendance.check_in_time.is_(None),
            Attendance.check_out_time.is_(None)
        )

        period_note = None
        if payroll_in.start_date and payroll_in.end_date:
            if payroll_in.start_date > payroll_in.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"start_date must not be after end_date for employee {payroll_in.employee_id}."
                )

            last_day_of_month = calendar.monthrange(payroll_in.year, payroll_in.month)[1]
            month_start = datetime.date(payroll_in.year, payroll_in.month, 1)
            month_end = datetime.date(payroll_in.year, payroll_in.month, last_day_of_month)
            # Clamp the period to the month this record belongs to
            first_day = max(payroll_in.start_date, month_start).day
            last_day = min(payroll_in.end_date, month_end).day

            leave_query = leave_query.filter(
                Attendance.day >= first_day,
                Attendance.day <= last_day
            )
            period_note = (
                f"Kỳ lương: {payroll_in.start_date.strftime('%d/%m/%Y')}"
                f" - {payroll_in.end_date.strftime('%d/%m/%Y')}"
            )

        leave_count = leave_query.count()

        # 4. Create the record
        db_payroll = Payroll(
            employee_id=payroll_in.employee_id,
            salary_id=None,
            penalty_rate=0.0,
            year=payroll_in.year,
            month=payroll_in.month,
            leave=leave_count,
            unapproved_leave=payroll_in.unapproved_leave,
            base_salary_amount=payroll_in.base_salary_amount,
            overtime_salary_amount=payroll_in.overtime_salary_amount,
            late_penalty=0.0,
            total_salary=payroll_in.total_salary,
            note=period_note
        )
        db.add(db_payroll)

        # 5. Update employee total_debt
        if employee.total_debt is None:
            employee.total_debt = 0
        employee.total_debt += int(round(payroll_in.total_salary or 0.0))

        added_payrolls.append((db_payroll, employee))
        
    db.commit()
    
    # 5. Return the new payroll records mapped to PayrollResponse
    response_list = []
    for db_payroll, employee in added_payrolls:
        db.refresh(db_payroll)
        response_list.append(
            PayrollResponse(
                id=db_payroll.id,
                employee_id=db_payroll.employee_id,
                first_name=employee.first_name,
                last_name=employee.last_name,
                salary_id=db_payroll.salary_id,
                penalty_rate=db_payroll.penalty_rate,
                year=db_payroll.year,
                month=db_payroll.month,
                leave=db_payroll.leave,
                unapproved_leave=db_payroll.unapproved_leave,
                base_salary_amount=db_payroll.base_salary_amount,
                overtime_salary_amount=db_payroll.overtime_salary_amount,
                late_penalty=db_payroll.late_penalty,
                total_salary=db_payroll.total_salary,
                note=db_payroll.note,
                lunch_allowance=employee.lunch_allowance,
                productivity_bonus=employee.productivity_bonus,
                other_allowance=employee.other_allowance,
                bhxh=employee.rate_bhxh
            )
        )

    # Send Telegram notification
    try:
        performer = current_user.employee_id or current_user.username or "unknown"
        details = "Đã xuất bảng lương mới:\n" + "\n".join(
            [f"- Nhân viên: {r.employee_id} ({r.first_name} {r.last_name}) - Tháng: {r.month}/{r.year} - Thực lĩnh: {r.total_salary:,.0f} VNĐ" for r in response_list]
        )
        await notify_telegram_group(
            db=db,
            action="UPDATE",
            module_key="salaries",
            details=details,
            performer=performer
        )
    except Exception as err:
        LogError(f"[Attendance API] Failed to send Telegram notification: {err}")

    return response_list


@router.delete("/delete-payrolls", response_model=List[PayrollResponse])
async def delete_payrolls(
    *,
    db: Session = Depends(deps.get_db),
    payroll_ids: List[UUID] = Body(..., description="List of payroll IDs to delete"),
    current_user: Credential = Depends(require_permission("attendance"))
):
    """
    Delete payroll records by list of IDs and revert employee debt values.
    """
    LogInfo(f"[Attendance API] Request to delete payroll records: {payroll_ids}")
    try:
        # Check for duplicates in input list itself
        if len(payroll_ids) != len(set(payroll_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate payroll IDs found in the request input."
            )
            
        # Check if all payroll IDs exist in the database
        existing_records = db.query(Payroll).filter(Payroll.id.in_(payroll_ids)).all()
        existing_ids = {r.id for r in existing_records}
        
        missing_ids = [str(pid) for pid in payroll_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payroll records with IDs {missing_ids} not found in the database."
            )
            
        deleted_records = []
        for record in existing_records:
            # Revert employee debt (total_debt)
            employee = db.query(Employee).filter(Employee.id == record.employee_id).first()
            if employee and employee.total_debt is not None:
                employee.total_debt -= int(round(record.total_salary or 0.0))

            # Map to response format before deletion
            first_name = employee.first_name if employee else None
            last_name = employee.last_name if employee else None
            lunch_allowance = employee.lunch_allowance if employee else None
            productivity_bonus = employee.productivity_bonus if employee else None
            other_allowance = employee.other_allowance if employee else None
            bhxh = employee.rate_bhxh if employee else None

            deleted_records.append(
                PayrollResponse(
                    id=record.id,
                    employee_id=record.employee_id,
                    first_name=first_name,
                    last_name=last_name,
                    salary_id=record.salary_id,
                    penalty_rate=record.penalty_rate,
                    year=record.year,
                    month=record.month,
                    leave=record.leave,
                    unapproved_leave=record.unapproved_leave,
                    base_salary_amount=record.base_salary_amount,
                    overtime_salary_amount=record.overtime_salary_amount,
                    late_penalty=record.late_penalty,
                    total_salary=record.total_salary,
                    note=record.note,
                    lunch_allowance=lunch_allowance,
                    productivity_bonus=productivity_bonus,
                    other_allowance=other_allowance,
                    bhxh=bhxh
                )
            )
            db.delete(record)
            
        db.commit()
        LogInfo(f"[Attendance API] Successfully deleted {len(deleted_records)} payroll records.")

        # Send Telegram notification
        try:
            performer = current_user.employee_id or current_user.username or "unknown"
            details = "Đã xóa bảng lương:\n" + "\n".join(
                [f"- Phiếu ID: {r.id} - Nhân viên: {r.employee_id} ({r.first_name} {r.last_name}) - Tháng: {r.month}/{r.year} - Số tiền: {r.total_salary:,.0f} VNĐ" for r in deleted_records]
            )
            await notify_telegram_group(
                db=db,
                action="DELETE",
                module_key="salaries",
                details=details,
                performer=performer
            )
        except Exception as err:
            LogError(f"[Attendance API] Failed to send Telegram notification: {err}")

        return deleted_records
    except HTTPException:
        raise
    except Exception as e:
        LogInfo(f"[Attendance API] Error in delete-payrolls: {e}")
        raise HTTPException(status_code=500, detail=str(e))




