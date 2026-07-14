"""
Hàm tổng quát gửi thông báo hành vi xuống nhóm Telegram.
Dùng được từ API endpoint, scheduler, bot handler, v.v.
"""
import datetime
from typing import Optional
from sqlalchemy.orm import Session
from pyrogram.enums import ParseMode

from bot.utils.bot import bot
from bot.utils.logger import LogInfo, LogError, LogType
from app.crud.notification import get_notify_config_by_module_key, create_notify_log


# Map action → (icon, label tiếng Việt)
ACTION_MAP = {
    "CREATE":  ("➕", "Thêm mới"),
    "UPDATE":  ("✏️", "Cập nhật"),
    "DELETE":  ("🗑️", "Xóa"),
    "PROCESS": ("⚡", "Xử lý"),
}


def _build_notify_message(
    action: str,
    module_name: str,
    details: str,
    performer: str,
    project_name: str = "",
) -> str:
    """Build formatted HTML message cho Telegram."""
    icon, label = ACTION_MAP.get(action.upper(), ("🔔", action))
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    lines = [
        f"📢 <b>THÔNG BÁO THAY ĐỔI</b>",
        f"",
        f"<b>Hành vi:</b> {label}",
        f"<b>Tính năng:</b> {module_name}",
    ]

    if project_name:
        lines.append(f"<b>Dự án:</b> {project_name}")

    lines.append(f"<b>Thực hiện bởi:</b> <code>{performer}</code>")
    lines.append(f"")
    lines.append(f"<b>Chi tiết:</b>")
    lines.append(details)
    lines.append(f"")
    lines.append(f"🕐 {now_str}")

    return "\n".join(lines)


async def notify_telegram_group(
    db: Session,
    action: str,
    module_key: str,
    details: str,
    performer: str,
) -> dict:
    """
    Gửi thông báo hành vi xuống nhóm Telegram dựa trên cấu hình trong notify_configs.

    Args:
        db: Database session
        action: Loại hành vi (CREATE / UPDATE / DELETE / PROCESS)
        module_key: Mã tính năng (customers, daily_purchases, ...)
        details: Nội dung chi tiết
        performer: Mã nhân viên từ Credential.employee_id (VD: TN001)

    Returns:
        dict: {"success": bool, "message_id": int|None, "chat_id": str, "error": str|None}
    """
    try:
        # 1. Lookup config
        config = get_notify_config_by_module_key(db, module_key)
        if not config:
            return {
                "success": False,
                "message_id": None,
                "chat_id": None,
                "error": f"Không tìm thấy cấu hình notify cho module_key='{module_key}' hoặc đã tắt."
            }

        # 2. Check action allowed
        allowed_actions = [a.strip().upper() for a in config.actions.split(",")]
        if action.upper() not in allowed_actions:
            return {
                "success": False,
                "message_id": None,
                "chat_id": config.chat_id,
                "error": f"Action '{action}' không nằm trong danh sách cho phép: {config.actions}"
            }

        # 3. Check bot connected
        if not bot.is_connected:
            # Log FAILED
            create_notify_log(
                db=db,
                config_id=config.id,
                action=action.upper(),
                module_key=config.module_key,
                module_name=config.module_name,
                project_name=config.project_name,
                chat_id=config.chat_id,
                group_name=config.group_name,
                performer=performer,
                details=details,
                message_id=None,
                status="FAILED",
                error_message="Bot chưa kết nối Telegram.",
            )
            return {
                "success": False,
                "message_id": None,
                "chat_id": config.chat_id,
                "error": "Bot chưa kết nối Telegram."
            }

        # 4. Build message
        html_text = _build_notify_message(
            action=action,
            module_name=config.module_name,
            details=details,
            performer=performer,
            project_name=config.project_name or "",
        )

        # 5. Send message
        try:
            chat_id_int = int(config.chat_id)
        except (ValueError, TypeError):
            create_notify_log(
                db=db,
                config_id=config.id,
                action=action.upper(),
                module_key=config.module_key,
                module_name=config.module_name,
                project_name=config.project_name,
                chat_id=config.chat_id,
                group_name=config.group_name,
                performer=performer,
                details=details,
                message_id=None,
                status="FAILED",
                error_message=f"Chat ID '{config.chat_id}' không hợp lệ.",
            )
            return {
                "success": False,
                "message_id": None,
                "chat_id": config.chat_id,
                "error": f"Chat ID '{config.chat_id}' không hợp lệ."
            }

        msg = await bot.send_message(
            chat_id=chat_id_int,
            text=html_text,
            parse_mode=ParseMode.HTML,
        )

        # 6. Log SUCCESS
        create_notify_log(
            db=db,
            config_id=config.id,
            action=action.upper(),
            module_key=config.module_key,
            module_name=config.module_name,
            project_name=config.project_name,
            chat_id=config.chat_id,
            group_name=config.group_name,
            performer=performer,
            details=details,
            message_id=msg.id,
            status="SUCCESS",
        )

        LogInfo(
            f"[Notify] Sent {action} notification for {module_key} by {performer} → chat {config.chat_id} (msg_id={msg.id})",
            LogType.SYSTEM_STATUS,
        )

        return {
            "success": True,
            "message_id": msg.id,
            "chat_id": config.chat_id,
            "error": None,
        }

    except Exception as e:
        LogError(f"[Notify] Error sending notification: {e}", LogType.SYSTEM_STATUS)

        # Log FAILED
        try:
            create_notify_log(
                db=db,
                config_id=config.id if config else None,
                action=action.upper(),
                module_key=module_key,
                module_name=config.module_name if config else module_key,
                project_name=config.project_name if config else None,
                chat_id=config.chat_id if config else "unknown",
                group_name=config.group_name if config else None,
                performer=performer,
                details=details,
                message_id=None,
                status="FAILED",
                error_message=str(e),
            )
        except Exception:
            pass  # Tránh lỗi chồng lỗi

        return {
            "success": False,
            "message_id": None,
            "chat_id": config.chat_id if config else None,
            "error": str(e),
        }
