from sqlalchemy.orm import Session
from app.models.finance import Salary
from app.schemas.salary import SalaryCreate, SalaryUpdate
from uuid import UUID

def get_salary(db: Session, salary_id: UUID):
    return db.query(Salary).filter(Salary.id == salary_id).first()

def get_salary_by_employee_id(db: Session, employee_id: str):
    return db.query(Salary).filter(Salary.employee_id == employee_id).first()

def create_salary(db: Session, salary: SalaryCreate):
    db_salary = Salary(**salary.dict())
    db.add(db_salary)
    db.commit()
    db.refresh(db_salary)
    return db_salary

def update_salary(db: Session, employee_id: str, salary_update: SalaryUpdate):
    db_salary = get_salary_by_employee_id(db, employee_id)
    if not db_salary:
        return None
    
    update_data = salary_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_salary, key, value)
    
    db.commit()
    db.refresh(db_salary)
    return db_salary

def delete_salary(db: Session, employee_id: str):
    db_salary = get_salary_by_employee_id(db, employee_id)
    if not db_salary:
        return None
    db.delete(db_salary)
    db.commit()
    return db_salary
