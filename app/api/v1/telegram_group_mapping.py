from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.models.employee import Credential
from app.schemas.telegram_group_mapping import (
    TelegramGroupMappingCreate,
    TelegramGroupMappingUpdate,
    TelegramGroupMappingResponse
)
from app.crud import telegram_group_mapping as crud

router = APIRouter()

@router.post("/", response_model=TelegramGroupMappingResponse, status_code=status.HTTP_201_CREATED)
def create_group_mapping(
    *,
    db: Session = Depends(get_db),
    obj_in: TelegramGroupMappingCreate,
    current_user: Credential = Depends(get_current_user)
):
    """
    Tạo mới một cấu hình Telegram group mapping.
    """
    # Check if a mapping for mapping_type & source_name already exists
    existing = crud.get_mapping_by_source(db, mapping_type=obj_in.mapping_type, source_name=obj_in.source_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mapping for type '{obj_in.mapping_type}' and source '{obj_in.source_name}' already exists."
        )
    return crud.create_mapping(db, obj_in=obj_in)

@router.get("/", response_model=List[TelegramGroupMappingResponse])
def read_group_mappings(
    db: Session = Depends(get_db),
    mapping_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: Credential = Depends(get_current_user)
):
    """
    Lấy danh sách các cấu hình Telegram group mapping.
    """
    return crud.get_mappings(db, mapping_type=mapping_type, skip=skip, limit=limit)

@router.get("/{mapping_id}", response_model=TelegramGroupMappingResponse)
def read_group_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Lấy chi tiết một cấu hình Telegram group mapping.
    """
    mapping = crud.get_mapping_by_id(db, mapping_id=mapping_id)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group mapping not found."
        )
    return mapping

@router.put("/{mapping_id}", response_model=TelegramGroupMappingResponse)
def update_group_mapping(
    mapping_id: UUID,
    obj_in: TelegramGroupMappingUpdate,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Cập nhật một cấu hình Telegram group mapping.
    """
    mapping = crud.get_mapping_by_id(db, mapping_id=mapping_id)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group mapping not found."
        )
    return crud.update_mapping(db, mapping_id=mapping_id, obj_in=obj_in)

@router.delete("/{mapping_id}", response_model=TelegramGroupMappingResponse)
def delete_group_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Xóa một cấu hình Telegram group mapping.
    """
    mapping = crud.get_mapping_by_id(db, mapping_id=mapping_id)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group mapping not found."
        )
    return crud.delete_mapping(db, mapping_id=mapping_id)
