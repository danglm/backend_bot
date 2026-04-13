from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bot.utils.logger import LogInfo, LogError, LogType
from bot.utils.db_logger import get_joined_users
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas import telegram as schemas_telegram
from app.crud import telegram as crud_telegram
from app.models.employee import Credential
from typing import Optional

router = APIRouter()

class TelegramActionRequest(BaseModel):
    message: str 
    chat_id: int

class MockWaitMsg:
    async def edit_text(self, text: str, parse_mode=None):
        LogInfo(f"[API MockMessage] edit_text: {text}", LogType.SYSTEM_STATUS)

class MockChatType:
    def __init__(self, name="SUPERGROUP"):
        self.name = name

class MockChat:
    def __init__(self, chat_id: int, title: str):
        self.id = chat_id
        self.type = MockChatType()
        self.title = title

class MockUser:
    def __init__(self, user_id=0, first_name="API", last_name="Admin"):
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name

class MockMessage:
    def __init__(self, text: str, chat_id: int, title: str):
        self.text = text
        self.chat = MockChat(chat_id, title)
        self.from_user = MockUser()
        
    async def reply_text(self, text: str, parse_mode=None):
        LogInfo(f"[API MockMessage] reply_text: {text}", LogType.SYSTEM_STATUS)
        return MockWaitMsg()

@router.post("/add_user")
async def api_add_user(request: TelegramActionRequest):
    if not bot.is_connected:
        raise HTTPException(status_code=500, detail="Bot is not connected.")
    
    try:
        # Get info from Telegram group
        chat = await bot.get_chat(request.chat_id)
        chat_title = chat.title or f"Group {request.chat_id}"
        
        # Create fake message
        mock_msg = MockMessage(text=request.message, chat_id=request.chat_id, title=chat_title)
        
        # Push to handler
        await add_user_handler(bot, mock_msg)
        
        return {
            "status": "success", 
            "message": "Add user handler executed",
            "mock_message": request.message,
            "chat_title": chat_title
        }
    except Exception as e:
        LogError(f"API Error in /add_user: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))

class TelegramMultipleActionRequest(BaseModel):
    message: str # Format: "@bot_username /add_users @user1 @user2 +841234..."
    chat_ids: list[int]

# @router.post("/add_users")
# async def api_add_users(request: TelegramMultipleActionRequest):
#     if not bot.is_connected:
#         raise HTTPException(status_code=500, detail="Bot is not connected.")
        
#     results = []
    
#     for chat_id in request.chat_ids:
#         try:
#             # Get info from Telegram group
#             chat = await bot.get_chat(chat_id)
#             chat_title = chat.title or f"Group {chat_id}"
            
#             # Create fake message
#             mock_msg = MockMessage(text=request.message, chat_id=chat_id, title=chat_title)
            
#             # Push to handler
#             await add_user_handler(bot, mock_msg)
            
#             results.append({
#                 "chat_id": chat_id,
#                 "status": "success",
#                 "chat_title": chat_title
#             })
            
#         except Exception as e:
#             LogError(f"API Error in /add_users for chat {chat_id}: {e}", LogType.SYSTEM_STATUS)
#             results.append({
#                 "chat_id": chat_id,
#                 "status": "error",
#                 "detail": str(e)
#             })
            
#     return {
#         "status": "completed",
#         "mock_message": request.message,
#         "results": results
#     }

# @router.post("/kick_users")
# async def api_kick_users(request: TelegramMultipleActionRequest):
#     if not bot.is_connected:
#         raise HTTPException(status_code=500, detail="Bot is not connected.")
        
#     results = []
    
#     for chat_id in request.chat_ids:
#         try:
#             # Get info from Telegram group
#             chat = await bot.get_chat(chat_id)
#             chat_title = chat.title or f"Group {chat_id}"
            
#             # Create fake message
#             mock_msg = MockMessage(text=request.message, chat_id=chat_id, title=chat_title)
            
#             # Push to handler
#             await kick_user_handler(bot, mock_msg)
            
#             results.append({
#                 "chat_id": chat_id,
#                 "status": "success",
#                 "chat_title": chat_title
#             })
            
#         except Exception as e:
#             LogError(f"API Error in /kick_users for chat {chat_id}: {e}", LogType.SYSTEM_STATUS)
#             results.append({
#                 "chat_id": chat_id,
#                 "status": "error",
#                 "detail": str(e)
#             })
            
#     return {
#         "status": "completed",
#         "mock_message": request.message,
#         "results": results
#     }

@router.get("/get_members_in_group")
async def api_get_members_in_group(chat_id: str, source: str = "telegram"):
    """
    Returns a list of currently active members in the specified chat group.
    source: "db" (based on database logs) or "telegram" (fetches directly from Telegram API)
    """
    try:
        if source == "telegram":
            if not bot.is_connected:
                raise HTTPException(status_code=500, detail="Bot is not connected.")
                
            members = []
            async for member in bot.get_chat_members(chat_id):
                user = member.user
                if getattr(user, "is_deleted", False):
                    continue
                    
                name = user.first_name or ""
                if user.last_name:
                    name += f" {user.last_name}"
                    
                members.append({
                    "user_id": str(user.id),
                    "name": name.strip() or "Unknown",
                    "username": user.username or "Unknown",
                    "status": member.status.name if hasattr(member, "status") else "MEMBER"
                })
                
            return {
                "status": "success",
                "chat_id": chat_id,
                "source": "telegram",
                "total_members": len(members),
                "members": members
            }
        else:
            joined_users = get_joined_users(chat_id)
            
            # Convert datetime objects to string format for JSON serialization
            formatted_users = []
            for user in joined_users:
                formatted_users.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "join_time": user["join_time"].isoformat()
                })
                
            return {
                "status": "success",
                "chat_id": chat_id,
                "source": "db",
                "total_members": len(formatted_users),
                "members": formatted_users
            }
    except Exception as e:
        LogError(f"API Error in /get_members_in_group for chat {chat_id}: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_project_member", response_model=schemas_telegram.TelegramProjectMember)
async def api_create_project_member(
    member_in: schemas_telegram.TelegramProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Add a new project member to the database.
    """
    try:
        new_member = crud_telegram.create_project_member(db, obj_in=member_in)
        return new_member
    except Exception as e:
        LogError(f"API Error in /create_project_member: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_project_members", response_model=list[schemas_telegram.TelegramProjectMember])
async def api_get_project_members(
    project_id: Optional[str] = None,
    chat_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get project members from the database.
    """
    try:
        # Convert project_id from str to UUID if it's provided
        from uuid import UUID
        p_uuid = None
        if project_id:
            try:
                p_uuid = UUID(project_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid project_id format")
                
        members = crud_telegram.get_project_members(db, project_id=p_uuid, chat_id=chat_id, skip=skip, limit=limit)
        return members
    except HTTPException as he:
        raise he
    except Exception as e:
        LogError(f"API Error in /get_project_members: {e}", LogType.SYSTEM_STATUS)
        raise HTTPException(status_code=500, detail=str(e))
