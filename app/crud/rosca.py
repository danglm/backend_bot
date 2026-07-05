from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid
from app.models.rosca import UserRosca, Rosca, RoscaMember, RoscaContribution
from app.schemas.rosca import UserRoscaCreate, UserRoscaUpdate, RoscaCreate, RoscaUpdate, RoscaMemberCreate, RoscaMemberUpdate, RoscaContributionCreate, RoscaContributionUpdate

def get_user_roscas(
    db: Session,
    id: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    phone_number: Optional[str] = None
):
    query = db.query(UserRosca)
    if id is not None:
        query = query.filter(UserRosca.id == id)
    if role is not None:
        query = query.filter(UserRosca.role == role)
    if status is not None:
        query = query.filter(UserRosca.status == status)
    if phone_number is not None:
        query = query.filter(UserRosca.phone_number == phone_number)
    return query.all()

def create_user_rosca(db: Session, obj_in: UserRoscaCreate):
    db_obj = UserRosca(
        id=obj_in.id,
        full_name=obj_in.full_name,
        username=obj_in.username,
        phone_number=obj_in.phone_number,
        cccd=obj_in.cccd,
        role=obj_in.role,
        status=obj_in.status
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_user_rosca(db: Session, user_id: str, obj_in: UserRoscaUpdate) -> Optional[UserRosca]:
    db_obj = db.query(UserRosca).filter(UserRosca.id == user_id).first()
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

def delete_user_rosca(db: Session, user_id: str) -> Optional[UserRosca]:
    db_obj = db.query(UserRosca).filter(UserRosca.id == user_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def get_roscas(
    db: Session,
    id: Optional[str] = None,
    code: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None
) -> list[dict]:
    query = db.query(
        Rosca,
        UserRosca.full_name.label("owner_name")
    ).outerjoin(
        UserRosca, Rosca.user_id == UserRosca.id
    )

    if id is not None:
        query = query.filter(Rosca.id == id)
    if code is not None:
        query = query.filter(Rosca.code == code)
    if user_id is not None:
        query = query.filter(Rosca.user_id == user_id)
    if status is not None:
        query = query.filter(Rosca.status == status)

    results = query.all()
    data = []
    for rosca, owner_name in results:
        rosca_dict = {c.name: getattr(rosca, c.name) for c in rosca.__table__.columns}
        rosca_dict["owner_name"] = owner_name
        data.append(rosca_dict)
    return data

def create_rosca(db: Session, obj_in: RoscaCreate):
    db_obj = Rosca(
        id=str(uuid.uuid4()),
        code=obj_in.code,
        user_id=obj_in.user_id,
        base_amount=obj_in.base_amount,
        min_bid_amount=obj_in.min_bid_amount,
        max_bid_amount=obj_in.max_bid_amount,
        total_parts=obj_in.total_parts,
        commission_fee=obj_in.commission_fee,
        start_date=obj_in.start_date,
        end_date=obj_in.end_date,
        payment_day=obj_in.payment_day,
        bidding_time=obj_in.bidding_time,
        period_type=obj_in.period_type,
        status=obj_in.status,
        note=obj_in.note
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_rosca(db: Session, rosca_id: str, obj_in: RoscaUpdate) -> Optional[Rosca]:
    db_obj = db.query(Rosca).filter(Rosca.id == rosca_id).first()
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

def delete_rosca(db: Session, rosca_id: str) -> Optional[Rosca]:
    db_obj = db.query(Rosca).filter(Rosca.id == rosca_id).first()
    if not db_obj:
        return None
    db_obj.status = "Deleted"
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_rosca_members(
    db: Session,
    id: Optional[str] = None,
    rosca_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None
) -> list[dict]:
    query = db.query(
        RoscaMember,
        UserRosca.full_name.label("player_name"),
        Rosca.code.label("rosca_code")
    ).outerjoin(
        UserRosca, RoscaMember.user_id == UserRosca.id
    ).outerjoin(
        Rosca, RoscaMember.rosca_id == Rosca.id
    )

    if id is not None:
        query = query.filter(RoscaMember.id == id)
    if rosca_id is not None:
        query = query.filter(RoscaMember.rosca_id == rosca_id)
    if user_id is not None:
        query = query.filter(RoscaMember.user_id == user_id)
    if status is not None:
        query = query.filter(RoscaMember.status == status)

    results = query.all()
    data = []
    for member, player_name, rosca_code in results:
        member_dict = {c.name: getattr(member, c.name) for c in member.__table__.columns}
        member_dict["player_name"] = player_name
        member_dict["rosca_code"] = rosca_code
        data.append(member_dict)
    return data

def create_rosca_member(db: Session, obj_in: RoscaMemberCreate):
    db_obj = RoscaMember(
        id=str(uuid.uuid4()),
        rosca_id=obj_in.rosca_id,
        user_id=obj_in.user_id,
        parts_count=obj_in.parts_count,
        total_contributed=obj_in.total_contributed,
        total_received=obj_in.total_received,
        total_profit=obj_in.total_profit,
        profit_rate=obj_in.profit_rate,
        status=obj_in.status,
        note=obj_in.note,
        telegram_group=obj_in.telegram_group
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_rosca_member(db: Session, member_id: str, obj_in: RoscaMemberUpdate) -> Optional[RoscaMember]:
    db_obj = db.query(RoscaMember).filter(RoscaMember.id == member_id).first()
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

def delete_rosca_member(db: Session, member_id: str) -> Optional[RoscaMember]:
    db_obj = db.query(RoscaMember).filter(RoscaMember.id == member_id).first()
    if not db_obj:
        return None
    db_obj.status = "Deleted"
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_rosca_contributions(
    db: Session,
    id: Optional[str] = None,
    rosca_id: Optional[str] = None,
    rosca_code: Optional[str] = None,
    member_id: Optional[str] = None,
    status: Optional[str] = None,
    flow_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list[dict]:
    query = db.query(
        RoscaContribution,
        UserRosca.full_name.label("player_name"),
        Rosca.code.label("rosca_code")
    ).outerjoin(
        RoscaMember, RoscaContribution.member_id == RoscaMember.id
    ).outerjoin(
        UserRosca, RoscaMember.user_id == UserRosca.id
    ).outerjoin(
        Rosca, RoscaContribution.rosca_id == Rosca.id
    )

    if id is not None:
        query = query.filter(RoscaContribution.id == id)
    if rosca_id is not None:
        query = query.filter(RoscaContribution.rosca_id == rosca_id)
    if rosca_code is not None:
        query = query.filter(Rosca.code.ilike(f"%{rosca_code}%"))
    if member_id is not None:
        query = query.filter(RoscaContribution.member_id == member_id)
    if status is not None:
        query = query.filter(RoscaContribution.status == status)
    if flow_type is not None:
        flow_lower = flow_type.lower()
        if flow_lower in ("pay", "contribute", "đóng"):
            query = query.filter(RoscaContribution.amount < 0)
        elif flow_lower in ("withdraw", "rút"):
            query = query.filter(RoscaContribution.amount > 0)
    if start_date is not None:
        query = query.filter(RoscaContribution.actual_payment_date >= start_date)
    if end_date is not None:
        query = query.filter(RoscaContribution.actual_payment_date <= end_date)

    results = query.all()
    data = []
    for contrib, player_name, rosca_code in results:
        contrib_dict = {c.name: getattr(contrib, c.name) for c in contrib.__table__.columns}
        contrib_dict["player_name"] = player_name
        contrib_dict["rosca_code"] = rosca_code
        data.append(contrib_dict)
    return data

def create_rosca_contribution(db: Session, obj_in: RoscaContributionCreate):
    db_obj = RoscaContribution(
        id=str(uuid.uuid4()),
        rosca_id=obj_in.rosca_id,
        round_id=obj_in.round_id,
        round_number=obj_in.round_number,
        member_id=obj_in.member_id,
        amount=obj_in.amount,
        actual_payment_date=obj_in.actual_payment_date,
        status=obj_in.status,
        note=obj_in.note
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_rosca_contribution(db: Session, contrib_id: str, obj_in: RoscaContributionUpdate) -> Optional[RoscaContribution]:
    db_obj = db.query(RoscaContribution).filter(RoscaContribution.id == contrib_id).first()
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

def delete_rosca_contribution(db: Session, contrib_id: str) -> Optional[RoscaContribution]:
    db_obj = db.query(RoscaContribution).filter(RoscaContribution.id == contrib_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj
