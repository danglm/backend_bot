from sqlalchemy.orm import Session
from app.models.employee import Credential
from app.schemas.employee import CredentialCreate
from app.core.security import get_password_hash

def create_credential(db: Session, employee_id: str, cred_in: CredentialCreate):
    hashed_password = get_password_hash(cred_in.password)
    db_credential = Credential(
        employee_id=employee_id,
        username=cred_in.username,
        hashed_password=hashed_password,
        role=cred_in.role,
        is_active=cred_in.is_active
    )
    db.add(db_credential)
    db.commit()
    db.refresh(db_credential)
    return db_credential
