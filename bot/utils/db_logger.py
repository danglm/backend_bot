from app.db.session import SessionLocal
from app.models.telegram import MemberActivityLog
from datetime import datetime
from bot.utils.logger import LogInfo, LogError, LogType

def log_member_activity(chat_id: str, group_name: str, user_id: str, username: str, action: str, admin_id: str = None, admin_username: str = None):
    """
    Logs member activity (JOIN, LEAVE, KICK) to the database.
    """
    db = SessionLocal()
    try:
        new_log = MemberActivityLog(
            chat_id=str(chat_id),
            group_name=str(group_name) if group_name else "Unknown",
            user_id=str(user_id),
            username=str(username) if username else "Unknown",
            action=action.upper(),
            admin_id=str(admin_id) if admin_id else None,
            admin_username=str(admin_username) if admin_username else None,
            timestamp=datetime.now()
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        LogError(f"Failed to log member activity to DB: {e}", LogType.MEMBER_LOG)
        db.rollback()
    finally:
        db.close()

def get_joined_users(chat_id: str) -> list:
    """
    Returns a list of dicts with information about users currently joined in the group.
    """
    db = SessionLocal()
    try:
        logs = db.query(MemberActivityLog).filter(MemberActivityLog.chat_id == str(chat_id)).order_by(MemberActivityLog.timestamp.asc()).all()
        
        users_status = {}
        
        for log in logs:
            if log.action == "JOIN":
                users_status[log.user_id] = {
                    "username": log.username,
                    "join_time": log.timestamp,
                    "status": "JOINED"
                }
            elif log.action in ["LEAVE", "KICK"]:
                if log.user_id in users_status:
                    users_status[log.user_id]["status"] = log.action
        
        joined_users = [
            {"user_id": uid, "username": info["username"], "join_time": info["join_time"]} 
            for uid, info in users_status.items() if info["status"] == "JOINED"
        ]
        
        joined_users.sort(key=lambda x: x["join_time"], reverse=True)
        return joined_users
    except Exception as e:
        LogError(f"Failed to fetch joined users from DB: {e}", LogType.MEMBER_LOG)
        return []
    finally:
        db.close()

def get_left_users(chat_id: str) -> list:
    """
    Returns a list of dicts with information about users who left or were kicked from the group.
    """
    db = SessionLocal()
    try:
        logs = db.query(MemberActivityLog).filter(MemberActivityLog.chat_id == str(chat_id)).order_by(MemberActivityLog.timestamp.asc()).all()
        
        users_status = {}
        for log in logs:
            if log.action == "JOIN":
                users_status[log.user_id] = {
                    "username": log.username,
                    "time": log.timestamp,
                    "status": "JOINED",
                    "admin_name": None
                }
            elif log.action in ["LEAVE", "KICK"]:
                # If they were never JOINED in our logs but we see a LEAVE/KICK, we can optionally still record it.
                if log.user_id not in users_status:
                    users_status[log.user_id] = {
                        "username": log.username,
                        "time": log.timestamp,
                        "status": log.action,
                        "admin_name": log.admin_username
                    }
                else:
                    users_status[log.user_id]["status"] = log.action
                    users_status[log.user_id]["time"] = log.timestamp
                    users_status[log.user_id]["admin_name"] = log.admin_username
                    
        # Filter for those whose final status is LEAVE or KICK
        left_users = [
            {
                "user_id": uid, 
                "username": info["username"], 
                "time": info["time"], 
                "status": info["status"],
                "admin_name": info["admin_name"]
            } 
            for uid, info in users_status.items() if info["status"] in ["LEAVE", "KICK"]
        ]
        
        # Sort by time (most recent first)
        left_users.sort(key=lambda x: x["time"], reverse=True)
        return left_users
    except Exception as e:
        LogError(f"Failed to fetch left users from DB: {e}", LogType.MEMBER_LOG)
        return []
    finally:
        db.close()
