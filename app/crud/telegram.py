from sqlalchemy.orm import Session
import datetime
from app.models.telegram import TelegramProjectMember
from app.schemas.telegram import TelegramProjectMemberCreate, TelegramProjectMemberUpdate
from uuid import UUID
from typing import Optional, List

def create_project_member(db: Session, obj_in: TelegramProjectMemberCreate):
    db_obj = TelegramProjectMember(
        project_id=obj_in.project_id,
        chat_id=obj_in.chat_id,
        group_name=obj_in.group_name,
        user_id=obj_in.user_id,
        user_name=obj_in.user_name,
        full_name=obj_in.full_name,
        role=obj_in.role,
        slot_name=obj_in.slot_name,
        is_bot=obj_in.is_bot,
        member_status=obj_in.member_status,
        custom_title=obj_in.custom_title,
        parent_id=obj_in.parent_id,
        first_seen_at=obj_in.first_seen_at or datetime.datetime.now(),
        last_seen_at=obj_in.last_seen_at or datetime.datetime.now(),
        last_seen_by=obj_in.last_seen_by
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_project_members(
    db: Session,
    project_id: Optional[UUID] = None,
    chat_id: Optional[str] = None,
    username: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TelegramProjectMember]:
    query = db.query(TelegramProjectMember)
    if project_id:
        query = query.filter(TelegramProjectMember.project_id == project_id)
    if chat_id:
        query = query.filter(TelegramProjectMember.chat_id == chat_id)
    if username:
        # Check against both user_name (Telegram username)
        query = query.filter(TelegramProjectMember.user_name.ilike(f"%{username.strip()}%"))
    if role:
        query = query.filter(TelegramProjectMember.role.ilike(f"%{role.strip()}%"))
    return query.offset(skip).limit(limit).all()

def update_project_member(db: Session, member_id: UUID, obj_in: TelegramProjectMemberUpdate) -> Optional[TelegramProjectMember]:
    db_obj = db.query(TelegramProjectMember).filter(TelegramProjectMember.id == member_id).first()
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

def delete_project_member(db: Session, member_id: UUID) -> Optional[TelegramProjectMember]:
    db_obj = db.query(TelegramProjectMember).filter(TelegramProjectMember.id == member_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def get_telegram_groups(
    db: Session,
    project_id: UUID,
    role: str,
    parent_id: Optional[str] = None,
) -> List[dict]:
    """
    Get distinct Telegram groups for a project, grouped by chat_id.
    - role='main': returns main groups (no parent_id filter)
    - role='member': requires parent_id to filter member groups
    """
    query = db.query(TelegramProjectMember).filter(
        TelegramProjectMember.project_id == project_id,
        TelegramProjectMember.role == role,
    )
    if role == "member" and parent_id:
        query = query.filter(TelegramProjectMember.parent_id == parent_id)

    members = query.all()

    # Group by chat_id
    groups_map: dict = {}
    for m in members:
        if m.chat_id not in groups_map:
            groups_map[m.chat_id] = {
                "chat_id": m.chat_id,
                "group_name": m.group_name,
                "member_count": 0,
                "custom_title": m.custom_title,
            }
        groups_map[m.chat_id]["member_count"] += 1

    return list(groups_map.values())

