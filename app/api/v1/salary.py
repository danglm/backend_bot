from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import re
import calendar
import datetime

from app.api import deps
from app.models.employee import Employee, Credential
from app.models.finance import Attendance, Payroll
from app.schemas.salary import GetSalaryResponse
from bot.utils.scheduler import _is_working_day
from bot.utils.logger import LogInfo

router = APIRouter()


@router.get("/get-salaries", response_model=List[GetSalaryResponse])
def get_salaries(
    *,
    db: Session = Depends(deps.get_db),
    pre_id: Optional[str] = Query(None, description="Employee ID prefix (e.g. TN, G)"),
    date: str = Query(..., description="Date in mm/yyyy format"),
    current_user: Credential = Depends(deps.get_current_user)
):
    """
    Get calculated salaries for employees in a given month.
    """
    LogInfo(f"[Salary API] Request to get salaries for pre_id={pre_id} and date={date}")

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

    # Fetch employees matching prefix if provided
    query = db.query(Employee)
    if pre_id:
        query = query.filter(Employee.id.ilike(f"{pre_id}%"))
    employees = query.all()

    response_list = []
    for employee in employees:
        full_name = f"{employee.last_name or ''} {employee.first_name or ''}".strip()
        
        # Calculate standard working days based on work_type
        emp_work_type = employee.work_type if employee.work_type else 3
        num_days_in_month = calendar.monthrange(year, month)[1]
        standard_days = sum(
            1 for d in range(1, num_days_in_month + 1)
            if _is_working_day(datetime.date(year, month, d).weekday(), emp_work_type)
        )

        # Query attendance records
        attendances = db.query(Attendance).filter(
            Attendance.employee_id == employee.id,
            Attendance.month == month,
            Attendance.year == year
        ).all()

        # Calculate actual workdays
        actual_workdays = 0
        total_overtime = 0.0
        for att in attendances:
            if att.check_in_time is not None or (att.working_time or 0) > 0:
                actual_workdays += 1
            
            if att.overtime:
                total_overtime += att.overtime
            elif att.start_overtime and att.end_overtime:
                diff = (att.end_overtime - att.start_overtime).total_seconds() / 3600
                total_overtime += diff

        # Base salary info
        monthly_salary = employee.monthly_salary or employee.base_salary or 0.0
        base_salary = employee.base_salary or 0.0
        
        # Overtime salary
        overtime_rate = employee.overtime_salary or 0.0
        overtime_salary_amount = total_overtime * overtime_rate
        
        # Allowance, bonus, bhxh
        other_allowance = employee.other_allowance or 0.0
        lunch_allowance = employee.lunch_allowance or 0.0
        productivity_bonus = employee.productivity_bonus or 0.0
        bonus = employee.bonus or 0.0
        bhxh = employee.rate_bhxh or 0.0

        # Query payroll for penalty and status
        payroll_record = db.query(Payroll).filter(
            Payroll.employee_id == employee.id,
            Payroll.month == month,
            Payroll.year == year
        ).first()

        if payroll_record:
            penalty = payroll_record.late_penalty or 0.0
            status = "exported"
        else:
            penalty = 0.0
            status = "draft"

        # Calculate total received
        if standard_days > 0:
            base_received = (monthly_salary / standard_days) * actual_workdays
        else:
            base_received = 0.0

        total_received = base_received + overtime_salary_amount + other_allowance + lunch_allowance + productivity_bonus + bonus - bhxh - penalty

        response_list.append(
            GetSalaryResponse(
                employee_id=employee.id,
                employee_name=full_name,
                standard_workdays=standard_days,
                actual_workdays=actual_workdays,
                base_salary=round(base_salary, 2),
                overtime_salary=round(overtime_salary_amount, 2),
                other_allowance=round(other_allowance, 2),
                lunch_allowance=round(lunch_allowance, 2),
                productivity_bonus=round(productivity_bonus, 2),
                bonus=round(bonus, 2),
                bhxh=round(bhxh, 2),
                penalty=round(penalty, 2),
                received_salary=round(base_received, 2),
                total_received=round(total_received, 2),
                status=status
            )
        )

    return response_list
