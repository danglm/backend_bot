from sqlalchemy.orm import Session
from app.models.credit import Credit, CreditInterest, CreditCustomer
from app.schemas.credit import CreditCreate, CreditInterestCreate, CreditCustomerCreate

def create_credit_customer(db: Session, obj_in: CreditCustomerCreate):
    db_obj = CreditCustomer(
        group_name=obj_in.group_name,
        customer_name=obj_in.customer_name,
        contact_info=obj_in.contact_info,
        total_credit_limit=obj_in.total_credit_limit,
        remaining_credit_limit=obj_in.remaining_credit_limit,
        total_principal_outstanding=obj_in.total_principal_outstanding
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
        credit_status=obj_in.credit_status
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

def get_credits(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Credit).offset(skip).limit(limit).all()

def get_credit_interests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(CreditInterest).offset(skip).limit(limit).all()
