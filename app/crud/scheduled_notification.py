import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.scheduled_notification import ScheduledNotifyConfig, ScheduledNotifyLog
from app.schemas.scheduled_notification import ScheduledNotifyConfigCreate, ScheduledNotifyConfigUpdate
from typing import Optional, List
from uuid import UUID


# ── ScheduledNotifyConfig CRUD ────────────────────────────────────────────────

def get_scheduled_notify_configs(
    db: Session,
    module_key: Optional[str] = None,
    notify_type: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 1000,
) -> List[ScheduledNotifyConfig]:
    query = db.query(ScheduledNotifyConfig).order_by(ScheduledNotifyConfig.created_at.desc())
    if module_key:
        query = query.filter(ScheduledNotifyConfig.module_key == module_key)
    if notify_type:
        query = query.filter(ScheduledNotifyConfig.notify_type == notify_type)
    if is_enabled is not None:
        query = query.filter(ScheduledNotifyConfig.is_enabled == is_enabled)
    return query.offset(skip).limit(limit).all()


def get_scheduled_notify_config_by_id(db: Session, config_id: UUID) -> Optional[ScheduledNotifyConfig]:
    return db.query(ScheduledNotifyConfig).filter(ScheduledNotifyConfig.id == config_id).first()


def get_enabled_configs(db: Session) -> List[ScheduledNotifyConfig]:
    """Lấy tất cả configs đang bật — dùng trong unified worker."""
    return db.query(ScheduledNotifyConfig).filter(
        ScheduledNotifyConfig.is_enabled == True
    ).all()


def create_scheduled_notify_config(db: Session, obj_in: ScheduledNotifyConfigCreate) -> ScheduledNotifyConfig:
    db_obj = ScheduledNotifyConfig(
        module_key=obj_in.module_key.strip() if obj_in.module_key else "",
        module_name=obj_in.module_name,
        notify_type=obj_in.notify_type.strip() if obj_in.notify_type else "",
        chat_id=obj_in.chat_id.strip() if obj_in.chat_id else "",
        group_name=obj_in.group_name,
        schedule_type=obj_in.schedule_type,
        schedule_hour=obj_in.schedule_hour,
        schedule_minute=obj_in.schedule_minute,
        schedule_day_of_week=obj_in.schedule_day_of_week,
        schedule_day_of_month=obj_in.schedule_day_of_month,
        schedule_month=obj_in.schedule_month,
        schedule_specific_date=obj_in.schedule_specific_date,
        message_template=obj_in.message_template,
        is_enabled=obj_in.is_enabled,
        max_retry_days=obj_in.max_retry_days,
        escalate_to_chat_id=obj_in.escalate_to_chat_id,
        escalate_after_days=obj_in.escalate_after_days,
        filter_conditions=obj_in.filter_conditions,
        reference_id=obj_in.reference_id,
        reference_name=obj_in.reference_name,
        created_by=obj_in.created_by,
    )
    if obj_in.id is not None:
        db_obj.id = obj_in.id
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_scheduled_notify_config(
    db: Session, config_id: UUID, obj_in: ScheduledNotifyConfigUpdate
) -> Optional[ScheduledNotifyConfig]:
    db_obj = db.query(ScheduledNotifyConfig).filter(ScheduledNotifyConfig.id == config_id).first()
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]

    # Strip string fields
    for field in ("module_key", "notify_type", "chat_id"):
        if field in update_data and update_data[field]:
            update_data[field] = update_data[field].strip()

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_scheduled_notify_config(db: Session, config_id: UUID) -> Optional[ScheduledNotifyConfig]:
    db_obj = db.query(ScheduledNotifyConfig).filter(ScheduledNotifyConfig.id == config_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def toggle_scheduled_notify_config(db: Session, config_id: UUID) -> Optional[ScheduledNotifyConfig]:
    """Bật/tắt config."""
    db_obj = db.query(ScheduledNotifyConfig).filter(ScheduledNotifyConfig.id == config_id).first()
    if not db_obj:
        return None
    db_obj.is_enabled = not db_obj.is_enabled
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ── ScheduledNotifyLog CRUD ──────────────────────────────────────────────────

def create_scheduled_notify_log(
    db: Session,
    config_id: Optional[UUID],
    module_key: str,
    notify_type: str,
    chat_id: str,
    group_name: Optional[str],
    reference_id: Optional[str],
    reference_name: Optional[str],
    message_id: Optional[int],
    message_content: Optional[str],
    status: str,
    error_message: Optional[str] = None,
    scheduled_at: Optional[datetime.datetime] = None,
) -> ScheduledNotifyLog:
    db_obj = ScheduledNotifyLog(
        config_id=config_id,
        module_key=module_key,
        notify_type=notify_type,
        chat_id=chat_id,
        group_name=group_name,
        reference_id=reference_id,
        reference_name=reference_name,
        message_id=message_id,
        message_content=message_content,
        status=status,
        error_message=error_message,
        scheduled_at=scheduled_at,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def check_already_sent_today(
    db: Session,
    config_id: UUID,
    reference_id: Optional[str],
    today: datetime.date,
) -> bool:
    """Kiểm tra đã gửi SUCCESS cho config + reference hôm nay chưa (tránh duplicate)."""
    start_of_day = datetime.datetime.combine(today, datetime.time.min)
    end_of_day = datetime.datetime.combine(today, datetime.time.max)

    query = db.query(ScheduledNotifyLog).filter(
        ScheduledNotifyLog.config_id == config_id,
        ScheduledNotifyLog.status == "SUCCESS",
        ScheduledNotifyLog.sent_at >= start_of_day,
        ScheduledNotifyLog.sent_at <= end_of_day,
    )
    if reference_id:
        query = query.filter(ScheduledNotifyLog.reference_id == reference_id)

    return query.first() is not None


def get_scheduled_notify_logs(
    db: Session,
    config_id: Optional[UUID] = None,
    module_key: Optional[str] = None,
    notify_type: Optional[str] = None,
    status: Optional[str] = None,
    search_query: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[ScheduledNotifyLog]:
    query = db.query(ScheduledNotifyLog).order_by(ScheduledNotifyLog.sent_at.desc())
    if config_id:
        query = query.filter(ScheduledNotifyLog.config_id == config_id)
    if module_key:
        query = query.filter(ScheduledNotifyLog.module_key == module_key)
    if notify_type:
        query = query.filter(ScheduledNotifyLog.notify_type == notify_type)
    if status:
        if status == "SUCCESS":
            query = query.filter(ScheduledNotifyLog.status.in_(["SUCCESS", "TEST_SUCCESS"]))
        elif status == "FAILED":
            query = query.filter(ScheduledNotifyLog.status.in_(["FAILED", "TEST_FAILED"]))
        else:
            query = query.filter(ScheduledNotifyLog.status == status)
    if start_date:
        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(ScheduledNotifyLog.sent_at >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
            query = query.filter(ScheduledNotifyLog.sent_at < end_dt)
        except ValueError:
            pass
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                ScheduledNotifyLog.reference_id.ilike(search_pattern),
                ScheduledNotifyLog.reference_name.ilike(search_pattern),
                ScheduledNotifyLog.message_content.ilike(search_pattern),
            )
        )
    return query.offset(skip).limit(limit).all()
