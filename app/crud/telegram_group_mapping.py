from sqlalchemy.orm import Session
from app.models.telegram import TelegramGroupMapping
from app.schemas.telegram_group_mapping import TelegramGroupMappingCreate, TelegramGroupMappingUpdate
from uuid import UUID
from typing import Optional, List

def get_mapping_by_id(db: Session, mapping_id: UUID) -> Optional[TelegramGroupMapping]:
    return db.query(TelegramGroupMapping).filter(TelegramGroupMapping.id == mapping_id).first()

def get_mappings(
    db: Session,
    mapping_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TelegramGroupMapping]:
    query = db.query(TelegramGroupMapping)
    if mapping_type:
        query = query.filter(TelegramGroupMapping.mapping_type == mapping_type)
    return query.offset(skip).limit(limit).all()

def get_mapping_by_source(db: Session, mapping_type: str, source_name: str) -> Optional[TelegramGroupMapping]:
    return db.query(TelegramGroupMapping).filter(
        TelegramGroupMapping.mapping_type == mapping_type,
        TelegramGroupMapping.source_name == source_name,
        TelegramGroupMapping.is_active == True
    ).first()

def create_mapping(db: Session, obj_in: TelegramGroupMappingCreate) -> TelegramGroupMapping:
    db_obj = TelegramGroupMapping(
        mapping_type=obj_in.mapping_type,
        source_name=obj_in.source_name,
        group_name=obj_in.group_name,
        chat_id=obj_in.chat_id,
        is_active=obj_in.is_active if obj_in.is_active is not None else True
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_mapping(
    db: Session,
    mapping_id: UUID,
    obj_in: TelegramGroupMappingUpdate
) -> Optional[TelegramGroupMapping]:
    db_obj = db.query(TelegramGroupMapping).filter(TelegramGroupMapping.id == mapping_id).first()
    if not db_obj:
        return None
    
    update_data = obj_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_mapping(db: Session, mapping_id: UUID) -> Optional[TelegramGroupMapping]:
    db_obj = db.query(TelegramGroupMapping).filter(TelegramGroupMapping.id == mapping_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj
