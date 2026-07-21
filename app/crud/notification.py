from sqlalchemy.orm import Session
from app.models.notification import NotifyConfig, NotifyLog
from app.schemas.notification import NotifyConfigCreate, NotifyConfigUpdate
from typing import Optional, List
from uuid import UUID


# ── NotifyConfig CRUD ─────────────────────────────────────────────────────────

def get_notify_configs(
    db: Session,
    module_key: Optional[str] = None,
    project_name: Optional[str] = None,
    enable_only: bool = False,
    skip: int = 0,
    limit: int = 1000
) -> List[NotifyConfig]:
    query = db.query(NotifyConfig)
    if module_key:
        query = query.filter(NotifyConfig.module_key == module_key)
    if project_name:
        query = query.filter(NotifyConfig.project_name == project_name)
    if enable_only:
        query = query.filter(NotifyConfig.enable_send_notify == True)
    return query.offset(skip).limit(limit).all()


def get_notify_config_by_module_key(db: Session, module_key: str) -> Optional[NotifyConfig]:
    """Lấy config theo module_key (chỉ lấy config đang bật)."""
    stripped_key = module_key.strip() if module_key else ""
    return db.query(NotifyConfig).filter(
        NotifyConfig.module_key == stripped_key,
        NotifyConfig.enable_send_notify == True
    ).first()


def create_notify_config(db: Session, obj_in: NotifyConfigCreate) -> NotifyConfig:
    db_obj = NotifyConfig(
        module_key=obj_in.module_key.strip() if obj_in.module_key else "",
        module_name=obj_in.module_name,
        project_name=obj_in.project_name,
        chat_id=obj_in.chat_id,
        group_name=obj_in.group_name,
        actions=obj_in.actions,
        enable_send_notify=obj_in.enable_send_notify,
    )
    if obj_in.id is not None:
        db_obj.id = obj_in.id
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_notify_config(db: Session, config_id: UUID, obj_in: NotifyConfigUpdate) -> Optional[NotifyConfig]:
    db_obj = db.query(NotifyConfig).filter(NotifyConfig.id == config_id).first()
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]
    if "module_key" in update_data and update_data["module_key"]:
        update_data["module_key"] = update_data["module_key"].strip()

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_notify_config(db: Session, config_id: UUID) -> Optional[NotifyConfig]:
    db_obj = db.query(NotifyConfig).filter(NotifyConfig.id == config_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


# ── NotifyLog CRUD ────────────────────────────────────────────────────────────

def create_notify_log(
    db: Session,
    config_id: Optional[UUID],
    action: str,
    module_key: str,
    module_name: str,
    project_name: Optional[str],
    chat_id: str,
    group_name: Optional[str],
    performer: str,
    details: str,
    message_id: Optional[int],
    status: str,
    error_message: Optional[str] = None,
) -> NotifyLog:
    db_obj = NotifyLog(
        config_id=config_id,
        action=action,
        module_key=module_key,
        module_name=module_name,
        project_name=project_name,
        chat_id=chat_id,
        group_name=group_name,
        performer=performer,
        details=details,
        message_id=message_id,
        status=status,
        error_message=error_message,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_notify_logs(
    db: Session,
    module_key: Optional[str] = None,
    performer: Optional[str] = None,
    status: Optional[str] = None,
    project_name: Optional[str] = None,
    search_query: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[NotifyLog]:
    from sqlalchemy import or_
    import datetime
    query = db.query(NotifyLog).order_by(NotifyLog.created_at.desc())
    if module_key:
        query = query.filter(NotifyLog.module_key == module_key)
    if performer:
        query = query.filter(NotifyLog.performer == performer)
    if status:
        query = query.filter(NotifyLog.status == status)
    if project_name:
        query = query.filter(NotifyLog.project_name == project_name)
    if start_date:
        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(NotifyLog.created_at >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
            query = query.filter(NotifyLog.created_at < end_dt)
        except ValueError:
            pass
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                NotifyLog.performer.ilike(search_pattern),
                NotifyLog.details.ilike(search_pattern),
                NotifyLog.module_name.ilike(search_pattern),
                NotifyLog.module_key.ilike(search_pattern),
            )
        )
    return query.offset(skip).limit(limit).all()
