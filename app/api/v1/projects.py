from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.crud.project import create_project, get_projects, update_project, delete_project
from app.models.employee import Credential
from app.models.business import Projects
from bot.utils.logger import LogInfo
from typing import List
from uuid import UUID

router = APIRouter()

@router.get("/get-projects", response_model=List[Project])
def get_projects_api(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    LogInfo("[Projects API] Received get-projects request.")
    try:
        results = get_projects(db, limit=1000)
        LogInfo(f"[Projects API] Found {len(results)} projects.")
        return results
    except Exception as e:
        LogInfo(f"[Projects API] Error in get-projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-projects", response_model=List[Project])
def add_projects_api(
    projects_in: List[ProjectCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    LogInfo(f"[Projects API] Received add-projects request. Total projects to add: {len(projects_in)}")
    try:
        created_projects = []
        for project_in in projects_in:
            new_project = create_project(db, obj_in=project_in)
            created_projects.append(new_project)
            
        LogInfo(f"[Projects API] Successfully added {len(created_projects)} projects.")
        return created_projects
    except Exception as e:
        LogInfo(f"[Projects API] Error in add-projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-projects", response_model=List[Project])
def update_projects_api(
    projects_in: List[ProjectUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    LogInfo(f"[Projects API] Received update-projects request. Total projects to update: {len(projects_in)}")
    try:
        input_ids = [p.id for p in projects_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate project IDs found in the request input."
            )
            
        # Check if all project IDs exist in the database
        existing_projects = db.query(Projects).filter(Projects.id.in_(input_ids)).all()
        existing_ids = {p.id for p in existing_projects}
        
        missing_ids = [pid for pid in input_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Projects with IDs {missing_ids} not found in the database."
            )
            
        updated_projects = []
        for project_in in projects_in:
            updated_project = update_project(db, project_id=project_in.id, obj_in=project_in)
            if updated_project:
                updated_projects.append(updated_project)
            
        LogInfo(f"[Projects API] Successfully updated {len(updated_projects)} projects.")
        return updated_projects
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Projects API] Error in update-projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-projects", response_model=List[Project])
def delete_projects_api(
    project_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    LogInfo(f"[Projects API] Received delete-projects request. Total projects to delete: {len(project_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(project_ids) != len(set(project_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate project IDs found in the request input."
            )
            
        # Check if all project IDs exist in the database
        existing_projects = db.query(Projects).filter(Projects.id.in_(project_ids)).all()
        existing_ids = {p.id for p in existing_projects}
        
        missing_ids = [pid for pid in project_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Projects with IDs {missing_ids} not found in the database."
            )
            
        deleted_projects = []
        for project in existing_projects:
            deleted_projects.append(project)
            delete_project(db, project_id=project.id)
            
        LogInfo(f"[Projects API] Successfully deleted {len(deleted_projects)} projects.")
        return deleted_projects
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Projects API] Error in delete-projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from app.schemas.telegram import TelegramProjectMember as SchemaTelegramProjectMember, TelegramProjectMemberCreate, TelegramProjectMemberUpdate, TelegramGroupInfo
from app.crud.telegram import create_project_member, get_project_members, update_project_member, delete_project_member, get_telegram_groups
from app.models.telegram import TelegramProjectMember as DBTelegramProjectMember
from typing import Optional


@router.get("/get-telegram-groups", response_model=List[TelegramGroupInfo])
def get_telegram_groups_api(
    project_id: UUID,
    role: str,
    parent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    LogInfo(f"[Projects API] get-telegram-groups. project_id={project_id}, role={role}, parent_id={parent_id}")
    try:
        # Validate role
        if role not in ("main", "member"):
            raise HTTPException(status_code=400, detail="role must be 'main' or 'member'.")

        # role=main must NOT have parent_id
        if role == "main" and parent_id:
            raise HTTPException(status_code=400, detail="parent_id is not allowed when role is 'main'.")

        # role=member MUST have parent_id
        if role == "member" and not parent_id:
            raise HTTPException(status_code=400, detail="parent_id is required when role is 'member'.")

        results = get_telegram_groups(db, project_id=project_id, role=role, parent_id=parent_id)
        LogInfo(f"[Projects API] Found {len(results)} telegram groups.")
        return results
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Projects API] Error in get-telegram-groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-telegram-project-members", response_model=List[SchemaTelegramProjectMember])
def get_telegram_project_members_api(
    project_id: Optional[UUID] = None,
    chat_id: Optional[str] = None,
    username: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    LogInfo(f"[Projects API] get-telegram-project-members. project_id={project_id}, chat_id={chat_id}, username={username}, role={role}")
    try:
        results = get_project_members(
            db, project_id=project_id, chat_id=chat_id, username=username, role=role, limit=1000
        )
        LogInfo(f"[Projects API] Found {len(results)} telegram project members.")
        return results
    except Exception as e:
        LogInfo(f"[Projects API] Error in get-telegram-project-members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-telegram-project-members", response_model=List[SchemaTelegramProjectMember])
def add_telegram_project_members_api(
    members_in: List[TelegramProjectMemberCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    LogInfo(f"[Projects API] add-telegram-project-members. Count: {len(members_in)}")
    try:
        created_members = []
        for member_in in members_in:
            new_member = create_project_member(db, obj_in=member_in)
            created_members.append(new_member)
            
        LogInfo(f"[Projects API] Successfully added {len(created_members)} telegram project members.")
        return created_members
    except Exception as e:
        LogInfo(f"[Projects API] Error in add-telegram-project-members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-telegram-project-members", response_model=List[SchemaTelegramProjectMember])
def update_telegram_project_members_api(
    members_in: List[TelegramProjectMemberUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    LogInfo(f"[Projects API] update-telegram-project-members. Count: {len(members_in)}")
    try:
        input_ids = [m.id for m in members_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate member IDs found in the request input."
            )
            
        # Check if all member IDs exist in the database
        existing_members = db.query(DBTelegramProjectMember).filter(DBTelegramProjectMember.id.in_(input_ids)).all()
        existing_ids = {m.id for m in existing_members}
        
        missing_ids = [mid for mid in input_ids if mid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Telegram project members with IDs {missing_ids} not found in the database."
            )
            
        updated_members = []
        for member_in in members_in:
            updated_member = update_project_member(db, member_id=member_in.id, obj_in=member_in)
            if updated_member:
                updated_members.append(updated_member)
                
        LogInfo(f"[Projects API] Successfully updated {len(updated_members)} telegram project members.")
        return updated_members
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Projects API] Error in update-telegram-project-members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-telegram-project-members", response_model=List[SchemaTelegramProjectMember])
def delete_telegram_project_members_api(
    member_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    LogInfo(f"[Projects API] delete-telegram-project-members. Count: {len(member_ids)}")
    try:
        if len(member_ids) != len(set(member_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate member IDs found in the request input."
            )
            
        existing_members = db.query(DBTelegramProjectMember).filter(DBTelegramProjectMember.id.in_(member_ids)).all()
        existing_ids = {m.id for m in existing_members}
        
        missing_ids = [mid for mid in member_ids if mid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Telegram project members with IDs {missing_ids} not found in the database."
            )
            
        deleted_members = []
        for member in existing_members:
            deleted_members.append(member)
            delete_project_member(db, member_id=member.id)
            
        LogInfo(f"[Projects API] Successfully deleted {len(deleted_members)} telegram project members.")
        return deleted_members
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Projects API] Error in delete-telegram-project-members: {e}")
        raise HTTPException(status_code=500, detail=str(e))

