from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Iterator, Tuple
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


def _parse_month(date_str: str) -> Tuple[int, int]:
    """Parse a mm/yyyy (or m/yyyy) string into a (year, month) tuple."""
    match = re.match(r"^(\d{1,2})/(\d{4})$", date_str.strip())
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

    return year, month


def _parse_day(date_str: str, field: str) -> datetime.date:
    """Parse a yyyy-mm-dd string into a date."""
    try:
        return datetime.date.fromisoformat(date_str.strip())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field} format. Expected yyyy-mm-dd."
        )


def _month_windows(
    start: datetime.date, end: datetime.date
) -> Iterator[Tuple[int, int, datetime.date, datetime.date]]:
    """
    Split [start, end] into per-calendar-month windows.

    Yields (year, month, window_start, window_end). A window covering a whole
    month spans the 1st to the last day, which is what keeps the month-mode and
    range-mode results identical for a full month.
    """
    cursor = datetime.date(start.year, start.month, 1)
    while cursor <= end:
        last_day = datetime.date(
            cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1]
        )
        yield cursor.year, cursor.month, max(cursor, start), min(last_day, end)
        cursor = last_day + datetime.timedelta(days=1)


def _working_days(
    year: int, month: int, work_type: int, first_day: int = 1, last_day: Optional[int] = None
) -> int:
    """Count working days of a month between first_day and last_day (inclusive)."""
    if last_day is None:
        last_day = calendar.monthrange(year, month)[1]
    return sum(
        1 for d in range(first_day, last_day + 1)
        if _is_working_day(datetime.date(year, month, d).weekday(), work_type)
    )


@router.get("/get-salaries", response_model=List[GetSalaryResponse])
def get_salaries(
    *,
    db: Session = Depends(deps.get_db),
    pre_id: Optional[str] = Query(None, description="Employee ID prefix (e.g. TN, G)"),
    date: Optional[str] = Query(None, description="Month in mm/yyyy format. Alone it selects the whole month; combined with start_date/end_date it says which month the period is filed under."),
    start_date: Optional[str] = Query(None, description="Range start in yyyy-mm-dd format. Must be paired with end_date."),
    end_date: Optional[str] = Query(None, description="Range end in yyyy-mm-dd format. Must be paired with start_date."),
    current_user: Credential = Depends(deps.get_current_user)
):
    """
    Get calculated salaries for employees, either for a whole month (`date`) or
    for an arbitrary day range (`start_date` + `end_date`).

    A range is treated as one single pay period worth one month's pay, not as a
    sum of month fractions. The standard working days are counted inside the
    period itself (05/07 -> 04/08 gives 26 days), and monthly figures — base
    salary, allowances, bonus, BHXH, penalty — are applied once.

    The two parameters combine: `date` picks the month the period is filed under
    and the range picks the actual days, so `date=07/2026` together with
    05/07 -> 04/08 is July's payroll paid over that cycle. Given a range alone,
    the period falls under the month it starts in.

    A range covering exactly one calendar month returns the same numbers as
    month mode.
    """
    LogInfo(
        f"[Salary API] Request to get salaries for pre_id={pre_id}, "
        f"date={date}, start_date={start_date}, end_date={end_date}"
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
    elif date and date.strip():
        year, month = _parse_month(date)
        range_start = datetime.date(year, month, 1)
        range_end = datetime.date(year, month, calendar.monthrange(year, month)[1])
    else:
        raise HTTPException(
            status_code=400,
            detail="Either date (mm/yyyy) or start_date + end_date (yyyy-mm-dd) is required."
        )

    windows = list(_month_windows(range_start, range_end))

    # Which month the period is filed under. An explicit `date` alongside a range
    # wins, otherwise the period falls under the month it starts in.
    period_year, period_month = range_start.year, range_start.month
    if has_range and date and date.strip():
        period_year, period_month = _parse_month(date)
        if (period_year, period_month) not in [(y, m) for y, m, _, _ in windows]:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Month {period_month:02d}/{period_year} is outside the range "
                    f"{range_start.isoformat()} - {range_end.isoformat()}."
                )
            )

    # Fetch employees matching prefix if provided
    query = db.query(Employee)
    if pre_id:
        query = query.filter(Employee.id.ilike(f"{pre_id}%"))
    employees = query.all()

    response_list = []
    for employee in employees:
        full_name = f"{employee.last_name or ''} {employee.first_name or ''}".strip()

        emp_work_type = employee.work_type if employee.work_type else 3

        # Monthly rates taken from the employee record
        base_salary = employee.base_salary or 0.0
        overtime_rate = employee.overtime_salary or 0.0
        other_allowance = employee.other_allowance or 0.0
        lunch_allowance = employee.lunch_allowance or 0.0
        productivity_bonus = employee.productivity_bonus or 0.0
        bonus = employee.bonus or 0.0
        bhxh = employee.rate_bhxh or 0.0

        # Standard working days of the period itself: for 05/07 -> 04/08 this is
        # the 23 working days left in July plus the 3 in August, i.e. 26.
        standard_days = sum(
            _working_days(win_year, win_month, emp_work_type, win_start.day, win_end.day)
            for win_year, win_month, win_start, win_end in windows
        )

        # Attendance across the whole period
        actual_workdays = 0.0
        overtime_hours = 0.0
        for win_year, win_month, win_start, win_end in windows:
            attendances = db.query(Attendance).filter(
                Attendance.employee_id == employee.id,
                Attendance.year == win_year,
                Attendance.month == win_month,
                Attendance.day >= win_start.day,
                Attendance.day <= win_end.day
            ).all()

            for att in attendances:
                if att.check_in_time is not None or (att.working_time or 0) > 0:
                    actual_workdays += 0.5 if att.is_half_day else 1

                if att.overtime:
                    overtime_hours += att.overtime
                elif att.start_overtime and att.end_overtime:
                    diff = (att.end_overtime - att.start_overtime).total_seconds() / 3600
                    overtime_hours += diff

        overtime_salary_amount = overtime_hours * overtime_rate

        # The period belongs to the month it starts in: 05/07 -> 04/08 is July's
        # payroll. That month drives the penalty and the export status.
        payroll_record = db.query(Payroll).filter(
            Payroll.employee_id == employee.id,
            Payroll.month == period_month,
            Payroll.year == period_year
        ).first()

        if payroll_record:
            penalty = payroll_record.late_penalty or 0.0
            status = "exported"
        else:
            penalty = 0.0
            status = "draft"

        # Monthly amounts count once for the period — a period is one month's pay
        if standard_days > 0:
            total_received = (
                (base_salary + overtime_salary_amount + other_allowance + lunch_allowance + productivity_bonus)
                * actual_workdays / standard_days
                + bonus - bhxh - penalty
            )
        else:
            total_received = bonus - bhxh - penalty

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
                received_salary=round(base_salary, 2),
                total_received=round(total_received, 2),
                status=status,
                start_date=range_start,
                end_date=range_end,
                period_year=period_year,
                period_month=period_month,
                is_range=has_range
            )
        )

    return response_list
