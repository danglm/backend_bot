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

