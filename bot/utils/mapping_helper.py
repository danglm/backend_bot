from sqlalchemy.orm import Session
from app.models.telegram import TelegramGroupMapping, TelegramProjectMember
from bot.utils.logger import LogInfo, LogType
from typing import List

def get_target_chat_ids(db: Session, mapping_type: str, source_name: str, fallback_group_name: str = None) -> List[str]:
    """
    Tìm danh sách chat_id từ database dựa trên mapping_type và source_name.
    Nếu không tìm thấy hoặc cấu hình không có chat_id, tìm fallback dùng tên group.
    """
    # 1. Tìm trong DB telegram_group_mappings
    mapping = db.query(TelegramGroupMapping).filter(
        TelegramGroupMapping.mapping_type == mapping_type,
        TelegramGroupMapping.source_name == source_name,
        TelegramGroupMapping.is_active == True
    ).first()

    if mapping:
        # 1.1 Nếu có lưu chat_id thì trả về luôn (cực kỳ chính xác, tránh group đổi tên)
        if mapping.chat_id:
            return [mapping.chat_id]
        
        # 1.2 Nếu có group_name nhưng không có chat_id, tra cứu từ telegram_project_members
        if mapping.group_name:
            members = db.query(TelegramProjectMember.chat_id).filter(
                TelegramProjectMember.group_name == mapping.group_name
            ).distinct().all()
            if members:
                return [m[0] for m in members]

    # 2. Cơ chế Fallback về cấu hình tĩnh (nếu có truyền fallback_group_name)
    if fallback_group_name:
        LogInfo(f"Fallback mapping for {mapping_type}:{source_name} to static group name '{fallback_group_name}'", LogType.SYSTEM_STATUS)
        members = db.query(TelegramProjectMember.chat_id).filter(
            TelegramProjectMember.group_name == fallback_group_name
        ).distinct().all()
        if members:
            return [m[0] for m in members]

    return []
