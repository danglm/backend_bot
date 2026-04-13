from sqlalchemy.orm import Session
import datetime
from app.models.telegram import TelegramProjectMember
from app.schemas.telegram import TelegramProjectMemberCreate

def create_project_member(db: Session, obj_in: TelegramProjectMemberCreate):
    db_obj = TelegramProjectMember(
        project_id=obj_in.project_id,
        chat_id=obj_in.chat_id,
        user_id=obj_in.user_id,
        user_name=obj_in.user_name,
        full_name=obj_in.full_name,
        role=obj_in.role,
        slot_name=obj_in.slot_name,
        is_bot=obj_in.is_bot,
        member_status=obj_in.member_status,
        custom_title=obj_in.custom_title,
        first_seen_at=obj_in.first_seen_at or datetime.datetime.now(),
        last_seen_at=obj_in.last_seen_at or datetime.datetime.now(),
        last_seen_by=obj_in.last_seen_by
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_project_members(db: Session, project_id = None, chat_id: str = None, skip: int = 0, limit: int = 100):
    query = db.query(TelegramProjectMember)
    if project_id:
        query = query.filter(TelegramProjectMember.project_id == project_id)
    if chat_id:
        query = query.filter(TelegramProjectMember.chat_id == chat_id)
    return query.offset(skip).limit(limit).all()
