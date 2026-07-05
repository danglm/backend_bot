from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.auth import UserRegister, UserLogin, Token, ForgotPassword
from app.crud import credential as crud_credential
from app.core import security
from app.core.config import settings
from bot.utils.logger import LogInfo, LogWarning, LogError, LogType

router = APIRouter()


@router.post("/register", response_model=Token)
def register(obj_in: UserRegister, db: Session = Depends(get_db)):
    LogInfo(f"[Auth] Registering new user: '{obj_in.username}'", LogType.MAIN_LOG)
    user = crud_credential.get_credential_by_username(db, username=obj_in.username)
    if user:
        LogWarning(f"[Auth] Register failed: User with username '{obj_in.username}' already exists.", LogType.MAIN_LOG)
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud_credential.create_credential(db, obj_in=obj_in)
    LogInfo(f"[Auth] User '{obj_in.username}' registered successfully.", LogType.MAIN_LOG)
    access_token_expires = timedelta(minutes=settings.Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.username, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "employee_id": user.employee_id,
    }


@router.post("/login", response_model=Token)
async def login(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    username = None
    password = None
    
    if "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
    else:
        # Default to JSON
        try:
            json_data = await request.json()
            username = json_data.get("username")
            password = json_data.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request body format. Expected JSON or Form data."
            )
            
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username and password are required."
        )

    LogInfo(f"[Auth] Login attempt for user: '{username}'", LogType.MAIN_LOG)
    user = crud_credential.get_credential_by_username(db, username=username)
    if not user or not security.verify_password(password, user.hashed_password):
        LogWarning(f"[Auth] Login failed for user: '{username}' (Incorrect username or password)", LogType.MAIN_LOG)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    elif not user.is_active:
        LogWarning(f"[Auth] Login failed for user: '{username}' (Inactive user)", LogType.MAIN_LOG)
        raise HTTPException(status_code=400, detail="Inactive user")
    
    LogInfo(f"[Auth] User '{username}' logged in successfully.", LogType.MAIN_LOG)
    access_token_expires = timedelta(minutes=settings.Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.username, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "employee_id": user.employee_id,
    }


@router.post("/forgot-password")
def forgot_password(obj_in: ForgotPassword, db: Session = Depends(get_db)):

    LogInfo(f"[Auth] Forgot password request for user: '{obj_in.username}'", LogType.MAIN_LOG)
    user = crud_credential.get_credential_by_username(db, username=obj_in.username)
    if not user:
        LogWarning(f"[Auth] Forgot password failed: User '{obj_in.username}' not found", LogType.MAIN_LOG)
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )
    crud_credential.update_password(db, db_obj=user, new_password=obj_in.new_password)
    LogInfo(f"[Auth] Password updated successfully for user '{obj_in.username}'", LogType.MAIN_LOG)
    return {"message": "Password updated successfully"}


from typing import List
from app.api.deps import require_permission
from app.models.employee import Credential as DBCredential
from app.schemas.employee import Credential as SchemaCredential
from pydantic import BaseModel

class PermissionUpdate(BaseModel):
    permissions: List[str]

@router.get("/get-permissions/{employee_id}", response_model=List[str])
def get_permissions(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: DBCredential = Depends(require_permission("admin"))
):
    """
    Xem quyền (permissions) của một user theo employee_id.
    Chỉ admin mới có quyền xem.
    """
    user = db.query(DBCredential).filter(DBCredential.employee_id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy credential cho nhân viên này."
        )
    return user.permissions or []

@router.put("/update-permissions/{employee_id}", response_model=List[str])
def update_permissions(
    employee_id: str,
    payload: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: DBCredential = Depends(require_permission("admin"))
):
    """
    Cập nhật quyền (permissions) cho user theo employee_id.
    Chỉ admin mới có quyền thực hiện.
    """
    user = db.query(DBCredential).filter(DBCredential.employee_id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy credential cho nhân viên này."
        )
    
    allowed_permissions = {
        "admin", "tien-nga", "ggomoosin", "rental", "credit", 
        "harvest", "project", "vehicle", "document", "attendance", "other", "rosca"
    }
    
    invalid_perms = [p for p in payload.permissions if p not in allowed_permissions]
    if invalid_perms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Các quyền sau không hợp lệ: {invalid_perms}. Quyền hợp lệ gồm: {list(allowed_permissions)}"
        )
        
    user.permissions = list(set(payload.permissions))
    db.commit()
    db.refresh(user)
    return user.permissions

@router.get("/get-all-credentials", response_model=List[SchemaCredential])
def get_all_credentials(
    db: Session = Depends(get_db),
    current_user: DBCredential = Depends(require_permission("admin"))
):
    """
    Lấy danh sách tất cả credential (kèm permissions).
    Chỉ admin mới được lấy danh sách.
    """
    return db.query(DBCredential).all()


from typing import Optional
from app.core.security import get_password_hash

class CredentialUpdatePayload(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

@router.put("/update-credential/{employee_id}", response_model=SchemaCredential)
def update_credential(
    employee_id: str,
    payload: CredentialUpdatePayload,
    db: Session = Depends(get_db),
    current_user: DBCredential = Depends(require_permission("admin"))
):
    """
    Cập nhật thông tin credential của nhân viên.
    Chỉ admin mới có quyền thực hiện.
    """
    user = db.query(DBCredential).filter(DBCredential.employee_id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy credential cho nhân viên này."
        )
    
    if payload.username is not None:
        existing = db.query(DBCredential).filter(
            DBCredential.username == payload.username,
            DBCredential.employee_id != employee_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Tên đăng nhập đã tồn tại."
            )
        user.username = payload.username
        
    if payload.password:
        user.hashed_password = get_password_hash(payload.password)
        
    if payload.role is not None:
        user.role = payload.role
        
    if payload.is_active is not None:
        user.is_active = payload.is_active
        
    db.commit()
    db.refresh(user)
    return user

@router.delete("/delete-credential/{employee_id}")
def delete_credential_api(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: DBCredential = Depends(require_permission("admin"))
):
    """
    Xóa credential của nhân viên theo employee_id.
    Chỉ admin mới có quyền thực hiện.
    """
    user = db.query(DBCredential).filter(DBCredential.employee_id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy credential cho nhân viên này."
        )
    db.delete(user)
    db.commit()
    return {"message": "Xóa tài khoản thành công"}


