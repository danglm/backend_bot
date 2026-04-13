from sqlalchemy.orm import Session
from app.models.rental import RealEstate, RentalCustomer, Rental, RentalPayment
from app.schemas.rental import RealEstateCreate, RentalCustomerCreate, RentalCreate, RentalPaymentCreate


def create_real_estate(db: Session, obj_in: RealEstateCreate):
    db_obj = RealEstate(
        real_estate_id=obj_in.real_estate_id,
        address=obj_in.address,
        start_buy=obj_in.start_buy,
        end_buy=obj_in.end_buy,
        total_cost=obj_in.total_cost,
        real_estate_cost=obj_in.real_estate_cost,
        construction_cost=obj_in.construction_cost,
        furniture_cost=obj_in.furniture_cost,
        sale_cost=obj_in.sale_cost,
        contributed_cost=obj_in.contributed_cost,
        monthly_interest_rate=obj_in.monthly_interest_rate,
        mining_profit=obj_in.mining_profit,
        rental_profit=obj_in.rental_profit,
        start_sale=obj_in.start_sale,
        end_sale=obj_in.end_sale,
        profit_after_tax=obj_in.profit_after_tax,
        profit_after_sale=obj_in.profit_after_sale,
        status=obj_in.status,
        note=obj_in.note,
        current_estimated=obj_in.current_estimated
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_real_estates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(RealEstate).offset(skip).limit(limit).all()


def get_real_estate_by_id(db: Session, real_estate_id: str):
    return db.query(RealEstate).filter(RealEstate.real_estate_id == real_estate_id).first()


def create_rental_customer(db: Session, obj_in: RentalCustomerCreate):
    db_obj = RentalCustomer(
        group_name=obj_in.group_name,
        customer_name=obj_in.customer_name,
        contact_info=obj_in.contact_info,
        number_phone=obj_in.number_phone
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_rental_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(RentalCustomer).offset(skip).limit(limit).all()


def create_rental(db: Session, obj_in: RentalCreate):
    db_obj = Rental(
        customer_id=obj_in.customer_id,
        contract_id=obj_in.contract_id,
        real_estate_id=obj_in.real_estate_id,
        type_contract=obj_in.type_contract,
        start_rental=obj_in.start_rental,
        end_rental=obj_in.end_rental,
        deposit=obj_in.deposit,
        monthly_rental=obj_in.monthly_rental,
        rental_debt=obj_in.rental_debt,
        status=obj_in.status
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_rentals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Rental).offset(skip).limit(limit).all()


def create_rental_payment(db: Session, obj_in: RentalPaymentCreate):
    db_obj = RentalPayment(
        contract_id=obj_in.contract_id,
        payment_date=obj_in.payment_date,
        payment_time=obj_in.payment_time,
        payment_amount=obj_in.payment_amount
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_rental_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(RentalPayment).offset(skip).limit(limit).all()
