from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_permission
from app.schemas import rosca as schemas_rosca
from app.crud import rosca as crud_rosca
from app.models.employee import Credential
from app.models.rosca import UserRosca, Rosca, RoscaMember, RoscaContribution
from bot.utils.logger import LogInfo
from typing import Optional, List
from datetime import datetime

router = APIRouter()

# ==========================================
# UserRosca Endpoints (Mã Người Chơi/Chủ Hụi)
# ==========================================

@router.get("/get-user-roscas", response_model=List[schemas_rosca.UserRoscaResponse])
async def api_get_user_roscas(
    id: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    phone_number: Optional[str] = None,
    chat_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Lấy danh sách người chơi/chủ hụi (user roscas).
    """
    LogInfo(f"[Rosca API] Received get-user-roscas request. id: {id}, role: {role}, status: {status}, phone_number: {phone_number}, chat_id: {chat_id}")
    try:
        users = crud_rosca.get_user_roscas(
            db,
            id=id,
            role=role,
            status=status,
            phone_number=phone_number,
            chat_id=chat_id
        )
        LogInfo(f"[Rosca API] Found {len(users)} user roscas.")
        return users
    except Exception as e:
        LogInfo(f"[Rosca API] Error in get-user-roscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-user-roscas", response_model=List[schemas_rosca.UserRoscaResponse])
async def api_add_user_roscas(
    users_in: List[schemas_rosca.UserRoscaCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Thêm mới danh sách người chơi/chủ hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received add-user-roscas request. Total: {len(users_in)}")
    try:
        # Check duplicate IDs in input list itself
        input_ids = [u.id for u in users_in if u.id]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate ID found in the request input."
            )

        # Check existing IDs in database
        existing_users = db.query(UserRosca).filter(UserRosca.id.in_(input_ids)).all()
        if existing_users:
            existing_ids = [u.id for u in existing_users]
            raise HTTPException(
                status_code=400,
                detail=f"Người dùng hụi với mã {existing_ids} đã tồn tại trong hệ thống."
            )

        # Check existing phone numbers or CCCD in input and database to prevent duplicates
        input_phones = [u.phone_number for u in users_in if u.phone_number]
        if len(input_phones) != len(set(input_phones)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate phone_number found in the request input."
            )

        input_cccds = [u.cccd for u in users_in if u.cccd]
        if len(input_cccds) != len(set(input_cccds)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate cccd found in the request input."
            )

        if input_phones:
            existing_phones = db.query(UserRosca).filter(UserRosca.phone_number.in_(input_phones)).all()
            if existing_phones:
                existing_p = [u.phone_number for u in existing_phones]
                raise HTTPException(
                    status_code=400,
                    detail=f"Số điện thoại {existing_p} đã được sử dụng."
                )

        if input_cccds:
            existing_cccds = db.query(UserRosca).filter(UserRosca.cccd.in_(input_cccds)).all()
            if existing_cccds:
                existing_c = [u.cccd for u in existing_cccds]
                raise HTTPException(
                    status_code=400,
                    detail=f"CCCD {existing_c} đã được sử dụng."
                )

        created_users = []
        for user_in in users_in:
            new_user = crud_rosca.create_user_rosca(db, obj_in=user_in)
            created_users.append(new_user)

        LogInfo(f"[Rosca API] Successfully added {len(created_users)} user roscas.")
        return created_users
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in add-user-roscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-user-roscas", response_model=List[schemas_rosca.UserRoscaResponse])
async def api_update_user_roscas(
    users_in: List[schemas_rosca.UserRoscaUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Cập nhật danh sách người chơi/chủ hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received update-user-roscas request. Total: {len(users_in)}")
    try:
        input_ids = [u.id for u in users_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        # Check existing
        existing_users = db.query(UserRosca).filter(UserRosca.id.in_(input_ids)).all()
        existing_map = {u.id: u for u in existing_users}

        missing_ids = [uid for uid in input_ids if uid not in existing_map]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"User roscas with IDs {missing_ids} not found in the database."
            )

        # Validate duplicate phones/cccd for update
        for u_in in users_in:
            user = existing_map[u_in.id]
            if u_in.phone_number and u_in.phone_number != user.phone_number:
                dup = db.query(UserRosca).filter(UserRosca.phone_number == u_in.phone_number).first()
                if dup:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Số điện thoại {u_in.phone_number} đã được sử dụng bởi người khác."
                    )
            if u_in.cccd and u_in.cccd != user.cccd:
                dup = db.query(UserRosca).filter(UserRosca.cccd == u_in.cccd).first()
                if dup:
                    raise HTTPException(
                        status_code=400,
                        detail=f"CCCD {u_in.cccd} đã được sử dụng bởi người khác."
                    )

        updated_users = []
        for user_in in users_in:
            updated_user = crud_rosca.update_user_rosca(db, user_id=user_in.id, obj_in=user_in)
            if updated_user:
                updated_users.append(updated_user)

        LogInfo(f"[Rosca API] Successfully updated {len(updated_users)} user roscas.")
        return updated_users
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in update-user-roscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-user-roscas", response_model=List[schemas_rosca.UserRoscaResponse])
async def api_delete_user_roscas(
    user_ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Xóa danh sách người chơi/chủ hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received delete-user-roscas request. Total: {len(user_ids)}")
    try:
        if len(user_ids) != len(set(user_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        existing_users = db.query(UserRosca).filter(UserRosca.id.in_(user_ids)).all()
        existing_map = {u.id: u for u in existing_users}

        missing_ids = [uid for uid in user_ids if uid not in existing_map]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"User roscas with IDs {missing_ids} not found in the database."
            )

        deleted_users = []
        for user_id in user_ids:
            deleted_user = crud_rosca.delete_user_rosca(db, user_id=user_id)
            if deleted_user:
                deleted_users.append(deleted_user)

        LogInfo(f"[Rosca API] Successfully deleted {len(deleted_users)} user roscas.")
        return deleted_users
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in delete-user-roscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Rosca Endpoints (Cấu Hình Dây Hụi / Bát Hụi)
# ==========================================

@router.get("/get-roscas", response_model=List[schemas_rosca.RoscaResponse])
async def api_get_roscas(
    id: Optional[str] = None,
    code: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Lấy danh sách cấu hình dây hụi (roscas).
    """
    LogInfo(f"[Rosca API] Received get-roscas request. id: {id}, code: {code}, user_id: {user_id}, status: {status}")
    try:
        roscas = crud_rosca.get_roscas(
            db,
            id=id,
            code=code,
            user_id=user_id,
            status=status
        )
        LogInfo(f"[Rosca API] Found {len(roscas)} roscas.")
        return roscas
    except Exception as e:
        LogInfo(f"[Rosca API] Error in get-roscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-roscas", response_model=List[schemas_rosca.RoscaResponse])
async def api_add_roscas(
    roscas_in: List[schemas_rosca.RoscaCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Thêm mới danh sách cấu hình dây hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received add-roscas request. Total: {len(roscas_in)}")
    try:
        # Check duplicate code in input list itself
        input_codes = [r.code for r in roscas_in if r.code]
        if len(input_codes) != len(set(input_codes)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate code found in the request input."
            )

        # Check if any owner exists
        owner_ids = list({r.user_id for r in roscas_in if r.user_id})
        existing_owners = db.query(UserRosca).filter(UserRosca.id.in_(owner_ids), UserRosca.role == "Owner").all()
        existing_owner_ids = {o.id for o in existing_owners}
        
        missing_owners = [oid for oid in owner_ids if oid not in existing_owner_ids]
        if missing_owners:
            raise HTTPException(
                status_code=400,
                detail=f"Không tìm thấy chủ hụi (Owner) với mã: {missing_owners}"
            )

        # Check existing codes in database
        existing_roscas = db.query(Rosca).filter(Rosca.code.in_(input_codes)).all()
        if existing_roscas:
            existing_codes = [r.code for r in existing_roscas]
            raise HTTPException(
                status_code=400,
                detail=f"Dây hụi với mã {existing_codes} đã tồn tại trong hệ thống."
            )

        created_roscas = []
        for r_in in roscas_in:
            new_rosca = crud_rosca.create_rosca(db, obj_in=r_in)
            created_roscas.append(new_rosca)

        # Fetch with owner_name
        created_ids = [r.id for r in created_roscas]
        detailed = crud_rosca.get_roscas(db)
        detailed_filtered = [r for r in detailed if r["id"] in created_ids]

        LogInfo(f"[Rosca API] Successfully added {len(created_roscas)} roscas.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in add-roscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-roscas", response_model=List[schemas_rosca.RoscaResponse])
async def api_update_roscas(
    roscas_in: List[schemas_rosca.RoscaUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Cập nhật danh sách cấu hình dây hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received update-roscas request. Total: {len(roscas_in)}")
    try:
        input_ids = [r.id for r in roscas_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        existing_roscas = db.query(Rosca).filter(Rosca.id.in_(input_ids)).all()
        existing_map = {r.id: r for r in existing_roscas}

        missing_ids = [rid for rid in input_ids if rid not in existing_map]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Roscas with IDs {missing_ids} not found in the database."
            )

        # Verify owner exists if user_id is changed
        owner_ids = list({r.user_id for r in roscas_in if r.user_id})
        if owner_ids:
            existing_owners = db.query(UserRosca).filter(UserRosca.id.in_(owner_ids), UserRosca.role == "Owner").all()
            existing_owner_ids = {o.id for o in existing_owners}
            missing_owners = [oid for oid in owner_ids if oid not in existing_owner_ids]
            if missing_owners:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy chủ hụi (Owner) với mã: {missing_owners}"
                )

        # Verify duplicate codes for update
        for r_in in roscas_in:
            rosca = existing_map[r_in.id]
            if r_in.code and r_in.code != rosca.code:
                dup = db.query(Rosca).filter(Rosca.code == r_in.code).first()
                if dup:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Mã dây hụi {r_in.code} đã được sử dụng."
                    )

        updated_roscas = []
        for r_in in roscas_in:
            updated = crud_rosca.update_rosca(db, rosca_id=r_in.id, obj_in=r_in)
            if updated:
                updated_roscas.append(updated)

        # Fetch with owner_name
        updated_ids = [r.id for r in updated_roscas]
        detailed = crud_rosca.get_roscas(db)
        detailed_filtered = [r for r in detailed if r["id"] in updated_ids]

        LogInfo(f"[Rosca API] Successfully updated {len(updated_roscas)} roscas.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in update-roscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-roscas", response_model=List[schemas_rosca.RoscaResponse])
async def api_delete_roscas(
    rosca_ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Xóa danh sách cấu hình dây hụi (bulk - soft delete).
    """
    LogInfo(f"[Rosca API] Received delete-roscas request. Total: {len(rosca_ids)}")
    try:
        if len(rosca_ids) != len(set(rosca_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        existing_roscas = db.query(Rosca).filter(Rosca.id.in_(rosca_ids)).all()
        existing_map = {r.id: r for r in existing_roscas}

        missing_ids = [rid for rid in rosca_ids if rid not in existing_map]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Roscas with IDs {missing_ids} not found in the database."
            )

        deleted_roscas = []
        for rosca_id in rosca_ids:
            deleted = crud_rosca.delete_rosca(db, rosca_id=rosca_id)
            if deleted:
                deleted_roscas.append(deleted)

        # Fetch with owner_name
        deleted_ids = [r.id for r in deleted_roscas]
        detailed = crud_rosca.get_roscas(db)
        detailed_filtered = [r for r in detailed if r["id"] in deleted_ids]

        LogInfo(f"[Rosca API] Successfully deleted (soft delete) {len(deleted_roscas)} roscas.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in delete-roscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# RoscaMember Endpoints (Chân Hụi)
# ==========================================

@router.get("/get-rosca-members", response_model=List[schemas_rosca.RoscaMemberResponse])
async def api_get_rosca_members(
    id: Optional[str] = None,
    rosca_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    chat_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Lấy danh sách chân hụi (rosca members).
    """
    LogInfo(f"[Rosca API] Received get-rosca-members request. id: {id}, rosca_id: {rosca_id}, user_id: {user_id}, status: {status}, chat_id: {chat_id}")
    try:
        members = crud_rosca.get_rosca_members(
            db,
            id=id,
            rosca_id=rosca_id,
            user_id=user_id,
            status=status,
            chat_id=chat_id
        )
        LogInfo(f"[Rosca API] Found {len(members)} rosca members.")
        return members
    except Exception as e:
        LogInfo(f"[Rosca API] Error in get-rosca-members: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-rosca-members", response_model=List[schemas_rosca.RoscaMemberResponse])
async def api_add_rosca_members(
    members_in: List[schemas_rosca.RoscaMemberCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Thêm mới danh sách chân hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received add-rosca-members request. Total: {len(members_in)}")
    try:
        # Check duplicate (rosca_id, user_id) in input list itself
        input_keys = [(m.rosca_id, m.user_id) for m in members_in]
        if len(input_keys) != len(set(input_keys)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate (rosca_id, user_id) found in the request input."
            )

        # Validate rosca IDs exist
        rosca_ids = list({m.rosca_id for m in members_in if m.rosca_id})
        existing_roscas = db.query(Rosca).filter(Rosca.id.in_(rosca_ids)).all()
        existing_rosca_ids = {r.id for r in existing_roscas}
        missing_roscas = [rid for rid in rosca_ids if rid not in existing_rosca_ids]
        if missing_roscas:
            raise HTTPException(
                status_code=400,
                detail=f"Không tìm thấy dây hụi với ID: {missing_roscas}"
            )

        # Validate user IDs exist
        user_ids = list({m.user_id for m in members_in if m.user_id})
        existing_users = db.query(UserRosca).filter(UserRosca.id.in_(user_ids)).all()
        existing_user_ids = {u.id for u in existing_users}
        missing_users = [uid for uid in user_ids if uid not in existing_user_ids]
        if missing_users:
            raise HTTPException(
                status_code=400,
                detail=f"Không tìm thấy người chơi với ID: {missing_users}"
            )

        # Check existing (rosca_id, user_id) in database where status != 'Deleted'
        for m_in in members_in:
            existing = db.query(RoscaMember).filter(
                RoscaMember.rosca_id == m_in.rosca_id,
                RoscaMember.user_id == m_in.user_id,
                RoscaMember.status != "Deleted"
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Người chơi {m_in.user_id} đã tham gia dây hụi {m_in.rosca_id}."
                )

        created_members = []
        for m_in in members_in:
            new_member = crud_rosca.create_rosca_member(db, obj_in=m_in)
            created_members.append(new_member)

        # Fetch with player_name and rosca_code
        created_ids = [m.id for m in created_members]
        detailed = crud_rosca.get_rosca_members(db)
        detailed_filtered = [m for m in detailed if m["id"] in created_ids]

        LogInfo(f"[Rosca API] Successfully added {len(created_members)} rosca members.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in add-rosca-members: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-rosca-members", response_model=List[schemas_rosca.RoscaMemberResponse])
async def api_update_rosca_members(
    members_in: List[schemas_rosca.RoscaMemberUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Cập nhật danh sách chân hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received update-rosca-members request. Total: {len(members_in)}")
    try:
        input_ids = [m.id for m in members_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        existing_members = db.query(RoscaMember).filter(RoscaMember.id.in_(input_ids)).all()
        existing_map = {m.id: m for m in existing_members}

        missing_ids = [mid for mid in input_ids if mid not in existing_map]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rosca members with IDs {missing_ids} not found in the database."
            )

        # Verify rosca_id/user_id exists if they are changed
        rosca_ids = list({m.rosca_id for m in members_in if m.rosca_id})
        if rosca_ids:
            existing_roscas = db.query(Rosca).filter(Rosca.id.in_(rosca_ids)).all()
            existing_rosca_ids = {r.id for r in existing_roscas}
            missing_roscas = [rid for rid in rosca_ids if rid not in existing_rosca_ids]
            if missing_roscas:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy dây hụi với ID: {missing_roscas}"
                )

        user_ids = list({m.user_id for m in members_in if m.user_id})
        if user_ids:
            existing_users = db.query(UserRosca).filter(UserRosca.id.in_(user_ids)).all()
            existing_user_ids = {u.id for u in existing_users}
            missing_users = [uid for uid in user_ids if uid not in existing_user_ids]
            if missing_users:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy người chơi với ID: {missing_users}"
                )

        updated_members = []
        for m_in in members_in:
            updated = crud_rosca.update_rosca_member(db, member_id=m_in.id, obj_in=m_in)
            if updated:
                updated_members.append(updated)

        # Fetch with player_name and rosca_code
        updated_ids = [m.id for m in updated_members]
        detailed = crud_rosca.get_rosca_members(db)
        detailed_filtered = [m for m in detailed if m["id"] in updated_ids]

        LogInfo(f"[Rosca API] Successfully updated {len(updated_members)} rosca members.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in update-rosca-members: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-rosca-members", response_model=List[schemas_rosca.RoscaMemberResponse])
async def api_delete_rosca_members(
    member_ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Xóa danh sách chân hụi (bulk - soft delete).
    """
    LogInfo(f"[Rosca API] Received delete-rosca-members request. Total: {len(member_ids)}")
    try:
        if len(member_ids) != len(set(member_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        existing_members = db.query(RoscaMember).filter(RoscaMember.id.in_(member_ids)).all()
        existing_map = {m.id: m for m in existing_members}

        missing_ids = [mid for mid in member_ids if mid not in existing_map]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rosca members with IDs {missing_ids} not found in the database."
            )

        deleted_members = []
        for member_id in member_ids:
            deleted = crud_rosca.delete_rosca_member(db, member_id=member_id)
            if deleted:
                deleted_members.append(deleted)

        # Fetch with player_name and rosca_code
        deleted_ids = [m.id for m in deleted_members]
        detailed = crud_rosca.get_rosca_members(db)
        detailed_filtered = [m for m in detailed if m["id"] in deleted_ids]

        LogInfo(f"[Rosca API] Successfully deleted (soft delete) {len(deleted_members)} rosca members.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in delete-rosca-members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# RoscaContribution Endpoints (Giao Dịch Hụi)
# ==========================================

@router.get("/get-rosca-contributions", response_model=List[schemas_rosca.RoscaContributionResponse])
async def api_get_rosca_contributions(
    id: Optional[str] = None,
    rosca_id: Optional[str] = None,
    rosca_code: Optional[str] = None,
    member_id: Optional[str] = None,
    status: Optional[str] = None,
    flow_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Lấy danh sách giao dịch đóng hụi (rosca contributions).
    """
    LogInfo(f"[Rosca API] Received get-rosca-contributions request. id: {id}, rosca_id: {rosca_id}, rosca_code: {rosca_code}, member_id: {member_id}, status: {status}, flow_type: {flow_type}, start_date: {start_date}, end_date: {end_date}")

    parsed_start_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            try:
                parsed_start_date = datetime.strptime(start_date, "%d/%m/%Y").replace(hour=0, minute=0, second=0, microsecond=0)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Expected YYYY-MM-DD or dd/mm/yyyy."
                )

    parsed_end_date = None
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            try:
                parsed_end_date = datetime.strptime(end_date, "%d/%m/%Y").replace(hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Expected YYYY-MM-DD or dd/mm/yyyy."
                )

    try:
        contribs = crud_rosca.get_rosca_contributions(
            db,
            id=id,
            rosca_id=rosca_id,
            rosca_code=rosca_code,
            member_id=member_id,
            status=status,
            flow_type=flow_type,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        LogInfo(f"[Rosca API] Found {len(contribs)} rosca contributions.")
        return contribs
    except Exception as e:
        LogInfo(f"[Rosca API] Error in get-rosca-contributions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-rosca-contributions", response_model=List[schemas_rosca.RoscaContributionResponse])
async def api_add_rosca_contributions(
    contribs_in: List[schemas_rosca.RoscaContributionCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Thêm mới danh sách giao dịch đóng hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received add-rosca-contributions request. Total: {len(contribs_in)}")
    try:
        created_contribs = []
        for c_in in contribs_in:
            # 1. Validate rosca exists
            rosca = db.query(Rosca).filter(Rosca.id == c_in.rosca_id).first()
            if not rosca:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy dây hụi với ID: {c_in.rosca_id}"
                )

            # 2. Validate member exists & support User ID fallback
            member = db.query(RoscaMember).filter(RoscaMember.id == c_in.member_id).first()
            if not member:
                member = db.query(RoscaMember).filter(
                    RoscaMember.user_id == c_in.member_id,
                    RoscaMember.rosca_id == c_in.rosca_id
                ).first()

            if not member:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy chân hụi hoặc người chơi với ID: {c_in.member_id} trong dây hụi {c_in.rosca_id}"
                )

            # Resolve the member_id if we matched user_id fallback
            c_in.member_id = member.id

            # 3. Check amount constraint (must be < 0)
            if c_in.amount >= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Số tiền đóng hụi (amount) luôn luôn phải nhỏ hơn 0 (amount < 0)."
                )

            # 4. Limit check for live member or exact base_amount check for dead member
            if member.status != "Dead":
                base_amount = rosca.base_amount or 0.0
                check_val = base_amount - abs(c_in.amount)

                min_bid = rosca.min_bid_amount
                max_bid = rosca.max_bid_amount if rosca.max_bid_amount is not None else rosca.base_amount

                if min_bid is not None and check_val < min_bid:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Số tiền hốt hụi ({check_val:,.0f} đ) nhỏ hơn mức bỏ hụi tối thiểu ({min_bid:,.0f} đ)."
                    )
                if max_bid is not None and check_val > max_bid:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Số tiền hốt hụi ({check_val:,.0f} đ) lớn hơn mức bỏ hụi tối đa ({max_bid:,.0f} đ)."
                    )
            else:
                # If dead, enforce abs(amount) == base_amount
                base_amount = rosca.base_amount or 0.0
                if abs(c_in.amount) != base_amount:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Chân hụi đã hốt (hụi chết) phải đóng đúng số tiền gốc của dây hụi ({base_amount:,.0f} đ)."
                    )

            # 5. Prevent duplicate transaction on the same day
            payment_date = c_in.actual_payment_date if c_in.actual_payment_date else datetime.now()
            start_of_day = payment_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = payment_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            existing_payment = db.query(RoscaContribution).filter(
                RoscaContribution.member_id == c_in.member_id,
                RoscaContribution.rosca_id == c_in.rosca_id,
                RoscaContribution.actual_payment_date >= start_of_day,
                RoscaContribution.actual_payment_date <= end_of_day
            ).first()

            if existing_payment:
                raise HTTPException(
                    status_code=400,
                    detail=f"Chân hụi {c_in.member_id} đã được ghi nhận đóng tiền trong ngày {payment_date.strftime('%d/%m/%Y')} rồi!"
                )

            # 6. Update member's total_contributed and total_profit
            if c_in.status == "Paid":
                member.total_contributed = (member.total_contributed or 0) + c_in.amount
                if member.status == "Dead" and abs(c_in.amount) == (rosca.base_amount or 0.0):
                    member.total_profit = (member.total_contributed or 0.0) + (member.total_received or 0.0)

            new_contrib = crud_rosca.create_rosca_contribution(db, obj_in=c_in)
            created_contribs.append(new_contrib)

        # Fetch with player_name and rosca_code
        created_ids = [c.id for c in created_contribs]
        detailed = crud_rosca.get_rosca_contributions(db)
        detailed_filtered = [c for c in detailed if c["id"] in created_ids]

        LogInfo(f"[Rosca API] Successfully added {len(created_contribs)} rosca contributions.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in add-rosca-contributions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/withdraw-roscas", response_model=List[schemas_rosca.RoscaContributionResponse])
async def api_withdraw_roscas(
    withdraws_in: List[schemas_rosca.RoscaContributionCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Ghi nhận rút hụi / hốt hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received withdraw-roscas request. Total: {len(withdraws_in)}")
    try:
        created_withdraws = []
        for w_in in withdraws_in:
            # 1. Validate rosca exists
            rosca = db.query(Rosca).filter(Rosca.id == w_in.rosca_id).first()
            if not rosca:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy dây hụi với ID: {w_in.rosca_id}"
                )

            # 2. Validate member exists & support User ID fallback
            member = db.query(RoscaMember).filter(RoscaMember.id == w_in.member_id).first()
            if not member:
                member = db.query(RoscaMember).filter(
                    RoscaMember.user_id == w_in.member_id,
                    RoscaMember.rosca_id == w_in.rosca_id
                ).first()

            if not member:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy chân hụi hoặc người chơi với ID: {w_in.member_id} trong dây hụi {w_in.rosca_id}"
                )

            # Resolve the member_id if we matched user_id fallback
            w_in.member_id = member.id

            # 3. Check amount constraint (must be > 0 for withdrawal)
            if w_in.amount <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Số tiền rút hụi (amount) luôn luôn phải lớn hơn 0 (amount > 0)."
                )

            # 4. Update member's total_received, status, and total_profit
            if w_in.status == "Paid":
                member.total_received = (member.total_received or 0.0) + w_in.amount
                member.status = "Dead"
                member.total_profit = (member.total_contributed or 0.0) + member.total_received

            new_withdraw = crud_rosca.create_rosca_contribution(db, obj_in=w_in)
            created_withdraws.append(new_withdraw)

        # Fetch with player_name and rosca_code
        created_ids = [w.id for w in created_withdraws]
        detailed = crud_rosca.get_rosca_contributions(db)
        detailed_filtered = [c for c in detailed if c["id"] in created_ids]

        LogInfo(f"[Rosca API] Successfully processed {len(created_withdraws)} withdraw-roscas.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in withdraw-roscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-rosca-contributions", response_model=List[schemas_rosca.RoscaContributionResponse])
async def api_update_rosca_contributions(
    contribs_in: List[schemas_rosca.RoscaContributionUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Cập nhật danh sách giao dịch đóng hụi (bulk).
    """
    LogInfo(f"[Rosca API] Received update-rosca-contributions request. Total: {len(contribs_in)}")
    try:
        input_ids = [c.id for c in contribs_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        existing_contribs = db.query(RoscaContribution).filter(RoscaContribution.id.in_(input_ids)).all()
        existing_map = {c.id: c for c in existing_contribs}

        missing_ids = [cid for cid in input_ids if cid not in existing_map]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rosca contributions with IDs {missing_ids} not found in the database."
            )

        # Validate rosca_id / member_id exist if changed
        rosca_ids = list({c.rosca_id for c in contribs_in if c.rosca_id})
        if rosca_ids:
            existing_roscas = db.query(Rosca).filter(Rosca.id.in_(rosca_ids)).all()
            existing_rosca_ids = {r.id for r in existing_roscas}
            missing_roscas = [rid for rid in rosca_ids if rid not in existing_rosca_ids]
            if missing_roscas:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy dây hụi với ID: {missing_roscas}"
                )

        member_ids = list({c.member_id for c in contribs_in if c.member_id})
        if member_ids:
            existing_members = db.query(RoscaMember).filter(RoscaMember.id.in_(member_ids)).all()
            existing_member_ids = {m.id for m in existing_members}
            missing_members = [mid for mid in member_ids if mid not in existing_member_ids]
            if missing_members:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy chân hụi với ID: {missing_members}"
                )

        updated_contribs = []
        for c_in in contribs_in:
            updated = crud_rosca.update_rosca_contribution(db, contrib_id=c_in.id, obj_in=c_in)
            if updated:
                updated_contribs.append(updated)

        # Fetch with player_name and rosca_code
        updated_ids = [c.id for c in updated_contribs]
        detailed = crud_rosca.get_rosca_contributions(db)
        detailed_filtered = [c for c in detailed if c["id"] in updated_ids]

        LogInfo(f"[Rosca API] Successfully updated {len(updated_contribs)} rosca contributions.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in update-rosca-contributions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-rosca-contributions", response_model=List[schemas_rosca.RoscaContributionResponse])
async def api_delete_rosca_contributions(
    contrib_ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rosca"))
):
    """
    Xóa danh sách giao dịch đóng hụi (bulk - physical delete).
    """
    LogInfo(f"[Rosca API] Received delete-rosca-contributions request. Total: {len(contrib_ids)}")
    try:
        if len(contrib_ids) != len(set(contrib_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        existing_contribs = db.query(RoscaContribution).filter(RoscaContribution.id.in_(contrib_ids)).all()
        existing_map = {c.id: c for c in existing_contribs}

        missing_ids = [cid for cid in contrib_ids if cid not in existing_map]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rosca contributions with IDs {missing_ids} not found in the database."
            )

        # Fetch details before delete to return
        detailed = crud_rosca.get_rosca_contributions(db)
        detailed_filtered = [c for c in detailed if c["id"] in existing_map]

        for contrib_id in contrib_ids:
            contrib = existing_map[contrib_id]
            if contrib.status == "Paid":
                member = db.query(RoscaMember).filter(RoscaMember.id == contrib.member_id).first()
                if member:
                    if contrib.amount < 0:
                        member.total_contributed = (member.total_contributed or 0) - contrib.amount
                        rosca = db.query(Rosca).filter(Rosca.id == contrib.rosca_id).first()
                        base_amt = rosca.base_amount or 0.0 if rosca else 0.0
                        if member.status == "Dead" and abs(contrib.amount) == base_amt:
                            member.total_profit = (member.total_contributed or 0.0) + (member.total_received or 0.0)
                    else: # amount > 0 (withdrawal)
                        member.total_received = (member.total_received or 0.0) - contrib.amount
                        if (member.total_received or 0.0) <= 0.0:
                            member.status = "Playing"
                        profit = (member.total_contributed or 0.0) + (member.total_received or 0.0)
                        if profit <= 0:
                            profit = 0.0
                        member.total_profit = profit
            crud_rosca.delete_rosca_contribution(db, contrib_id=contrib_id)

        LogInfo(f"[Rosca API] Successfully deleted {len(contrib_ids)} rosca contributions.")
        return detailed_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rosca API] Error in delete-rosca-contributions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
