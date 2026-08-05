from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_permission
from app.schemas import rental as schemas_rental
from app.crud import rental as crud_rental
from app.models.employee import Credential
from app.models.rental import RealEstate, RentalCustomer, Rental, RentalPayment
from bot.utils.logger import LogInfo
from uuid import UUID
from typing import Optional
from datetime import datetime, date
import calendar

router = APIRouter()


@router.get("/get-real-estates", response_model=list[schemas_rental.RealEstate])
async def api_get_all_real_estates(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Lấy toàn bộ danh sách Bất Động Sản.
    """
    LogInfo(f"[Rental API] Received get-real-estates request. Status filter: {status}")
    try:
        real_estates = crud_rental.get_all_real_estates(db, status=status)
        LogInfo(f"[Rental API] Found {len(real_estates)} real estates.")
        return real_estates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/add-real-estates", response_model=list[schemas_rental.RealEstate])
async def api_add_real_estates(
    real_estates_in: list[schemas_rental.RealEstateCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Thêm mới danh sách Bất Động Sản (bulk).
    """
    LogInfo(f"[Rental API] Received add-real-estates request. Total real estates to add: {len(real_estates_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [r.real_estate_id for r in real_estates_in if r.real_estate_id]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate real_estate_id found in the request input."
            )
            
        # Check if any real_estate_id already exists in the database
        existing_real_estates = db.query(RealEstate).filter(RealEstate.real_estate_id.in_(input_ids)).all()
        if existing_real_estates:
            existing_ids = [r.real_estate_id for r in existing_real_estates]
            raise HTTPException(
                status_code=400,
                detail=f"Real estates with IDs {existing_ids} already exist in the database."
            )
            
        created_real_estates = []
        for re_in in real_estates_in:
            new_re = crud_rental.create_real_estate(db, obj_in=re_in)
            created_real_estates.append(new_re)
            
        LogInfo(f"[Rental API] Successfully added {len(created_real_estates)} real estates.")
        return created_real_estates
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in add-real-estates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-real-estates", response_model=list[schemas_rental.RealEstate])
async def api_update_real_estates(
    real_estates_in: list[schemas_rental.RealEstateUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Cập nhật danh sách Bất Động Sản (bulk).
    """
    LogInfo(f"[Rental API] Received update-real-estates request. Total real estates to update: {len(real_estates_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [r.id for r in real_estates_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all real estate IDs exist in the database
        existing_real_estates = db.query(RealEstate).filter(RealEstate.id.in_(input_ids)).all()
        existing_ids = {r.id for r in existing_real_estates}
        
        missing_ids = [rid for rid in input_ids if rid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Real estates with IDs {missing_ids} not found in the database."
            )
            
        updated_real_estates = []
        for re_in in real_estates_in:
            updated_re = crud_rental.update_real_estate(db, real_estate_uuid=re_in.id, obj_in=re_in)
            if updated_re:
                updated_real_estates.append(updated_re)
            
        LogInfo(f"[Rental API] Successfully updated {len(updated_real_estates)} real estates.")
        return updated_real_estates
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in update-real-estates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-real-estates", response_model=list[schemas_rental.RealEstate])
async def api_delete_real_estates(
    real_estate_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Xóa danh sách Bất Động Sản (bulk).
    """
    LogInfo(f"[Rental API] Received delete-real-estates request. Total real estates to delete: {len(real_estate_ids)}")
    try:
        # Check for duplicates in the input list itself
        if len(real_estate_ids) != len(set(real_estate_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all real estate IDs exist in the database
        existing_real_estates = db.query(RealEstate).filter(RealEstate.id.in_(real_estate_ids)).all()
        existing_ids = {r.id for r in existing_real_estates}
        
        missing_ids = [rid for rid in real_estate_ids if rid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Real estates with IDs {missing_ids} not found in the database."
            )
            
        deleted_real_estates = []
        for re_uuid in real_estate_ids:
            deleted_re = crud_rental.delete_real_estate(db, real_estate_uuid=re_uuid)
            if deleted_re:
                deleted_real_estates.append(deleted_re)
            
        LogInfo(f"[Rental API] Successfully deleted {len(deleted_real_estates)} real estates.")
        return deleted_real_estates
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in delete-real-estates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-rentals", response_model=list[schemas_rental.RentalResponse])
async def api_get_rentals_detailed(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Lấy danh sách các hợp đồng thuê kèm thông tin chi tiết khách hàng.
    """
    LogInfo(f"[Rental API] Received get-rentals request. Status filter: {status}")
    try:
        rentals = crud_rental.get_rentals_detailed(db, status=status)
        LogInfo(f"[Rental API] Found {len(rentals)} rental records.")
        return rentals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-rentals", response_model=list[schemas_rental.Rental])
async def api_add_rentals(
    rentals_in: list[schemas_rental.RentalCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Thêm mới danh sách hợp đồng thuê (bulk).
    """
    LogInfo(f"[Rental API] Received add-rentals request. Total rentals to add: {len(rentals_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [r.contract_id for r in rentals_in if r.contract_id]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate contract_id found in the request input."
            )
            
        # Check if any contract_id already exists in the database
        existing_rentals = db.query(Rental).filter(Rental.contract_id.in_(input_ids)).all()
        if existing_rentals:
            existing_ids = [r.contract_id for r in existing_rentals]
            raise HTTPException(
                status_code=400,
                detail=f"Rental contracts with IDs {existing_ids} already exist in the database."
            )
            
        created_rentals = []
        for rent_in in rentals_in:
            new_rent = crud_rental.create_rental(db, obj_in=rent_in)
            created_rentals.append(new_rent)
            
        LogInfo(f"[Rental API] Successfully added {len(created_rentals)} rental contracts.")
        return created_rentals
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in add-rentals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-rentals", response_model=list[schemas_rental.Rental])
async def api_update_rentals(
    rentals_in: list[schemas_rental.RentalUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Cập nhật danh sách hợp đồng thuê (bulk).
    """
    LogInfo(f"[Rental API] Received update-rentals request. Total rentals to update: {len(rentals_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [r.id for r in rentals_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all rental IDs exist in the database
        existing_rentals = db.query(Rental).filter(Rental.id.in_(input_ids)).all()
        existing_ids = {r.id for r in existing_rentals}
        
        missing_ids = [rid for rid in input_ids if rid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rental contracts with IDs {missing_ids} not found in the database."
            )
            
        updated_rentals = []
        for rent_in in rentals_in:
            updated_rent = crud_rental.update_rental(db, rental_uuid=rent_in.id, obj_in=rent_in)
            if updated_rent:
                updated_rentals.append(updated_rent)
            
        LogInfo(f"[Rental API] Successfully updated {len(updated_rentals)} rental contracts.")
        return updated_rentals
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in update-rentals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-rentals", response_model=list[schemas_rental.Rental])
async def api_delete_rentals(
    rental_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Xóa danh sách hợp đồng thuê (bulk).
    """
    LogInfo(f"[Rental API] Received delete-rentals request. Total rentals to delete: {len(rental_ids)}")
    try:
        # Check for duplicates in the input list itself
        if len(rental_ids) != len(set(rental_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all rental IDs exist in the database
        existing_rentals = db.query(Rental).filter(Rental.id.in_(rental_ids)).all()
        existing_ids = {r.id for r in existing_rentals}
        
        missing_ids = [rid for rid in rental_ids if rid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rental contracts with IDs {missing_ids} not found in the database."
            )
            
        deleted_rentals = []
        for rent_uuid in rental_ids:
            deleted_rent = crud_rental.delete_rental(db, rental_uuid=rent_uuid)
            if deleted_rent:
                deleted_rentals.append(deleted_rent)
            
        LogInfo(f"[Rental API] Successfully deleted {len(deleted_rentals)} rental contracts.")
        return deleted_rentals
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in delete-rentals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-rental-customers", response_model=list[schemas_rental.RentalCustomer])
async def api_add_rental_customers(
    customers_in: list[schemas_rental.RentalCustomerCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Thêm mới danh sách khách hàng thuê (bulk).
    """
    LogInfo(f"[Rental API] Received add-rental-customers request. Total customers to add: {len(customers_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [c.customer_id for c in customers_in if c.customer_id]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate customer_id found in the request input."
            )
            
        # Check if any customer_id already exists in the database
        existing_customers = db.query(RentalCustomer).filter(RentalCustomer.customer_id.in_(input_ids)).all()
        if existing_customers:
            existing_ids = [c.customer_id for c in existing_customers]
            raise HTTPException(
                status_code=400,
                detail=f"Rental customers with IDs {existing_ids} already exist in the database."
            )
            
        created_customers = []
        for cust_in in customers_in:
            new_cust = crud_rental.create_rental_customer(db, obj_in=cust_in)
            created_customers.append(new_cust)
            
        LogInfo(f"[Rental API] Successfully added {len(created_customers)} rental customers.")
        return created_customers
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in add-rental-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-rental-customers", response_model=list[schemas_rental.RentalCustomer])
async def api_get_rental_customers(
    customer_id: Optional[str] = None,
    chat_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Lấy danh sách các khách hàng thuê.
    """
    LogInfo(f"[Rental API] Received get-rental-customers request. Customer ID filter: {customer_id}, Chat ID filter: {chat_id}")
    try:
        customers = crud_rental.get_all_rental_customers(db, customer_id=customer_id, chat_id=chat_id)
        LogInfo(f"[Rental API] Found {len(customers)} rental customers.")
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-rental-customers", response_model=list[schemas_rental.RentalCustomer])
async def api_update_rental_customers(
    customers_in: list[schemas_rental.RentalCustomerUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Cập nhật danh sách khách hàng thuê (bulk).
    """
    LogInfo(f"[Rental API] Received update-rental-customers request. Total customers to update: {len(customers_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [c.id for c in customers_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all customer IDs exist in the database
        existing_customers = db.query(RentalCustomer).filter(RentalCustomer.id.in_(input_ids)).all()
        existing_ids = {c.id for c in existing_customers}
        
        missing_ids = [cid for cid in input_ids if cid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rental customers with IDs {missing_ids} not found in the database."
            )
            
        updated_customers = []
        for cust_in in customers_in:
            updated_cust = crud_rental.update_rental_customer(db, customer_uuid=cust_in.id, obj_in=cust_in)
            if updated_cust:
                updated_customers.append(updated_cust)
            
        LogInfo(f"[Rental API] Successfully updated {len(updated_customers)} rental customers.")
        return updated_customers
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in update-rental-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-rental-customers", response_model=list[schemas_rental.RentalCustomer])
async def api_delete_rental_customers(
    customer_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Xóa danh sách khách hàng thuê (bulk).
    """
    LogInfo(f"[Rental API] Received delete-rental-customers request. Total customers to delete: {len(customer_ids)}")
    try:
        # Check for duplicates in the input list itself
        if len(customer_ids) != len(set(customer_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all customer IDs exist in the database
        existing_customers = db.query(RentalCustomer).filter(RentalCustomer.id.in_(customer_ids)).all()
        existing_ids = {c.id for c in existing_customers}
        
        missing_ids = [cid for cid in customer_ids if cid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rental customers with IDs {missing_ids} not found in the database."
            )
            
        deleted_customers = []
        for cust_uuid in customer_ids:
            deleted_cust = crud_rental.delete_rental_customer(db, customer_uuid=cust_uuid)
            if deleted_cust:
                deleted_customers.append(deleted_cust)
            
        LogInfo(f"[Rental API] Successfully deleted {len(deleted_customers)} rental customers.")
        return deleted_customers
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in delete-rental-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-rental-payments", response_model=list[schemas_rental.RentalPayment])
async def api_add_rental_payments(
    payments_in: list[schemas_rental.RentalPaymentCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Thêm mới danh sách khoản thanh toán (bulk).
    """
    LogInfo(f"[Rental API] Received add-rental-payments request. Total payments to add: {len(payments_in)}")
    try:
        # Check if all contract_ids exist in the database
        input_contract_ids = [p.contract_id for p in payments_in]
        existing_rentals = db.query(Rental).filter(Rental.contract_id.in_(input_contract_ids)).all()
        existing_contract_ids = {r.contract_id for r in existing_rentals}
        
        missing_contracts = [cid for cid in input_contract_ids if cid not in existing_contract_ids]
        if missing_contracts:
            raise HTTPException(
                status_code=400,
                detail=f"Rental contracts with IDs {missing_contracts} do not exist in the database."
            )
            
        created_payments = []
        for pay_in in payments_in:
            new_pay = crud_rental.create_rental_payment(db, obj_in=pay_in)
            created_payments.append(new_pay)
            
            # Subtract payment_amount from corresponding contract's rental_debt
            if pay_in.payment_amount:
                contract = db.query(Rental).filter(Rental.contract_id == pay_in.contract_id).first()
                if contract:
                    contract.rental_debt = (contract.rental_debt or 0.0) - pay_in.payment_amount
                    db.commit()
                    db.refresh(contract)
            
        LogInfo(f"[Rental API] Successfully added {len(created_payments)} rental payments and updated rental debts.")
        return created_payments
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in add-rental-payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-rental-payments", response_model=list[schemas_rental.RentalPayment])
async def api_update_rental_payments(
    payments_in: list[schemas_rental.RentalPaymentUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Cập nhật danh sách các khoản thanh toán (bulk) và điều chỉnh công nợ hợp đồng.
    """
    LogInfo(f"[Rental API] Received update-rental-payments request. Total payments to update: {len(payments_in)}")
    try:
        # Check for duplicate IDs in the input list itself
        input_ids = [p.id for p in payments_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Verify that all payment records exist in DB
        existing_payments = db.query(RentalPayment).filter(RentalPayment.id.in_(input_ids)).all()
        existing_ids = {p.id for p in existing_payments}
        
        missing_ids = [pid for pid in input_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rental payments with IDs {missing_ids} not found in the database."
            )
            
        # Verify that if contract_id is updated, it must exist in DB
        new_contract_ids = [p.contract_id for p in payments_in if p.contract_id]
        if new_contract_ids:
            existing_rentals = db.query(Rental).filter(Rental.contract_id.in_(new_contract_ids)).all()
            existing_contract_ids = {r.contract_id for r in existing_rentals}
            missing_contracts = [cid for cid in new_contract_ids if cid not in existing_contract_ids]
            if missing_contracts:
                raise HTTPException(
                    status_code=400,
                    detail=f"Rental contracts with IDs {missing_contracts} do not exist in the database."
                )

        updated_payments = []
        for pay_in in payments_in:
            # 1. Fetch old payment attributes
            old_payment = db.query(RentalPayment).filter(RentalPayment.id == pay_in.id).first()
            old_amount = old_payment.payment_amount or 0.0
            old_contract_id = old_payment.contract_id
            
            # 2. Update payment record
            updated_pay = crud_rental.update_rental_payment(db, payment_uuid=pay_in.id, obj_in=pay_in)
            if not updated_pay:
                continue
            updated_payments.append(updated_pay)
            
            # 3. Recalculate and update rental contract debt
            new_amount = updated_pay.payment_amount or 0.0
            new_contract_id = updated_pay.contract_id
            
            if old_contract_id == new_contract_id:
                # Same contract
                diff = new_amount - old_amount
                if diff != 0:
                    contract = db.query(Rental).filter(Rental.contract_id == old_contract_id).first()
                    if contract:
                        contract.rental_debt = (contract.rental_debt or 0.0) - diff
                        db.commit()
                        db.refresh(contract)
            else:
                # Contract changed
                # Restore old amount to old contract
                if old_amount != 0:
                    old_contract = db.query(Rental).filter(Rental.contract_id == old_contract_id).first()
                    if old_contract:
                        old_contract.rental_debt = (old_contract.rental_debt or 0.0) + old_amount
                        db.commit()
                        db.refresh(old_contract)
                # Subtract new amount from new contract
                if new_amount != 0:
                    new_contract = db.query(Rental).filter(Rental.contract_id == new_contract_id).first()
                    if new_contract:
                        new_contract.rental_debt = (new_contract.rental_debt or 0.0) - new_amount
                        db.commit()
                        db.refresh(new_contract)
                        
        LogInfo(f"[Rental API] Successfully updated {len(updated_payments)} rental payments.")
        return updated_payments
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in update-rental-payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-rental-payments", response_model=list[schemas_rental.RentalPayment])
async def api_delete_rental_payments(
    payment_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Xóa danh sách khoản thanh toán (bulk) và hoàn trả công nợ hợp đồng.
    """
    LogInfo(f"[Rental API] Received delete-rental-payments request. Total payments to delete: {len(payment_ids)}")
    try:
        # Check for duplicates in the input list itself
        if len(payment_ids) != len(set(payment_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Verify that all payment records exist in DB
        existing_payments = db.query(RentalPayment).filter(RentalPayment.id.in_(payment_ids)).all()
        existing_ids = {p.id for p in existing_payments}
        
        missing_ids = [pid for pid in payment_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Rental payments with IDs {missing_ids} not found in the database."
            )
            
        deleted_payments = []
        for pay_uuid in payment_ids:
            # 1. Fetch payment attributes before deleting
            payment = db.query(RentalPayment).filter(RentalPayment.id == pay_uuid).first()
            payment_amount = payment.payment_amount or 0.0
            payment_contract_id = payment.contract_id
            
            # 2. Delete payment record
            deleted_pay = crud_rental.delete_rental_payment(db, payment_uuid=pay_uuid)
            if not deleted_pay:
                continue
            deleted_payments.append(deleted_pay)
            
            # 3. Restore payment amount back to contract's rental_debt
            if payment_amount != 0:
                contract = db.query(Rental).filter(Rental.contract_id == payment_contract_id).first()
                if contract:
                    contract.rental_debt = (contract.rental_debt or 0.0) + payment_amount
                    db.commit()
                    db.refresh(contract)
                    
        LogInfo(f"[Rental API] Successfully deleted {len(deleted_payments)} rental payments and restored rental debts.")
        return deleted_payments
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in delete-rental-payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-rental-payments", response_model=list[schemas_rental.RentalPaymentResponse])
async def api_get_rental_payments(
    contract_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("rental"))
):
    """
    Lấy danh sách chi tiết các khoản thanh toán tiền thuê kèm thông tin hợp đồng và khách hàng.
    """
    LogInfo(f"[Rental API] Received get-rental-payments request. Contract ID: {contract_id}, start_date: {start_date}, end_date: {end_date}, status: {status}")
    
    parsed_start_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%m/%Y").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Expected MM/YYYY."
            )
            
    parsed_end_date = None
    if end_date:
        try:
            first_day = datetime.strptime(end_date, "%m/%Y").date()
            last_day = calendar.monthrange(first_day.year, first_day.month)[1]
            parsed_end_date = date(first_day.year, first_day.month, last_day)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Expected MM/YYYY."
            )
            
    try:
        payments = crud_rental.get_rental_payments_detailed(
            db, 
            contract_id=contract_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            status=status
        )
        LogInfo(f"[Rental API] Found {len(payments)} rental payments.")
        return payments
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Rental API] Error in get-rental-payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))





