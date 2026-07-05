from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.models.credit import Credit, CreditInterest, CreditCustomer
from app.schemas.credit import CreditCreate, CreditUpdate, CreditInterestCreate, CreditCustomerCreate, CreditCustomerUpdate
from uuid import UUID

def create_credit_customer(db: Session, obj_in: CreditCustomerCreate):
    db_obj = CreditCustomer(
        customer_id=obj_in.customer_id,
        group_name=obj_in.group_name,
        customer_name=obj_in.customer_name,
        contact_info=obj_in.contact_info,
        total_credit_limit=obj_in.total_credit_limit,
        remaining_credit_limit=obj_in.remaining_credit_limit,
        total_principal_outstanding=obj_in.total_principal_outstanding,
        classification=obj_in.classification
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def create_credit(db: Session, obj_in: CreditCreate):
    db_obj = Credit(
        customer_id=obj_in.customer_id,
        contract_id=obj_in.contract_id,
        loan_type=obj_in.loan_type,
        initial_principal=obj_in.initial_principal,
        start_date=obj_in.start_date,
        due_date=obj_in.due_date,
        interest_start_date=obj_in.interest_start_date,
        monthly_interest_rate=obj_in.monthly_interest_rate,
        monthly_interest_amount=obj_in.monthly_interest_amount,
        total_principal_paid=obj_in.total_principal_paid,
        remaining_principal=obj_in.remaining_principal,
        notes=obj_in.notes,
        send_message_arise=obj_in.send_message_arise,
        message_content=obj_in.message_content,
        credit_status=obj_in.credit_status,
        interest_debt=obj_in.interest_debt,
        last_interest_charged_date=obj_in.last_interest_charged_date,
        classification=obj_in.classification
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def create_credit_interest(db: Session, obj_in: CreditInterestCreate):
    db_obj = CreditInterest(
        contract_id=obj_in.contract_id,
        interest_payment_date=obj_in.interest_payment_date,
        payment_time=obj_in.payment_time,
        interest_amount=obj_in.interest_amount
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_credit_interests_detailed(
    db: Session,
    contract_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> list[dict]:
    query = db.query(
        CreditInterest,
        Credit.loan_type,
        Credit.initial_principal,
        Credit.remaining_principal,
        Credit.monthly_interest_rate,
        Credit.credit_status,
        Credit.start_date.label("contract_start_date"),
        Credit.due_date,
        CreditCustomer.customer_id.label("customer_code"),
        CreditCustomer.customer_name,
        CreditCustomer.group_name,
        CreditCustomer.contact_info
    ).outerjoin(
        Credit, CreditInterest.contract_id == Credit.contract_id
    ).outerjoin(
        CreditCustomer, Credit.customer_id == CreditCustomer.id
    )

    if contract_id is not None:
        query = query.filter(CreditInterest.contract_id == contract_id)
    if start_date is not None:
        query = query.filter(CreditInterest.interest_payment_date >= start_date)
    if end_date is not None:
        query = query.filter(CreditInterest.interest_payment_date <= end_date)

    results = query.all()

    data = []
    for (ci, loan_type, initial_principal, remaining_principal, monthly_interest_rate,
         credit_status, contract_start_date, due_date,
         customer_code, customer_name, group_name, contact_info) in results:
        data.append({
            "id": ci.id,
            "contract_id": ci.contract_id,
            "interest_payment_date": ci.interest_payment_date,
            "payment_time": ci.payment_time,
            "interest_amount": ci.interest_amount,
            "loan_type": loan_type,
            "initial_principal": initial_principal,
            "remaining_principal": remaining_principal,
            "monthly_interest_rate": monthly_interest_rate,
            "credit_status": credit_status,
            "start_date": contract_start_date,
            "due_date": due_date,
            "customer_code": customer_code,
            "customer_name": customer_name,
            "group_name": group_name,
            "contact_info": contact_info,
        })
    return data


def get_credits(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Credit).offset(skip).limit(limit).all()


def get_credits_detailed(
    db: Session,
    status: Optional[str] = None,
    loan_type: Optional[str] = None,
    contract_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> list[dict]:
    query = db.query(
        Credit,
        CreditCustomer.customer_id.label("customer_code"),
        CreditCustomer.customer_name,
        CreditCustomer.group_name,
        CreditCustomer.contact_info
    ).outerjoin(
        CreditCustomer, Credit.customer_id == CreditCustomer.id
    )

    if status is not None:
        query = query.filter(Credit.credit_status == status)
    if loan_type is not None:
        query = query.filter(Credit.loan_type == loan_type)
    if contract_id is not None:
        query = query.filter(Credit.contract_id == contract_id)
    if start_date is not None:
        query = query.filter(Credit.start_date >= start_date)
    if end_date is not None:
        query = query.filter(Credit.start_date <= end_date)

    results = query.all()

    data = []
    for c, customer_code, customer_name, group_name, contact_info in results:
        data.append({
            "id": c.id,
            "customer_id": c.customer_id,
            "customer_code": customer_code,
            "customer_name": customer_name,
            "group_name": group_name,
            "contact_info": contact_info,
            "contract_id": c.contract_id,
            "loan_type": c.loan_type,
            "initial_principal": c.initial_principal,
            "start_date": c.start_date,
            "due_date": c.due_date,
            "interest_start_date": c.interest_start_date,
            "monthly_interest_rate": c.monthly_interest_rate,
            "monthly_interest_amount": c.monthly_interest_amount,
            "total_principal_paid": c.total_principal_paid,
            "remaining_principal": c.remaining_principal,
            "notes": c.notes,
            "send_message_arise": c.send_message_arise,
            "message_content": c.message_content,
            "credit_status": c.credit_status,
            "interest_debt": c.interest_debt,
            "last_interest_charged_date": c.last_interest_charged_date,
            "classification": c.classification
        })
    return data

def get_credit_interests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(CreditInterest).offset(skip).limit(limit).all()


def get_all_credit_customers(db: Session, customer_id: Optional[str] = None):
    query = db.query(CreditCustomer)
    if customer_id is not None:
        query = query.filter(CreditCustomer.customer_id == customer_id)
    return query.all()


def update_credit_customer(db: Session, customer_uuid: UUID, obj_in: CreditCustomerUpdate) -> Optional[CreditCustomer]:
    db_obj = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
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


def delete_credit_customer(db: Session, customer_uuid: UUID) -> Optional[CreditCustomer]:
    db_obj = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def update_credit(db: Session, credit_uuid: UUID, obj_in: CreditUpdate) -> Optional[Credit]:
    db_obj = db.query(Credit).filter(Credit.id == credit_uuid).first()
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


def delete_credit(db: Session, credit_uuid: UUID) -> Optional[Credit]:
    db_obj = db.query(Credit).filter(Credit.id == credit_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def delete_credit_interest(db: Session, interest_uuid: UUID) -> Optional[CreditInterest]:
    db_obj = db.query(CreditInterest).filter(CreditInterest.id == interest_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def get_distinct_classifications(db: Session) -> list[str]:
    cust_classifications = db.query(CreditCustomer.classification).distinct().all()
    credit_classifications = db.query(Credit.classification).distinct().all()

    merged = set()
    for row in cust_classifications:
        if row[0]:
            merged.add(row[0])
    for row in credit_classifications:
        if row[0]:
            merged.add(row[0])

    return sorted(list(merged))

