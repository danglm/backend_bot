from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.models.employee import Employee, Credential
from app.crud import employee as crud_employee
from app.schemas import employee as schema_employee

router = APIRouter()

@router.post("/create_employee", response_model=schema_employee.EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_in: schema_employee.EmployeeCreate
):
    """
    Create new employee.
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
    return db_employee

@router.get("/{employee_id}", response_model=schema_employee.EmployeeResponse)
def get_employee(
    employee_id: str,
    db: Session = Depends(deps.get_db)
):
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@router.put("/{employee_id}", response_model=schema_employee.EmployeeResponse)
def update_employee(
    employee_id: str,
    employee_in: schema_employee.EmployeeUpdate,
    db: Session = Depends(deps.get_db)
):
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = employee_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_employee, key, value)

    db.commit()
    db.refresh(db_employee)
    return db_employee

@router.post("/{employee_id}/credential", response_model=schema_employee.Credential)
def create_employee_credential(
    employee_id: str,
    cred_in: schema_employee.CredentialCreate,
    db: Session = Depends(deps.get_db)
):
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return crud_employee.create_credential(db=db, employee_id=employee_id, cred_in=cred_in)
