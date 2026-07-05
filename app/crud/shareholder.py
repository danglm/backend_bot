from sqlalchemy.orm import Session
from app.models.business import Shareholder, Investment
from app.schemas.shareholder import ShareholderCreate, ShareholderUpdate
from typing import Optional, List
from uuid import UUID

def get_shareholders_with_investment_name(
    db: Session,
    investment_id: Optional[UUID] = None,
    shareholder_code: Optional[str] = None
) -> List[dict]:
    query = db.query(Shareholder, Investment.name).outerjoin(
        Investment, Shareholder.investment_id == Investment.id
    )

    if investment_id is not None:
        query = query.filter(Shareholder.investment_id == investment_id)
    if shareholder_code is not None:
        query = query.filter(Shareholder.shareholder_code.ilike(f"%{shareholder_code.strip()}%"))

    results = query.all()

    data = []
    for sh, name in results:
        data.append({
            "id": sh.id,
            "shareholder_code": sh.shareholder_code,
            "fullname": sh.fullname,
            "investment_id": sh.investment_id,
            "investment_amount": sh.investment_amount,
            "start_date": sh.start_date,
            "username": sh.username,
            "telegram_group": sh.telegram_group,
            "notes": sh.notes,
            "created_at": sh.created_at,
            "investment_name": name
        })
    return data

def create_shareholder(db: Session, obj_in: ShareholderCreate) -> Shareholder:
    db_obj = Shareholder(
        shareholder_code=obj_in.shareholder_code,
        fullname=obj_in.fullname,
        investment_id=obj_in.investment_id,
        investment_amount=obj_in.investment_amount,
        start_date=obj_in.start_date,
        username=obj_in.username,
        telegram_group=obj_in.telegram_group,
        notes=obj_in.notes
    )
    if obj_in.id is not None:
        db_obj.id = obj_in.id
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_shareholder(db: Session, shareholder_id: UUID, obj_in: ShareholderUpdate) -> Optional[Shareholder]:
    db_obj = db.query(Shareholder).filter(Shareholder.id == shareholder_id).first()
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_shareholder(db: Session, shareholder_id: UUID) -> Optional[Shareholder]:
    db_obj = db.query(Shareholder).filter(Shareholder.id == shareholder_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj
