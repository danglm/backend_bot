from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.auth import UserRegister, UserLogin, Token, ForgotPassword
from app.crud import credential as crud_credential
from app.core import security
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=Token)
def register(obj_in: UserRegister, db: Session = Depends(get_db)):
    user = crud_credential.get_credential_by_username(db, username=obj_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud_credential.create_credential(db, obj_in=obj_in)
    access_token_expires = timedelta(minutes=settings.Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.username, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
def login(obj_in: UserLogin, db: Session = Depends(get_db)):
    user = crud_credential.get_credential_by_username(db, username=obj_in.username)
    if not user or not security.verify_password(obj_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.username, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/forgot-password")
def forgot_password(obj_in: ForgotPassword, db: Session = Depends(get_db)):
    user = crud_credential.get_credential_by_username(db, username=obj_in.username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )
    crud_credential.update_password(db, db_obj=user, new_password=obj_in.new_password)
    return {"message": "Password updated successfully"}
