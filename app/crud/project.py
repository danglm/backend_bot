from sqlalchemy.orm import Session
from app.models.business import Projects
from app.schemas.project import ProjectCreate

def create_project(db: Session, obj_in: ProjectCreate):
    db_obj = Projects(
        project_name=obj_in.project_name
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Projects).offset(skip).limit(limit).all()
