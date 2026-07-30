"""
REST API endpoints cho Scheduled Notification System.

Endpoints:
  GET    /configs           — Danh sách configs
  POST   /configs           — Tạo config mới
  PUT    /configs/{id}      — Cập nhật config
  DELETE /configs/{id}      — Xóa config
  PATCH  /configs/{id}/toggle — Bật/tắt config
  POST   /configs/{id}/test — Gửi test thủ công
  GET    /logs              — Xem lịch sử gửi
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.db.session import SessionLocal
from app.schemas.scheduled_notification import (
    ScheduledNotifyConfigCreate,
    ScheduledNotifyConfigUpdate,
    ScheduledNotifyConfigResponse,
    ScheduledNotifyLogResponse,
)
from app.crud.scheduled_notification import (
    get_scheduled_notify_configs,
    get_scheduled_notify_config_by_id,
    create_scheduled_notify_config,
    update_scheduled_notify_config,
    delete_scheduled_notify_config,
    toggle_scheduled_notify_config,
    get_scheduled_notify_logs,
    create_scheduled_notify_log,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Config CRUD ──────────────────────────────────────────────────────────────

@router.get("/configs", response_model=List[ScheduledNotifyConfigResponse])
def list_configs(
    module_key: Optional[str] = None,
    notify_type: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
):
    """Danh sách tất cả scheduled notification configs."""
    return get_scheduled_notify_configs(
        db, module_key=module_key, notify_type=notify_type,
        is_enabled=is_enabled, skip=skip, limit=limit
    )


@router.get("/configs/{config_id}", response_model=ScheduledNotifyConfigResponse)
def get_config(config_id: UUID, db: Session = Depends(get_db)):
    """Lấy chi tiết 1 config."""
    config = get_scheduled_notify_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@router.post("/configs", response_model=ScheduledNotifyConfigResponse)
def create_config(
    obj_in: ScheduledNotifyConfigCreate,
    db: Session = Depends(get_db),
):
    """Tạo scheduled notification config mới."""
    return create_scheduled_notify_config(db, obj_in)


@router.put("/configs/{config_id}", response_model=ScheduledNotifyConfigResponse)
def update_config(
    config_id: UUID,
    obj_in: ScheduledNotifyConfigUpdate,
    db: Session = Depends(get_db),
):
    """Cập nhật config."""
    obj_in.id = config_id
    result = update_scheduled_notify_config(db, config_id, obj_in)
    if not result:
        raise HTTPException(status_code=404, detail="Config not found")
    return result


@router.delete("/configs/{config_id}")
def delete_config(config_id: UUID, db: Session = Depends(get_db)):
    """Xóa config."""
    result = delete_scheduled_notify_config(db, config_id)
    if not result:
        raise HTTPException(status_code=404, detail="Config not found")
    return {"message": "Config deleted successfully", "id": str(config_id)}


@router.patch("/configs/{config_id}/toggle", response_model=ScheduledNotifyConfigResponse)
def toggle_config(config_id: UUID, db: Session = Depends(get_db)):
    """Bật/tắt config."""
    result = toggle_scheduled_notify_config(db, config_id)
    if not result:
        raise HTTPException(status_code=404, detail="Config not found")
    return result


# ── Test Send ────────────────────────────────────────────────────────────────

@router.post("/configs/{config_id}/test")
async def test_send(config_id: UUID, db: Session = Depends(get_db)):
    """Gửi test thủ công — bỏ qua schedule check, gửi ngay lập tức."""
    import datetime
    from pyrogram.enums import ParseMode
    from bot.utils.bot import bot
    from bot.utils.notify_resolvers import NOTIFY_RESOLVERS

    config = get_scheduled_notify_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    if not bot.is_connected:
        raise HTTPException(status_code=503, detail="Bot chưa kết nối Telegram")

    resolver = NOTIFY_RESOLVERS.get(config.module_key)
    if not resolver:
        raise HTTPException(status_code=400, detail=f"No resolver for module_key='{config.module_key}'")

    now = datetime.datetime.now()
    results = []

    # Resolve items
    items = resolver.get_pending_items(db, config, now.date(), is_test=True)

    if items is None:
        # Loại tự do
        message = resolver.build_message(None, config)
        if not message:
            raise HTTPException(status_code=400, detail="Config loại tự do chưa có nội dung tin nhắn (message_template)")
        try:
            msg = await bot.send_message(
                chat_id=int(config.chat_id),
                text=message,
                parse_mode=ParseMode.HTML,
            )
            create_scheduled_notify_log(
                db=db, config_id=config.id,
                module_key=config.module_key, notify_type=config.notify_type,
                chat_id=config.chat_id, group_name=config.group_name,
                reference_id=None, reference_name=None,
                message_id=msg.id, message_content=message[:500],
                status="TEST_SUCCESS", scheduled_at=now,
            )
            results.append({"status": "SUCCESS", "message_id": msg.id})
        except Exception as e:
            create_scheduled_notify_log(
                db=db, config_id=config.id,
                module_key=config.module_key, notify_type=config.notify_type,
                chat_id=config.chat_id, group_name=config.group_name,
                reference_id=None, reference_name=None,
                message_id=None, message_content=message[:500] if message else None,
                status="TEST_FAILED", error_message=str(e), scheduled_at=now,
            )
            results.append({"status": "FAILED", "error": str(e)})
    else:
        # Loại Business — gửi tối đa 3 items để test
        for item_data in items[:3]:
            message = resolver.build_message(item_data, config, item_data.get("days_late", 0))
            if not message:
                continue
            try:
                msg = await bot.send_message(
                    chat_id=int(config.chat_id),
                    text=message,
                    parse_mode=ParseMode.HTML,
                )
                create_scheduled_notify_log(
                    db=db, config_id=config.id,
                    module_key=config.module_key, notify_type=config.notify_type,
                    chat_id=config.chat_id, group_name=config.group_name,
                    reference_id=item_data.get("reference_id"), reference_name=item_data.get("reference_name"),
                    message_id=msg.id, message_content=message[:500],
                    status="TEST_SUCCESS", scheduled_at=now,
                )
                results.append({
                    "status": "SUCCESS",
                    "message_id": msg.id,
                    "reference_id": item_data.get("reference_id"),
                })
            except Exception as e:
                create_scheduled_notify_log(
                    db=db, config_id=config.id,
                    module_key=config.module_key, notify_type=config.notify_type,
                    chat_id=config.chat_id, group_name=config.group_name,
                    reference_id=item_data.get("reference_id"), reference_name=item_data.get("reference_name"),
                    message_id=None, message_content=message[:500] if message else None,
                    status="TEST_FAILED", error_message=str(e), scheduled_at=now,
                )
                results.append({
                    "status": "FAILED",
                    "error": str(e),
                    "reference_id": item_data.get("reference_id"),
                })

    return {
        "config_id": str(config_id),
        "notify_type": config.notify_type,
        "total_items": len(items) if items else 0,
        "sent_count": len(results),
        "results": results,
    }


# ── Logs ─────────────────────────────────────────────────────────────────────

@router.get("/logs", response_model=List[ScheduledNotifyLogResponse])
def list_logs(
    config_id: Optional[UUID] = None,
    module_key: Optional[str] = None,
    notify_type: Optional[str] = None,
    status: Optional[str] = None,
    search_query: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Xem lịch sử gửi notification."""
    return get_scheduled_notify_logs(
        db, config_id=config_id, module_key=module_key,
        notify_type=notify_type, status=status,
        search_query=search_query, start_date=start_date,
        end_date=end_date, skip=skip, limit=limit,
    )
