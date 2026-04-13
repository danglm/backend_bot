from sqlalchemy.orm import Session
from app.models.employee import Credential
from app.schemas.auth import UserRegister
from app.core.security import get_password_hash


def get_credential_by_username(db: Session, username: str):
    return db.query(Credential).filter(Credential.username == username).first()


def create_credential(db: Session, obj_in: UserRegister):
    hashed_password = get_password_hash(obj_in.password)
    db_obj = Credential(
        username=obj_in.username,
        hashed_password=hashed_password,
        employee_id=obj_in.employee_id,
        role=obj_in.role,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_password(db: Session, db_obj: Credential, new_password: str):
    db_obj.hashed_password = get_password_hash(new_password)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
