from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas import project as schemas_project
from app.crud import project as crud_project
from app.models.employee import Credential

router = APIRouter()

@router.post("/create_project", response_model=schemas_project.Project)
async def api_create_project(
    project_in: schemas_project.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Create a new project.
    """
    try:
        return crud_project.create_project(db, obj_in=project_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_projects", response_model=list[schemas_project.Project])
async def api_get_projects(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all projects.
    """
    try:
        return crud_project.get_projects(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
