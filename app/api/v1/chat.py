from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Query, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
import datetime
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.models.employee import Credential
from app.models.telegram import TelegramProjectMember
from app.models.business import Projects
from app.models.chat import TelegramChatMessage, TelegramChatMessageEdit, TelegramChatAttachment
from app.services.chat_socket import chat_ws_manager
from bot.utils.bot import bot
from bot.core.config import settings
from bot.utils.logger import LogInfo, LogError, LogType

router = APIRouter()


class SendMessageSchema(BaseModel):
    chat_id: str
    text_content: Optional[str] = None
    message: Optional[str] = None  # Backward compatibility field
    reply_to_message_id: Optional[int] = None


# ══════════════════════════════════════════════════════════════════════════════
# ── WebSocket Real-time Endpoint ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

@router.websocket("/chat/ws")
async def chat_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket Endpoint dành cho Frontend Web Chat.
    Path: WS /api/v1/telegram/chat/ws
    Sử dụng để nhận các sự kiện Real-time: NEW_MESSAGE, MESSAGE_EDITED, MESSAGE_DELETED.
    """
    client_ip = websocket.client.host if websocket.client else "unknown"
    client_port = websocket.client.port if websocket.client else "0"
    LogInfo(f"[ChatWS Connection Request] Incoming WebSocket handshake from {client_ip}:{client_port}", LogType.SYSTEM_STATUS)

    await chat_ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            LogInfo(f"[ChatWS Frame Received] From {client_ip}:{client_port} -> Payload: {data}", LogType.SYSTEM_STATUS)
    except WebSocketDisconnect:
        LogInfo(f"[ChatWS Disconnected] Client {client_ip}:{client_port} closed connection cleanly", LogType.SYSTEM_STATUS)
        chat_ws_manager.disconnect(websocket)
    except Exception as e:
        LogError(f"[ChatWS Exception] Unexpected socket error from {client_ip}:{client_port}: {e}", LogType.SYSTEM_STATUS)
        chat_ws_manager.disconnect(websocket)


# ══════════════════════════════════════════════════════════════════════════════
# ── REST API Endpoints ────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/chat/groups")
def get_chat_groups_api(
    project_id: Optional[UUID] = None,
    search_query: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Path: GET /api/v1/telegram/chat/groups
    Lấy danh sách tất cả các nhóm Telegram đã syncchat,
    kèm theo thông tin tin nhắn mới nhất (last message) cho cột bên trái của Web Chat.
    """
    try:
        query = db.query(
            TelegramProjectMember.chat_id,
            TelegramProjectMember.group_name,
            TelegramProjectMember.project_id,
            TelegramProjectMember.role,
            TelegramProjectMember.custom_title
        )
        if project_id:
            query = query.filter(TelegramProjectMember.project_id == project_id)

        distinct_groups = query.distinct(TelegramProjectMember.chat_id).all()

        results = []
        for g in distinct_groups:
            chat_id = g.chat_id
            group_name = g.group_name or f"Nhóm {chat_id}"

            if search_query and search_query.strip():
                if search_query.lower() not in group_name.lower():
                    continue

            project_name = None
            if g.project_id:
                proj = db.query(Projects).filter(Projects.id == g.project_id).first()
                if proj:
                    project_name = proj.project_name

            last_msg = db.query(TelegramChatMessage).filter(
                TelegramChatMessage.chat_id == chat_id,
                TelegramChatMessage.is_deleted == False
            ).order_by(desc(TelegramChatMessage.date)).first()

            msg_count = db.query(func.count(TelegramChatMessage.id)).filter(
                TelegramChatMessage.chat_id == chat_id,
                TelegramChatMessage.is_deleted == False
            ).scalar() or 0

            last_msg_dict = None
            if last_msg:
                last_msg_dict = {
                    "id": str(last_msg.id),
                    "message_id": last_msg.message_id,
                    "sender_name": last_msg.full_name or last_msg.username or last_msg.user_id,
                    "message_type": last_msg.message_type,
                    "text_content": last_msg.text_content,
                    "date": last_msg.date.isoformat() if last_msg.date else None
                }

            results.append({
                "chat_id": chat_id,
                "group_name": group_name,
                "project_id": str(g.project_id) if g.project_id else None,
                "project_name": project_name,
                "role": g.role,
                "custom_title": g.custom_title,
                "total_messages": msg_count,
                "last_message": last_msg_dict,
                "last_activity": last_msg.date.isoformat() if (last_msg and last_msg.date) else None
            })

        results.sort(key=lambda x: x["last_activity"] or "", reverse=True)
        return results
    except Exception as e:
        LogError(f"API Error in /telegram/chat/groups: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/messages")
def get_chat_messages_api(
    chat_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    before_message_id: Optional[int] = None,
    search_query: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Path: GET /api/v1/telegram/chat/messages
    Lấy danh sách tin nhắn từ CSDL của nhóm chat_id cụ thể,
    hỗ trợ phân trang cuộn vô tận, đính kèm file media, reply info và cờ edit/delete.
    """
    try:
        query = db.query(TelegramChatMessage).filter(
            TelegramChatMessage.chat_id == chat_id,
            TelegramChatMessage.is_deleted == False
        )

        if before_message_id:
            query = query.filter(TelegramChatMessage.message_id < before_message_id)

        if search_query and search_query.strip():
            query = query.filter(TelegramChatMessage.text_content.ilike(f"%{search_query.strip()}%"))

        messages = query.order_by(desc(TelegramChatMessage.date), desc(TelegramChatMessage.message_id)).offset(skip).limit(limit).all()

        formatted_messages = []
        for msg in reversed(messages):
            attachments = db.query(TelegramChatAttachment).filter(
                TelegramChatAttachment.message_db_id == msg.id
            ).all()

            att_list = []
            for att in attachments:
                att_list.append({
                    "id": str(att.id),
                    "file_type": att.file_type,
                    "file_id": att.file_id,
                    "file_name": att.file_name,
                    "file_size": att.file_size,
                    "mime_type": att.mime_type,
                    "download_url": f"/api/v1/telegram/chat/media/{att.id}" if att.local_path else None
                })

            edit_count = db.query(func.count(TelegramChatMessageEdit.id)).filter(
                TelegramChatMessageEdit.message_db_id == msg.id
            ).scalar() or 0

            formatted_messages.append({
                "id": str(msg.id),
                "message_id": msg.message_id,
                "chat_id": msg.chat_id,
                "group_name": msg.group_name,
                "project_id": str(msg.project_id) if msg.project_id else None,
                "user_id": msg.user_id,
                "username": msg.username,
                "full_name": msg.full_name,
                "is_bot": msg.is_bot,
                "is_mine": True if (msg.full_name and ("Bot (" in msg.full_name or "Admin" in msg.full_name or "Web" in msg.full_name)) else False,
                "message_type": msg.message_type,
                "text_content": msg.text_content,
                "reply_to_message_id": msg.reply_to_message_id,
                "reply_to_user_id": msg.reply_to_user_id,
                "thread_id": msg.thread_id,
                "has_media": msg.has_media,
                "is_edited": msg.is_edited,
                "edited_at": msg.edited_at.isoformat() if msg.edited_at else None,
                "edit_count": edit_count,
                "attachments": att_list,
                "date": msg.date.isoformat() if msg.date else None,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            })

        return {
            "chat_id": chat_id,
            "total_count": len(formatted_messages),
            "messages": formatted_messages
        }
    except Exception as e:
        LogError(f"API Error in /telegram/chat/messages: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-message")
async def send_chat_message_api(
    request: SendMessageSchema,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Path: POST /api/v1/telegram/send-message
    Gửi tin nhắn văn bản từ Web Dashboard xuống nhóm Telegram qua Bot API,
    tự động lưu vào CSDL và broadcast tới tất cả Web clients qua WebSocket.
    """
    if not bot.is_connected:
        raise HTTPException(status_code=500, detail="Telegram Bot chưa kết nối.")

    text_to_send = request.text_content or request.message or ""
    if not text_to_send:
        raise HTTPException(status_code=400, detail="Nội dung tin nhắn không được để trống.")

    try:
        chat_id_int = int(request.chat_id)
        
        sent_msg = await bot.send_message(
            chat_id=chat_id_int,
            text=text_to_send,
            reply_to_message_id=request.reply_to_message_id
        )

        performer_name = current_user.employee_id or current_user.username or "Web Admin"

        synced_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == request.chat_id
        ).first()

        project_id = synced_member.project_id if synced_member else None
        group_name = sent_msg.chat.title or (synced_member.group_name if synced_member else None)

        new_msg = TelegramChatMessage(
            message_id=sent_msg.id,
            chat_id=request.chat_id,
            group_name=group_name,
            project_id=project_id,
            user_id=str(bot.me.id) if bot.me else "bot",
            username=bot.me.username if bot.me else "bot",
            full_name=f"Bot ({performer_name})",
            is_bot=True,
            message_type="text",
            text_content=text_to_send,
            reply_to_message_id=request.reply_to_message_id,
            has_media=False,
            date=sent_msg.date or datetime.datetime.now()
        )
        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)

        msg_dict = {
            "id": str(new_msg.id),
            "message_id": new_msg.message_id,
            "chat_id": new_msg.chat_id,
            "group_name": new_msg.group_name,
            "project_id": str(new_msg.project_id) if new_msg.project_id else None,
            "user_id": new_msg.user_id,
            "username": new_msg.username,
            "full_name": new_msg.full_name,
            "is_bot": new_msg.is_bot,
            "is_mine": True,
            "message_type": new_msg.message_type,
            "text_content": new_msg.text_content,
            "reply_to_message_id": new_msg.reply_to_message_id,
            "has_media": False,
            "date": new_msg.date.isoformat() if new_msg.date else None,
            "created_at": new_msg.created_at.isoformat() if new_msg.created_at else None
        }

        await chat_ws_manager.broadcast_event("NEW_MESSAGE", msg_dict)

        return {
            "status": "success",
            "message_id": sent_msg.id,
            "chat_id": request.chat_id,
            "text": text_to_send,
            "data": msg_dict
        }

    except Exception as e:
        db.rollback()
        LogError(f"API Error in /telegram/send-message: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-attachment")
@router.post("/send-document")
async def send_chat_attachment_api(
    chat_id: str = Form(...),
    caption: Optional[str] = Form(""),
    reply_to_message_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Path: POST /api/v1/telegram/send-attachment (hoặc /send-document)
    Gửi file/ảnh từ Web Dashboard xuống Telegram qua Bot API,
    lưu file đĩa Server (`uploads/chat_media`), lưu bản ghi CSDL và broadcast qua WebSocket.
    """
    if not bot.is_connected:
        raise HTTPException(status_code=500, detail="Telegram Bot chưa kết nối.")

    now = datetime.datetime.now()
    relative_dir = os.path.join(settings.MEDIA_STORAGE_PATH, f"{now.year}", f"{now.month:02d}")
    abs_dir = os.path.join(os.getcwd(), relative_dir)
    os.makedirs(abs_dir, exist_ok=True)

    timestamp_str = int(now.timestamp())
    saved_filename = f"{timestamp_str}_{file.filename}"
    target_file_path = os.path.join(abs_dir, saved_filename)
    relative_file_path = os.path.join(relative_dir, saved_filename).replace("\\", "/")

    try:
        with open(target_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chat_id_int = int(chat_id)
        is_photo = file.content_type.startswith("image/") if file.content_type else False

        if is_photo:
            sent_msg = await bot.send_photo(
                chat_id=chat_id_int,
                photo=target_file_path,
                caption=caption,
                reply_to_message_id=reply_to_message_id
            )
            file_type = "photo"
            telegram_media = sent_msg.photo
        else:
            sent_msg = await bot.send_document(
                chat_id=chat_id_int,
                document=target_file_path,
                caption=caption,
                reply_to_message_id=reply_to_message_id
            )
            file_type = "document"
            telegram_media = sent_msg.document

        performer_name = current_user.employee_id or current_user.username or "Web Admin"

        synced_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        project_id = synced_member.project_id if synced_member else None
        group_name = sent_msg.chat.title or (synced_member.group_name if synced_member else None)

        new_msg = TelegramChatMessage(
            message_id=sent_msg.id,
            chat_id=chat_id,
            group_name=group_name,
            project_id=project_id,
            user_id=str(bot.me.id) if bot.me else "bot",
            username=bot.me.username if bot.me else "bot",
            full_name=f"Bot ({performer_name})",
            is_bot=True,
            message_type=file_type,
            text_content=caption,
            reply_to_message_id=reply_to_message_id,
            has_media=True,
            date=sent_msg.date or datetime.datetime.now()
        )
        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)

        file_id = getattr(telegram_media, "file_id", str(sent_msg.id))
        file_unique_id = getattr(telegram_media, "file_unique_id", None)
        file_size = getattr(telegram_media, "file_size", os.path.getsize(target_file_path))

        attachment = TelegramChatAttachment(
            message_db_id=new_msg.id,
            file_type=file_type,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_name=file.filename,
            file_size=file_size,
            mime_type=file.content_type,
            local_path=relative_file_path
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)

        msg_dict = {
            "id": str(new_msg.id),
            "message_id": new_msg.message_id,
            "chat_id": new_msg.chat_id,
            "group_name": new_msg.group_name,
            "project_id": str(new_msg.project_id) if new_msg.project_id else None,
            "user_id": new_msg.user_id,
            "username": new_msg.username,
            "full_name": new_msg.full_name,
            "is_bot": new_msg.is_bot,
            "is_mine": True,
            "message_type": new_msg.message_type,
            "text_content": new_msg.text_content,
            "reply_to_message_id": new_msg.reply_to_message_id,
            "has_media": True,
            "attachments": [
                {
                    "id": str(attachment.id),
                    "file_type": attachment.file_type,
                    "file_name": attachment.file_name,
                    "file_size": attachment.file_size,
                    "mime_type": attachment.mime_type,
                    "download_url": f"/api/v1/telegram/chat/media/{attachment.id}"
                }
            ],
            "date": new_msg.date.isoformat() if new_msg.date else None,
            "created_at": new_msg.created_at.isoformat() if new_msg.created_at else None
        }

        await chat_ws_manager.broadcast_event("NEW_MESSAGE", msg_dict)

        return {
            "status": "success",
            "message_id": sent_msg.id,
            "chat_id": chat_id,
            "filename": file.filename,
            "data": msg_dict
        }

    except Exception as e:
        db.rollback()
        LogError(f"API Error in /telegram/send-attachment: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/media/{attachment_id}")
def get_chat_media_file_api(
    attachment_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Path: GET /api/v1/telegram/chat/media/{attachment_id}
    Đọc và phục vụ download / hiển thị file media trực tiếp từ đĩa Server cho Web Frontend.
    """
    try:
        attachment = db.query(TelegramChatAttachment).filter(
            TelegramChatAttachment.id == attachment_id
        ).first()

        if not attachment or not attachment.local_path:
            raise HTTPException(status_code=404, detail="Attachment file not found in database.")

        abs_file_path = os.path.join(os.getcwd(), attachment.local_path)
        if not os.path.exists(abs_file_path):
            raise HTTPException(status_code=404, detail="File does not exist on server disk.")

        return FileResponse(
            path=abs_file_path,
            filename=attachment.file_name or "file",
            media_type=attachment.mime_type or "application/octet-stream"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        LogError(f"API Error in /telegram/chat/media/{attachment_id}: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/messages/{message_id}")
async def delete_chat_message_api(
    message_id: str,
    chat_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Path: DELETE /api/v1/telegram/chat/messages/{message_id}
    Xóa tin nhắn từ Web Chat: xóa tin nhắn khỏi CSDL, thử xóa khỏi nhóm Telegram (nếu bot có quyền admin/là tác giả) và broadcast WebSocket event MESSAGE_DELETED.
    """
    try:
        query = db.query(TelegramChatMessage).filter(TelegramChatMessage.is_deleted == False)
        try:
            msg_uuid = UUID(message_id)
            query = query.filter(TelegramChatMessage.id == msg_uuid)
        except ValueError:
            query = query.filter(TelegramChatMessage.message_id == int(message_id))
            if chat_id:
                query = query.filter(TelegramChatMessage.chat_id == chat_id)

        target_msg = query.first()
        if not target_msg:
            raise HTTPException(status_code=404, detail="Tin nhắn không tồn tại hoặc đã bị xóa.")

        # 1. Try deleting message on Telegram if bot is connected
        if bot.is_connected:
            try:
                await bot.delete_messages(chat_id=int(target_msg.chat_id), message_ids=target_msg.message_id)
                LogInfo(f"[ChatAPI] Successfully deleted Telegram message_id={target_msg.message_id} in chat={target_msg.chat_id}")
            except Exception as tg_err:
                LogError(f"[ChatAPI] Warning: Could not delete message on Telegram API: {tg_err}")

        # 2. Mark as deleted in CSDL
        target_msg.is_deleted = True
        target_msg.deleted_at = datetime.datetime.now()
        db.commit()

        # 3. Broadcast WebSocket event
        event_data = {
            "id": str(target_msg.id),
            "chat_id": target_msg.chat_id,
            "message_id": target_msg.message_id
        }
        await chat_ws_manager.broadcast_event("MESSAGE_DELETED", event_data)

        return {
            "status": "success",
            "message": "Đã xóa tin nhắn thành công.",
            "data": event_data
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        LogError(f"API Error in /telegram/chat/messages/{message_id}: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))

