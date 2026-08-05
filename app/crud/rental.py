from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import date
from app.models.rental import RealEstate, RentalCustomer, Rental, RentalPayment
from app.schemas.rental import RealEstateCreate, RealEstateUpdate, RentalCustomerCreate, RentalCustomerUpdate, RentalCreate, RentalUpdate, RentalPaymentCreate, RentalPaymentUpdate
# Helper khớp khách hàng với nhóm member: ưu tiên chat_id, không có mới đối chiếu
# group_name (bỏ qua hoa/thường). Dùng chung với module Credit vì cùng cấu trúc.
from app.crud.credit import match_member_link  # noqa: F401


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


def get_all_real_estates(db: Session, status: Optional[str] = None):
    query = db.query(RealEstate)
    if status is not None:
        query = query.filter(RealEstate.status == status)
    return query.all()



def update_real_estate(db: Session, real_estate_uuid: UUID, obj_in: RealEstateUpdate) -> Optional[RealEstate]:
    db_obj = db.query(RealEstate).filter(RealEstate.id == real_estate_uuid).first()
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


def delete_real_estate(db: Session, real_estate_uuid: UUID) -> Optional[RealEstate]:
    db_obj = db.query(RealEstate).filter(RealEstate.id == real_estate_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def get_real_estate_by_id(db: Session, real_estate_id: str):
    return db.query(RealEstate).filter(RealEstate.real_estate_id == real_estate_id).first()


def create_rental_customer(db: Session, obj_in: RentalCustomerCreate):
    db_obj = RentalCustomer(
        customer_id=obj_in.customer_id,
        group_name=obj_in.group_name,
        customer_name=obj_in.customer_name,
        contact_info=obj_in.contact_info,
        number_phone=obj_in.number_phone,
        chat_id=obj_in.chat_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_rental_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(RentalCustomer).offset(skip).limit(limit).all()


def get_all_rental_customers(db: Session, customer_id: Optional[str] = None, chat_id: Optional[str] = None):
    query = db.query(RentalCustomer)
    if customer_id is not None:
        query = query.filter(RentalCustomer.customer_id == customer_id)
    if chat_id is not None:
        query = query.filter(RentalCustomer.chat_id == str(chat_id))
    return query.all()


def update_rental_customer(db: Session, customer_uuid: UUID, obj_in: RentalCustomerUpdate) -> Optional[RentalCustomer]:
    db_obj = db.query(RentalCustomer).filter(RentalCustomer.id == customer_uuid).first()
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


def delete_rental_customer(db: Session, customer_uuid: UUID) -> Optional[RentalCustomer]:
    db_obj = db.query(RentalCustomer).filter(RentalCustomer.id == customer_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


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
        status=obj_in.status,
        notes=obj_in.notes
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_rentals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Rental).offset(skip).limit(limit).all()


def update_rental(db: Session, rental_uuid: UUID, obj_in: RentalUpdate) -> Optional[Rental]:
    db_obj = db.query(Rental).filter(Rental.id == rental_uuid).first()
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


def delete_rental(db: Session, rental_uuid: UUID) -> Optional[Rental]:
    db_obj = db.query(Rental).filter(Rental.id == rental_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def get_rentals_detailed(db: Session, status: Optional[str] = None) -> list[dict]:
    query = db.query(
        Rental,
        RentalCustomer.customer_id.label("customer_code"),
        RentalCustomer.customer_name,
        RentalCustomer.group_name,
        RentalCustomer.contact_info,
        RentalCustomer.number_phone,
        RentalCustomer.chat_id
    ).outerjoin(
        RentalCustomer, Rental.customer_id == RentalCustomer.id
    )

    if status is not None:
        query = query.filter(Rental.status == status)

    results = query.all()

    data = []
    for r, customer_code, customer_name, group_name, contact_info, number_phone, chat_id in results:
        data.append({
            "id": r.id,
            "customer_id": r.customer_id,
            "customer_code": customer_code,
            "customer_name": customer_name,
            "group_name": group_name,
            "contact_info": contact_info,
            "number_phone": number_phone,
            "chat_id": chat_id,
            "contract_id": r.contract_id,
            "real_estate_id": r.real_estate_id,
            "type_contract": r.type_contract,
            "start_rental": r.start_rental,
            "end_rental": r.end_rental,
            "deposit": r.deposit,
            "monthly_rental": r.monthly_rental,
            "rental_debt": r.rental_debt,
            "status": r.status,
            "notes": r.notes
        })
    return data



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


def get_rental_payments_detailed(
    db: Session, 
    contract_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None
) -> list[dict]:
    query = db.query(
        RentalPayment,
        Rental.real_estate_id,
        Rental.type_contract,
        Rental.start_rental,
        Rental.end_rental,
        Rental.deposit,
        Rental.monthly_rental,
        Rental.rental_debt,
        Rental.status.label("contract_status"),
        RentalCustomer.customer_id.label("customer_code"),
        RentalCustomer.customer_name,
        RentalCustomer.group_name,
        RentalCustomer.contact_info,
        RentalCustomer.number_phone,
        RentalCustomer.chat_id
    ).outerjoin(
        Rental, RentalPayment.contract_id == Rental.contract_id
    ).outerjoin(
        RentalCustomer, Rental.customer_id == RentalCustomer.id
    )
    
    if contract_id is not None:
        query = query.filter(RentalPayment.contract_id == contract_id)
    if start_date is not None:
        query = query.filter(RentalPayment.payment_date >= start_date)
    if end_date is not None:
        query = query.filter(RentalPayment.payment_date <= end_date)
    if status is not None:
        query = query.filter(Rental.status == status)
        
    results = query.all()
    
    data = []
    for (
        rp, real_estate_id, type_contract, start_rental, end_rental, deposit, monthly_rental,
        rental_debt, contract_status, customer_code, customer_name, group_name, contact_info, number_phone,
        chat_id
    ) in results:
        data.append({
            "id": rp.id,
            "contract_id": rp.contract_id,
            "payment_date": rp.payment_date,
            "payment_time": rp.payment_time,
            "payment_amount": rp.payment_amount,
            
            # Contract details
            "real_estate_id": real_estate_id,
            "type_contract": type_contract,
            "start_rental": start_rental,
            "end_rental": end_rental,
            "deposit": deposit,
            "monthly_rental": monthly_rental,
            "rental_debt": rental_debt,
            "status": contract_status,
            
            # Customer details
            "customer_code": customer_code,
            "customer_name": customer_name,
            "group_name": group_name,
            "contact_info": contact_info,
            "number_phone": number_phone,
            "chat_id": chat_id
        })
    return data


def update_rental_payment(db: Session, payment_uuid: UUID, obj_in: RentalPaymentUpdate) -> Optional[RentalPayment]:
    db_obj = db.query(RentalPayment).filter(RentalPayment.id == payment_uuid).first()
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


def delete_rental_payment(db: Session, payment_uuid: UUID) -> Optional[RentalPayment]:
    db_obj = db.query(RentalPayment).filter(RentalPayment.id == payment_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj
