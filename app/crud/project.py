from sqlalchemy.orm import Session
from app.models.business import Projects
from app.schemas.project import ProjectCreate, ProjectUpdate
from uuid import UUID
from typing import Optional

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

def update_project(db: Session, project_id: UUID, obj_in: ProjectUpdate) -> Optional[Projects]:
    db_obj = db.query(Projects).filter(Projects.id == project_id).first()
    if not db_obj:
        return None
    
    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]
        
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_project(db: Session, project_id: UUID) -> Optional[Projects]:
    db_obj = db.query(Projects).filter(Projects.id == project_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj

