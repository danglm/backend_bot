from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud import credential as crud_credential
from app.models.employee import Credential

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> Credential:
    try:
        payload = jwt.decode(
            token, settings.Auth.SECRET_KEY, algorithms=[settings.Auth.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = crud_credential.get_credential_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def require_permission(*required_modules: str):
    """
    Dependency factory: kiểm tra user có permission phù hợp.
    Nếu "admin" nằm trong permissions → bypass, toàn quyền.
    """
    def dependency(current_user: Credential = Depends(get_current_user)):
        user_perms = current_user.permissions or []

        # Admin bypass — toàn quyền
        if "admin" in user_perms:
            return current_user

        # Kiểm tra user có ít nhất 1 permission khớp
        if not any(perm in user_perms for perm in required_modules):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn không có quyền truy cập chức năng này. Yêu cầu quyền: {', '.join(required_modules)}"
            )
        return current_user
    return dependency

