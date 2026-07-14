from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.api import deps
from app.models.employee import Employee, Credential
from app.schemas import employee as schema_employee
from bot.utils.logger import LogInfo, LogError
from app.services.notification import notify_telegram_group

router = APIRouter()

@router.get("/get-employee", response_model=List[schema_employee.EmployeeResponse])
def get_employee(
    *,
    db: Session = Depends(deps.get_db),
    pre_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Credential = Depends(deps.get_current_user)
):
    """
    Get all employees, optionally filtering by ID prefix (pre_id) and/or status.
    """
    query = db.query(Employee)
    if pre_id:
        query = query.filter(Employee.id.ilike(f"{pre_id}%"))
    if status:
        query = query.filter(Employee.status == status)
        
    return query.all()


@router.post("/add-employee", response_model=schema_employee.EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def add_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_in: schema_employee.EmployeeCreate,
    current_user: Credential = Depends(deps.get_current_user)
):
    """
    Create a new employee.
    """
    # Check if employee ID already exists
    db_employee = db.query(Employee).filter(Employee.id == employee_in.id).first()
    if db_employee:
        raise HTTPException(
            status_code=400,
            detail="Employee with this ID already exists in the system.",
        )
    
    # Check if email already exists
    if employee_in.email:
        db_employee_email = db.query(Employee).filter(Employee.email == employee_in.email).first()
        if db_employee_email:
            raise HTTPException(
                status_code=400,
                detail="Employee with this email already exists in the system.",
            )

    # Check if username already exists
    if employee_in.username:
        db_employee_username = db.query(Employee).filter(Employee.username == employee_in.username).first()
        if db_employee_username:
            raise HTTPException(
                status_code=400,
                detail="Employee with this username already exists in the system.",
            )

    db_employee = Employee(**employee_in.model_dump())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

    # Send Telegram notification
    try:
        performer = current_user.employee_id or current_user.username or "unknown"
        fullname = f"{db_employee.last_name or ''} {db_employee.first_name or ''}".strip()
        details = f"Đã thêm mới nhân viên:\n- Mã nhân viên: {db_employee.id}\n- Họ tên: {fullname}\n- SĐT: {db_employee.number_phone or 'N/A'}"
        await notify_telegram_group(
            db=db,
            action="CREATE",
            module_key="employees",
            details=details,
            performer=performer
        )
    except Exception as err:
        LogError(f"[Employee API] Failed to send Telegram notification: {err}")

    return db_employee


@router.post("/update-employee", response_model=schema_employee.EmployeeResponse)
async def update_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_in: schema_employee.EmployeeUpdate,
    current_user: Credential = Depends(deps.get_current_user)
):
    """
    Update an employee.
    """
    db_employee = db.query(Employee).filter(Employee.id == employee_in.id).first()
    if not db_employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    # If updating email, check if it's already taken by another employee
    if employee_in.email:
        db_employee_email = db.query(Employee).filter(
            Employee.email == employee_in.email,
            Employee.id != employee_in.id
        ).first()
        if db_employee_email:
            raise HTTPException(
                status_code=400,
                detail="Employee with this email already exists in the system.",
            )

    # If updating username, check if it's already taken by another employee
    if employee_in.username:
        db_employee_username = db.query(Employee).filter(
            Employee.username == employee_in.username,
            Employee.id != employee_in.id
        ).first()
        if db_employee_username:
            raise HTTPException(
                status_code=400,
                detail="Employee with this username already exists in the system.",
            )

    update_data = employee_in.model_dump(exclude_unset=True)
    update_data.pop("id", None)
    
    for key, value in update_data.items():
        setattr(db_employee, key, value)

    db.commit()
    db.refresh(db_employee)

    # Send Telegram notification
    try:
        performer = current_user.employee_id or current_user.username or "unknown"
        fullname = f"{db_employee.last_name or ''} {db_employee.first_name or ''}".strip()
        details = f"Đã cập nhật nhân viên:\n- Mã nhân viên: {db_employee.id}\n- Họ tên: {fullname}\n- SĐT: {db_employee.number_phone or 'N/A'}"
        await notify_telegram_group(
            db=db,
            action="UPDATE",
            module_key="employees",
            details=details,
            performer=performer
        )
    except Exception as err:
        LogError(f"[Employee API] Failed to send Telegram notification: {err}")

    return db_employee


@router.delete("/delete-employee", response_model=List[schema_employee.EmployeeResponse])
async def delete_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_ids: List[str] = Body(...),
    current_user: Credential = Depends(deps.get_current_user)
):
    """
    Delete employees by list of IDs in request body.
    """
    LogInfo(f"[Employee API] Received delete-employee request. Total employees to delete: {len(employee_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(employee_ids) != len(set(employee_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate employee IDs found in the request input."
            )
            
        # Check if all employee IDs exist in the database
        existing_employees = db.query(Employee).filter(Employee.id.in_(employee_ids)).all()
        existing_ids = {e.id for e in existing_employees}
        
        missing_ids = [eid for eid in employee_ids if eid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Employees with IDs {missing_ids} not found in the database."
            )
            
        deleted_employees = []
        for employee in existing_employees:
            deleted_employees.append(employee)
            
            # Delete associated credentials if any
            db.query(Credential).filter(Credential.employee_id == employee.id).delete(synchronize_session=False)
            
            # Delete employee
            db.delete(employee)
            
        db.commit()
        LogInfo(f"[Employee API] Successfully deleted {len(deleted_employees)} employees.")

        # Send Telegram notification
        try:
            performer = current_user.employee_id or current_user.username or "unknown"
            details = "Đã xóa nhân viên:\n" + "\n".join(
                [f"- Mã nhân viên: {e.id} - Họ tên: {e.last_name or ''} {e.first_name or ''}" for e in deleted_employees]
            )
            await notify_telegram_group(
                db=db,
                action="DELETE",
                module_key="employees",
                details=details,
                performer=performer
            )
        except Exception as err:
            LogError(f"[Employee API] Failed to send Telegram notification: {err}")

        return deleted_employees
        
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Employee API] Error in delete-employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))
