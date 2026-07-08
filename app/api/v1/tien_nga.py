from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_permission
from app.schemas.customer import CustomerResponse, CustomerCreate, CustomerUpdate
from app.schemas.collection_point import CollectionPointResponse
from app.schemas import DailyPurchaseResponse, DailyPurchaseCreate, DailyPurchaseUpdate, MaterialPurchaseResponse, MaterialPurchaseCreate, InventoryResponse, InventoryCreate, InventoryUpdate, PartnerResponse, PartnerCreate, PartnerUpdate, PartnerBusinessResponse, PartnerBusinessCreate, PartnerBusinessUpdate, InvestmentResponse, InvestmentCreate, InvestmentUpdate, DailyPaymentResponse, DailyPaymentCreate, InventoryExportResponse, InventoryExportCreate, ProductTransactionResponse, ProductTransactionCreate
from app.schemas.process_debt import ProcessDebtRequest, ProcessDebtResponse, DailyPurchaseAllocation
from app.schemas.loss_control import ProcessLossControlRequest, LossControlItem, ProcessLossControlResponse
from app.crud.customer import (
    get_customers_with_collection_name,
    get_collection_points_by_ingredient,
    create_customer,
    update_customer,
    delete_customer,
    get_daily_purchases_detailed,
    create_daily_purchase,
    update_daily_purchase,
    delete_daily_purchase,
    get_material_purchases_detailed,
    create_material_purchase,
    delete_material_purchase,
    get_inventories,
    get_inventories_by_material_name,
    create_inventory,
    update_inventory,
    delete_inventory,
    get_inventory_exports,
    get_product_transactions,
    create_product_transaction,
    delete_product_transaction,
    create_inventory_export,
    delete_inventory_export,
    get_partners,
    create_partner,
    update_partner,
    delete_partner,
    get_partner_businesses_detailed,
    create_partner_business,
    update_partner_business,
    delete_partner_business,
    get_investments,
    create_investment,
    update_investment,
    delete_investment,
    get_daily_payments,
    create_daily_payment,
    delete_daily_payment,
    update_investment_financials,
)
from app.models.employee import Credential
from app.models.business import Customers, CollectionPoint, DailyPurchases, Partners, PartnerBusinesses, Investment, DailyPayment, LossControls, Shareholder
from app.models.inventory import Inventory, MaterialPurchase, InventoryExport, ProductTransaction
from bot.utils.logger import LogInfo
from app.schemas.shareholder import ShareholderCreate, ShareholderUpdate, ShareholderResponse
import app.crud.shareholder as crud_shareholder
from typing import Optional, List
from datetime import date
from uuid import UUID

router = APIRouter()

@router.get("/get-customers", response_model=List[CustomerResponse])
def get_customers(
    ingredient: Optional[str] = None, 
    collection_point_id: Optional[str] = None,
    hoursehold_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-customers request. Raw ingredient: {ingredient}, collection_point_id: {collection_point_id}, hoursehold_id: {hoursehold_id}")
    try:
        cp_ids = None
        if collection_point_id:
            cp_ids = [cp.strip() for cp in collection_point_id.split(",") if cp.strip()]

        customers = get_customers_with_collection_name(
            db, 
            ingredient=ingredient, 
            collection_point_id=cp_ids,
            hoursehold_id=hoursehold_id
        )
        LogInfo(f"[TienNga API] Found {len(customers)} customers.")
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-collection-points", response_model=List[CollectionPointResponse])
def get_collection_points(
    ingredient: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-collection-points request. Raw ingredient: {ingredient}")
    try:
        collection_points = get_collection_points_by_ingredient(db, ingredient=ingredient)
        LogInfo(f"[TienNga API] Found {len(collection_points)} collection points.")
        return collection_points
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-customers", response_model=List[CustomerResponse])
def add_customers(
    customers_in: List[CustomerCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-customers request. Total customers to add: {len(customers_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [c.id for c in customers_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate customer IDs found in the request input."
            )
            
        # Check if any customer ID already exists in the database
        existing_customers = db.query(Customers).filter(Customers.id.in_(input_ids)).all()
        if existing_customers:
            existing_ids = [c.id for c in existing_customers]
            raise HTTPException(
                status_code=400,
                detail=f"Customers with IDs {existing_ids} already exist in the database."
            )
        
        # Add all customers
        created_customers = []
        # Get collection point mappings to populate collection_name in response
        cp_ids = {c.collection_point_id for c in customers_in if c.collection_point_id}
        cp_map = {}
        if cp_ids:
            cps = db.query(CollectionPoint).filter(CollectionPoint.id.in_(cp_ids)).all()
            cp_map = {cp.id: cp.collection_name for cp in cps}

        for customer_in in customers_in:
            new_customer = create_customer(db, obj_in=customer_in)
            # Create a dictionary representing the response to populate collection_name
            customer_dict = {
                "id": new_customer.id,
                "fullname": new_customer.fullname,
                "hoursehold_id": new_customer.hoursehold_id,
                "collection_point_id": new_customer.collection_point_id,
                "number_phone": new_customer.number_phone,
                "address": new_customer.address,
                "ingredient": new_customer.ingredient,
                "amount_of_debt": new_customer.amount_of_debt,
                "cash_advance": new_customer.cash_advance,
                "total_debt": new_customer.total_debt,
                "status": new_customer.status,
                "username": new_customer.username,
                "telegram_group": new_customer.telegram_group,
                "number_bank": new_customer.number_bank,
                "bank_name": new_customer.bank_name,
                "is_subsidized": new_customer.is_subsidized,
                "collection_name": cp_map.get(new_customer.collection_point_id) if new_customer.collection_point_id else None
            }
            created_customers.append(customer_dict)
            
        LogInfo(f"[TienNga API] Successfully added {len(created_customers)} customers.")
        return created_customers
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-customers", response_model=List[CustomerResponse])
def update_customers(
    customers_in: List[CustomerUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received update-customers request. Total customers to update: {len(customers_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [c.id for c in customers_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate customer IDs found in the request input."
            )
            
        # Check if all customer IDs exist in the database
        existing_customers = db.query(Customers).filter(Customers.id.in_(input_ids)).all()
        existing_ids = {c.id for c in existing_customers}
        
        missing_ids = [cid for cid in input_ids if cid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Customers with IDs {missing_ids} not found in the database."
            )
        
        # Update all customers
        updated_customers = []
        # Get collection point mappings to populate collection_name in response
        cp_ids = {c.collection_point_id for c in customers_in if c.collection_point_id}
        cp_map = {}
        if cp_ids:
            cps = db.query(CollectionPoint).filter(CollectionPoint.id.in_(cp_ids)).all()
            cp_map = {cp.id: cp.collection_name for cp in cps}

        for customer_in in customers_in:
            updated_customer = update_customer(db, customer_id=customer_in.id, obj_in=customer_in)
            
            customer_dict = {
                "id": updated_customer.id,
                "fullname": updated_customer.fullname,
                "hoursehold_id": updated_customer.hoursehold_id,
                "collection_point_id": updated_customer.collection_point_id,
                "number_phone": updated_customer.number_phone,
                "address": updated_customer.address,
                "ingredient": updated_customer.ingredient,
                "amount_of_debt": updated_customer.amount_of_debt,
                "cash_advance": updated_customer.cash_advance,
                "total_debt": updated_customer.total_debt,
                "status": updated_customer.status,
                "username": updated_customer.username,
                "telegram_group": updated_customer.telegram_group,
                "number_bank": updated_customer.number_bank,
                "bank_name": updated_customer.bank_name,
                "is_subsidized": updated_customer.is_subsidized,
                "collection_name": cp_map.get(updated_customer.collection_point_id) if updated_customer.collection_point_id else None
            }
            updated_customers.append(customer_dict)
            
        LogInfo(f"[TienNga API] Successfully updated {len(updated_customers)} customers.")
        return updated_customers
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in update-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-customers", response_model=List[CustomerResponse])
def delete_customers(
    customer_ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-customers request. Total customers to delete: {len(customer_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(customer_ids) != len(set(customer_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate customer IDs found in the request input."
            )
            
        # Check if all customer IDs exist in the database
        existing_customers = db.query(Customers).filter(Customers.id.in_(customer_ids)).all()
        existing_ids = {c.id for c in existing_customers}
        
        missing_ids = [cid for cid in customer_ids if cid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Customers with IDs {missing_ids} not found in the database."
            )
            
        # Map collection points to populate collection_name in the response
        cp_ids = {c.collection_point_id for c in existing_customers if c.collection_point_id}
        cp_map = {}
        if cp_ids:
            cps = db.query(CollectionPoint).filter(CollectionPoint.id.in_(cp_ids)).all()
            cp_map = {cp.id: cp.collection_name for cp in cps}
            
        deleted_customers = []
        for customer in existing_customers:
            customer_dict = {
                "id": customer.id,
                "fullname": customer.fullname,
                "hoursehold_id": customer.hoursehold_id,
                "collection_point_id": customer.collection_point_id,
                "number_phone": customer.number_phone,
                "address": customer.address,
                "ingredient": customer.ingredient,
                "amount_of_debt": customer.amount_of_debt,
                "cash_advance": customer.cash_advance,
                "total_debt": customer.total_debt,
                "status": customer.status,
                "username": customer.username,
                "telegram_group": customer.telegram_group,
                "number_bank": customer.number_bank,
                "bank_name": customer.bank_name,
                "is_subsidized": customer.is_subsidized,
                "collection_name": cp_map.get(customer.collection_point_id) if customer.collection_point_id else None
            }
            deleted_customers.append(customer_dict)
            delete_customer(db, customer_id=customer.id)
            
        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_customers)} customers.")
        return deleted_customers
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-shareholders", response_model=List[ShareholderResponse])
def get_shareholders(
    investment_id: Optional[UUID] = None,
    shareholder_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-shareholders request. investment_id: {investment_id}, shareholder_code: {shareholder_code}")
    try:
        shareholders = crud_shareholder.get_shareholders_with_investment_name(
            db,
            investment_id=investment_id,
            shareholder_code=shareholder_code
        )
        LogInfo(f"[TienNga API] Found {len(shareholders)} shareholders.")
        return shareholders
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-shareholders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-shareholders", response_model=List[ShareholderResponse])
def add_shareholders(
    shareholders_in: List[ShareholderCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-shareholders request. Total shareholders to add: {len(shareholders_in)}")
    try:
        # Check for duplicates in the input list itself
        input_codes = [s.shareholder_code for s in shareholders_in]
        if len(input_codes) != len(set(input_codes)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate shareholder codes found in the request input."
            )
            
        # Check if any shareholder code already exists in the database
        existing_shareholders = db.query(Shareholder).filter(Shareholder.shareholder_code.in_(input_codes)).all()
        if existing_shareholders:
            existing_codes = [s.shareholder_code for s in existing_shareholders]
            raise HTTPException(
                status_code=400,
                detail=f"Shareholders with codes {existing_codes} already exist in the database."
            )
        
        # Add all shareholders
        created_shareholders = []
        for sh_in in shareholders_in:
            new_sh = crud_shareholder.create_shareholder(db, obj_in=sh_in)
            
            # Fetch investment name if investment_id is provided
            inv_name = None
            if new_sh.investment_id:
                inv = db.query(Investment).filter(Investment.id == new_sh.investment_id).first()
                if inv:
                    inv_name = inv.name
                    
            created_shareholders.append({
                "id": new_sh.id,
                "shareholder_code": new_sh.shareholder_code,
                "fullname": new_sh.fullname,
                "investment_id": new_sh.investment_id,
                "investment_amount": new_sh.investment_amount,
                "start_date": new_sh.start_date,
                "username": new_sh.username,
                "telegram_group": new_sh.telegram_group,
                "notes": new_sh.notes,
                "created_at": new_sh.created_at,
                "investment_name": inv_name
            })
            
        LogInfo(f"[TienNga API] Successfully added {len(created_shareholders)} shareholders.")
        return created_shareholders
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-shareholders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-shareholders", response_model=List[ShareholderResponse])
def update_shareholders(
    shareholders_in: List[ShareholderUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received update-shareholders request. Total shareholders to update: {len(shareholders_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [s.id for s in shareholders_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate shareholder IDs found in the request input."
            )
            
        # Check if all shareholder IDs exist in the database
        existing_shareholders = db.query(Shareholder).filter(Shareholder.id.in_(input_ids)).all()
        existing_ids = {s.id for s in existing_shareholders}
        
        missing_ids = [sid for sid in input_ids if sid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Shareholders with IDs {missing_ids} not found in the database."
            )
        
        # Update all shareholders
        updated_shareholders = []
        for sh_in in shareholders_in:
            updated_sh = crud_shareholder.update_shareholder(db, shareholder_id=sh_in.id, obj_in=sh_in)
            
            inv_name = None
            if updated_sh.investment_id:
                inv = db.query(Investment).filter(Investment.id == updated_sh.investment_id).first()
                if inv:
                    inv_name = inv.name
                    
            updated_shareholders.append({
                "id": updated_sh.id,
                "shareholder_code": updated_sh.shareholder_code,
                "fullname": updated_sh.fullname,
                "investment_id": updated_sh.investment_id,
                "investment_amount": updated_sh.investment_amount,
                "start_date": updated_sh.start_date,
                "username": updated_sh.username,
                "telegram_group": updated_sh.telegram_group,
                "notes": updated_sh.notes,
                "created_at": updated_sh.created_at,
                "investment_name": inv_name
            })
            
        LogInfo(f"[TienNga API] Successfully updated {len(updated_shareholders)} shareholders.")
        return updated_shareholders
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in update-shareholders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-shareholders", response_model=List[ShareholderResponse])
def delete_shareholders(
    shareholder_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-shareholders request. Total shareholders to delete: {len(shareholder_ids)}")
    try:
        # Check for duplicates in the input list itself
        if len(shareholder_ids) != len(set(shareholder_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate shareholder IDs found in the request input."
            )
            
        # Check if all shareholder IDs exist in the database
        existing_shareholders = db.query(Shareholder).filter(Shareholder.id.in_(shareholder_ids)).all()
        existing_ids = {s.id for s in existing_shareholders}
        
        missing_ids = [sid for sid in shareholder_ids if sid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Shareholders with IDs {missing_ids} not found in the database."
            )
            
        deleted_shareholders = []
        for sh in existing_shareholders:
            inv_name = None
            if sh.investment_id:
                inv = db.query(Investment).filter(Investment.id == sh.investment_id).first()
                if inv:
                    inv_name = inv.name
                    
            deleted_shareholders.append({
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
                "investment_name": inv_name
            })
            crud_shareholder.delete_shareholder(db, shareholder_id=sh.id)
            
        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_shareholders)} shareholders.")
        return deleted_shareholders
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-shareholders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-daily-purchases", response_model=List[DailyPurchaseResponse])
def get_daily_purchases(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    hoursehold_id: Optional[str] = None,
    product_code: Optional[str] = None,
    collection_point_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-daily-purchases request. Filters: start_date={start_date}, end_date={end_date}, hoursehold_id={hoursehold_id}, product_code={product_code}, collection_point_id={collection_point_id}")
    try:
        cp_ids = None
        if collection_point_id:
            cp_ids = [cp.strip() for cp in collection_point_id.split(",") if cp.strip()]

        results = get_daily_purchases_detailed(
            db,
            start_date=start_date,
            end_date=end_date,
            hoursehold_id=hoursehold_id,
            product_code=product_code,
            collection_point_id=cp_ids,
        )
        LogInfo(f"[TienNga API] Found {len(results)} daily purchase records.")
        return results
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-daily-purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-daily-purchases", response_model=List[DailyPurchaseResponse])
def add_daily_purchases(
    purchases_in: List[DailyPurchaseCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-daily-purchases request. Total purchases: {len(purchases_in)}")
    try:
        created_records = []
        
        # 1. Fetch related CollectionPoints and Customers to map names in the response
        cp_ids = {p.collection_point_id for p in purchases_in if p.collection_point_id}
        hh_ids = {p.hoursehold_id for p in purchases_in if p.hoursehold_id}
        
        cp_map = {}
        if cp_ids:
            cps = db.query(CollectionPoint).filter(CollectionPoint.id.in_(cp_ids)).all()
            cp_map = {cp.id: cp.collection_name for cp in cps}
            
        cust_map = {}
        if hh_ids:
            custs = db.query(Customers).filter(Customers.hoursehold_id.in_(hh_ids)).all()
            cust_map = {cust.hoursehold_id: cust.fullname for cust in custs}

        # 2. Insert each purchase
        for purchase_in in purchases_in:
            new_dp = create_daily_purchase(db, obj_in=purchase_in)
            
            # Update customer debt if there is any saved amount
            if new_dp.saved_amount and new_dp.saved_amount > 0:
                customer = db.query(Customers).filter(Customers.hoursehold_id == new_dp.hoursehold_id).first()
                if customer:
                    if customer.total_debt is None: customer.total_debt = 0
                    customer.total_debt += int(new_dp.saved_amount)
                    db.commit()
            
            # Form response dictionary containing fullname and collection_name
            record_dict = {
                "id": new_dp.id,
                "hoursehold_id": new_dp.hoursehold_id,
                "fullname": cust_map.get(new_dp.hoursehold_id),
                "collection_name": cp_map.get(new_dp.collection_point_id),
                "day": new_dp.day,
                "is_subsidized": new_dp.is_subsidized,
                "weight": new_dp.weight,
                "tare_weight": new_dp.tare_weight,
                "actual_weight": new_dp.actual_weight,
                "degree": new_dp.degree,
                "dry_rubber": new_dp.dry_rubber,
                "unit_price": new_dp.unit_price,
                "subsidy_price": new_dp.subsidy_price,
                "total_amount": new_dp.total_amount,
                "paid_amount": new_dp.paid_amount,
                "saved_amount": new_dp.saved_amount,
                "product_code": new_dp.product_code
            }
            created_records.append(record_dict)

        LogInfo(f"[TienNga API] Successfully added {len(created_records)} daily purchase records.")
        return created_records
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-daily-purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-daily-purchases", response_model=List[DailyPurchaseResponse])
def update_daily_purchases(
    purchases_in: List[DailyPurchaseUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received update-daily-purchases request. Total purchases to update: {len(purchases_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [p.id for p in purchases_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate purchase IDs found in the request input."
            )
            
        # Check if all daily purchase IDs exist in the database
        existing_purchases = db.query(DailyPurchases).filter(DailyPurchases.id.in_(input_ids)).all()
        existing_ids = {p.id for p in existing_purchases}
        
        missing_ids = [pid for pid in input_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Daily purchases with IDs {missing_ids} not found in the database."
            )
            
        # Fetch related CollectionPoints and Customers to map names in the response
        cp_ids = set()
        hh_ids = set()
        
        db_purchases_map = {p.id: p for p in existing_purchases}
        
        for p_in in purchases_in:
            db_p = db_purchases_map[p_in.id]
            cp_id = p_in.collection_point_id if p_in.collection_point_id is not None else db_p.collection_point_id
            hh_id = p_in.hoursehold_id if p_in.hoursehold_id is not None else db_p.hoursehold_id
            if cp_id:
                cp_ids.add(cp_id)
            if hh_id:
                hh_ids.add(hh_id)
                
        cp_map = {}
        if cp_ids:
            cps = db.query(CollectionPoint).filter(CollectionPoint.id.in_(cp_ids)).all()
            cp_map = {cp.id: cp.collection_name for cp in cps}
            
        cust_map = {}
        if hh_ids:
            custs = db.query(Customers).filter(Customers.hoursehold_id.in_(hh_ids)).all()
            cust_map = {cust.hoursehold_id: cust.fullname for cust in custs}
            
        # Update each purchase
        updated_records = []
        for purchase_in in purchases_in:
            db_p = db.query(DailyPurchases).filter(DailyPurchases.id == purchase_in.id).first()
            old_saved_amount = db_p.saved_amount if db_p else 0
            old_hoursehold_id = db_p.hoursehold_id if db_p else None
            
            updated_dp = update_daily_purchase(db, purchase_id=purchase_in.id, obj_in=purchase_in)
            
            # Adjust customer debt
            new_saved_amount = updated_dp.saved_amount or 0
            new_hoursehold_id = updated_dp.hoursehold_id
            
            if old_hoursehold_id == new_hoursehold_id:
                diff = new_saved_amount - old_saved_amount
                if diff != 0:
                    customer = db.query(Customers).filter(Customers.hoursehold_id == new_hoursehold_id).first()
                    if customer:
                        if customer.total_debt is None: customer.total_debt = 0
                        customer.total_debt += int(diff)
                        db.commit()
            else:
                if old_hoursehold_id and old_saved_amount > 0:
                    old_cust = db.query(Customers).filter(Customers.hoursehold_id == old_hoursehold_id).first()
                    if old_cust:
                        if old_cust.total_debt is None: old_cust.total_debt = 0
                        old_cust.total_debt -= int(old_saved_amount)
                        db.commit()
                if new_hoursehold_id and new_saved_amount > 0:
                    new_cust = db.query(Customers).filter(Customers.hoursehold_id == new_hoursehold_id).first()
                    if new_cust:
                        if new_cust.total_debt is None: new_cust.total_debt = 0
                        new_cust.total_debt += int(new_saved_amount)
                        db.commit()
            
            record_dict = {
                "id": updated_dp.id,
                "hoursehold_id": updated_dp.hoursehold_id,
                "fullname": cust_map.get(updated_dp.hoursehold_id),
                "collection_name": cp_map.get(updated_dp.collection_point_id),
                "day": updated_dp.day,
                "is_subsidized": updated_dp.is_subsidized,
                "weight": updated_dp.weight,
                "tare_weight": updated_dp.tare_weight,
                "actual_weight": updated_dp.actual_weight,
                "degree": updated_dp.degree,
                "dry_rubber": updated_dp.dry_rubber,
                "unit_price": updated_dp.unit_price,
                "subsidy_price": updated_dp.subsidy_price,
                "total_amount": updated_dp.total_amount,
                "paid_amount": updated_dp.paid_amount,
                "saved_amount": updated_dp.saved_amount,
                "product_code": updated_dp.product_code
            }
            updated_records.append(record_dict)
            
        LogInfo(f"[TienNga API] Successfully updated {len(updated_records)} daily purchase records.")
        return updated_records
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in update-daily-purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-daily-purchases", response_model=List[DailyPurchaseResponse])
def delete_daily_purchases(
    purchase_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-daily-purchases request. Total purchases to delete: {len(purchase_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(purchase_ids) != len(set(purchase_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate purchase IDs found in the request input."
            )
            
        # Check if all daily purchase IDs exist in the database
        existing_purchases = db.query(DailyPurchases).filter(DailyPurchases.id.in_(purchase_ids)).all()
        existing_ids = {p.id for p in existing_purchases}
        
        missing_ids = [pid for pid in purchase_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Daily purchases with IDs {missing_ids} not found in the database."
            )
            
        # Map collection points and customers to populate names in the response
        cp_ids = {p.collection_point_id for p in existing_purchases if p.collection_point_id}
        cp_map = {}
        if cp_ids:
            cps = db.query(CollectionPoint).filter(CollectionPoint.id.in_(cp_ids)).all()
            cp_map = {cp.id: cp.collection_name for cp in cps}
            
        hh_ids = {p.hoursehold_id for p in existing_purchases if p.hoursehold_id}
        cust_map = {}
        if hh_ids:
            custs = db.query(Customers).filter(Customers.hoursehold_id.in_(hh_ids)).all()
            cust_map = {cust.hoursehold_id: cust.fullname for cust in custs}
            
        deleted_records = []
        for purchase in existing_purchases:
            record_dict = {
                "id": purchase.id,
                "hoursehold_id": purchase.hoursehold_id,
                "fullname": cust_map.get(purchase.hoursehold_id),
                "collection_name": cp_map.get(purchase.collection_point_id),
                "day": purchase.day,
                "is_subsidized": purchase.is_subsidized,
                "weight": purchase.weight,
                "tare_weight": purchase.tare_weight,
                "actual_weight": purchase.actual_weight,
                "degree": purchase.degree,
                "dry_rubber": purchase.dry_rubber,
                "unit_price": purchase.unit_price,
                "subsidy_price": purchase.subsidy_price,
                "total_amount": purchase.total_amount,
                "paid_amount": purchase.paid_amount,
                "saved_amount": purchase.saved_amount,
                "product_code": purchase.product_code
            }
            deleted_records.append(record_dict)
            
            # Adjust customer debt before deleting the purchase record
            if purchase.saved_amount and purchase.saved_amount > 0:
                customer = db.query(Customers).filter(Customers.hoursehold_id == purchase.hoursehold_id).first()
                if customer:
                    if customer.total_debt is None: customer.total_debt = 0
                    customer.total_debt -= int(purchase.saved_amount)
                    db.commit()
                    
            delete_daily_purchase(db, purchase_id=purchase.id)
            
        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_records)} daily purchase records.")
        return deleted_records
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-daily-purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-material-purchases", response_model=List[MaterialPurchaseResponse])
def get_material_purchases(
    material_type: Optional[str] = None,
    storage_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-material-purchases request. Filters: material_type={material_type}, storage_name={storage_name}, start_date={start_date}, end_date={end_date}")
    try:
        results = get_material_purchases_detailed(
            db, 
            material_type=material_type, 
            storage_name=storage_name,
            start_date=start_date,
            end_date=end_date
        )
        LogInfo(f"[TienNga API] Found {len(results)} material purchase records.")
        return results
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-material-purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-material-purchases", response_model=List[MaterialPurchaseResponse])
def add_material_purchases(
    purchases_in: List[MaterialPurchaseCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-material-purchases request. Total purchases: {len(purchases_in)}")
    try:
        # Fetch customer names for response
        cust_ids = {p.customer_id for p in purchases_in if p.customer_id}
        cust_map = {}
        if cust_ids:
            custs = db.query(Customers).filter(Customers.hoursehold_id.in_(cust_ids)).all()
            cust_map = {cust.hoursehold_id: cust.fullname for cust in custs}

        created_records = []
        for purchase_in in purchases_in:
            new_mp = create_material_purchase(db, obj_in=purchase_in)

            # Update inventory quantity: match by storage_name and material_name ↔ material_type
            # Case 1: material_name chứa material_type (VD: "Cao su RSS3" chứa "Cao su RSS3")
            inventory = db.query(Inventory).filter(
                Inventory.storage_name == new_mp.storage_name,
                Inventory.material_name.ilike(f"%{new_mp.material_type}%")
            ).first()
            # Case 2: material_type chứa material_name (VD: "Cao su RSS3" chứa "Cao su")
            if not inventory:
                all_invs = db.query(Inventory).filter(
                    Inventory.storage_name == new_mp.storage_name
                ).all()
                for inv in all_invs:
                    if inv.material_name and inv.material_name.lower() in (new_mp.material_type or "").lower():
                        inventory = inv
                        break
            if inventory:
                inventory.quantity = (inventory.quantity or 0.0) + (new_mp.weight or 0.0)
                db.commit()
                db.refresh(inventory)
                LogInfo(f"[TienNga API] Updated inventory '{inventory.material_name}' in '{inventory.storage_name}': quantity = {inventory.quantity}")
            else:
                LogInfo(f"[TienNga API] No matching inventory found for storage_name='{new_mp.storage_name}', material_type='{new_mp.material_type}'")

            # Update customer total_debt
            if new_mp.customer_id and new_mp.debt:
                customer = db.query(Customers).filter(Customers.hoursehold_id == new_mp.customer_id).first()
                if customer:
                    old_debt = customer.total_debt or 0
                    customer.total_debt = old_debt + int(new_mp.debt)
                    db.commit()
                    db.refresh(customer)
                    LogInfo(f"[TienNga API] Updated customer '{customer.fullname}' debt: {old_debt} -> {customer.total_debt}")

            record_dict = {
                "id": new_mp.id,
                "transaction_date": new_mp.transaction_date,
                "customer_id": new_mp.customer_id,
                "fullname": cust_map.get(new_mp.customer_id),
                "material_type": new_mp.material_type,
                "storage_name": new_mp.storage_name,
                "trip_count": new_mp.trip_count,
                "weight": new_mp.weight,
                "unit_price": new_mp.unit_price,
                "total_amount": new_mp.total_amount,
                "advance_payment": new_mp.advance_payment,
                "debt": new_mp.debt,
                "notes": new_mp.notes,
            }
            created_records.append(record_dict)

        LogInfo(f"[TienNga API] Successfully added {len(created_records)} material purchase records.")
        return created_records
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-material-purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.delete("/delete-material-purchases", response_model=List[MaterialPurchaseResponse])
def delete_material_purchases(
    purchase_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-material-purchases request. Total purchases to delete: {len(purchase_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(purchase_ids) != len(set(purchase_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate purchase IDs found in the request input."
            )

        # Check if all purchase IDs exist in the database
        existing_purchases = db.query(MaterialPurchase).filter(MaterialPurchase.id.in_(purchase_ids)).all()
        existing_ids = {p.id for p in existing_purchases}

        missing_ids = [pid for pid in purchase_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Material purchases with IDs {missing_ids} not found in the database."
            )

        # Map customer names for response
        cust_ids = {p.customer_id for p in existing_purchases if p.customer_id}
        cust_map = {}
        if cust_ids:
            custs = db.query(Customers).filter(Customers.hoursehold_id.in_(cust_ids)).all()
            cust_map = {cust.hoursehold_id: cust.fullname for cust in custs}

        deleted_records = []
        for purchase in existing_purchases:
            # Revert inventory quantity: match by storage_name and material_name ↔ material_type
            inventory = db.query(Inventory).filter(
                Inventory.storage_name == purchase.storage_name,
                Inventory.material_name.ilike(f"%{purchase.material_type}%")
            ).first()

            if not inventory:
                all_invs = db.query(Inventory).filter(
                    Inventory.storage_name == purchase.storage_name
                ).all()
                for inv in all_invs:
                    if inv.material_name and inv.material_name.lower() in (purchase.material_type or "").lower():
                        inventory = inv
                        break

            if inventory:
                inventory.quantity = (inventory.quantity or 0.0) - (purchase.weight or 0.0)
                if inventory.quantity < 0:
                    LogInfo(f"[TienNga API] Warning: Inventory '{inventory.material_name}' in '{inventory.storage_name}' quantity went negative: {inventory.quantity}")
                db.commit()
                db.refresh(inventory)
                LogInfo(f"[TienNga API] Reverted inventory '{inventory.material_name}' in '{inventory.storage_name}': quantity = {inventory.quantity}")
            else:
                LogInfo(f"[TienNga API] No matching inventory found for storage_name='{purchase.storage_name}', material_type='{purchase.material_type}'. Inventory quantity not updated.")

            # Revert customer total_debt
            if purchase.customer_id and purchase.debt:
                customer = db.query(Customers).filter(Customers.hoursehold_id == purchase.customer_id).first()
                if customer:
                    old_debt = customer.total_debt or 0
                    customer.total_debt = old_debt - int(purchase.debt)
                    db.commit()
                    db.refresh(customer)
                    LogInfo(f"[TienNga API] Reverted customer '{customer.fullname}' debt: {old_debt} -> {customer.total_debt}")

            record_dict = {
                "id": purchase.id,
                "transaction_date": purchase.transaction_date,
                "customer_id": purchase.customer_id,
                "fullname": cust_map.get(purchase.customer_id),
                "material_type": purchase.material_type,
                "storage_name": purchase.storage_name,
                "trip_count": purchase.trip_count,
                "weight": purchase.weight,
                "unit_price": purchase.unit_price,
                "total_amount": purchase.total_amount,
                "advance_payment": purchase.advance_payment,
                "debt": purchase.debt,
                "notes": purchase.notes,
            }
            deleted_records.append(record_dict)

            # Perform the actual deletion in CRUD
            delete_material_purchase(db, purchase_id=purchase.id)

        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_records)} material purchase records.")
        return deleted_records

    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-material-purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-inventories", response_model=List[InventoryResponse])
def get_inventories_api(
    material_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-inventories request. material_name filter: {material_name}")
    try:
        results = get_inventories_by_material_name(db, material_name=material_name)
        LogInfo(f"[TienNga API] Found {len(results)} inventory records.")
        return results
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-inventories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-partners", response_model=List[PartnerResponse])
def get_partners_api(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo("[TienNga API] Received get-partners request.")
    try:
        results = get_partners(db)
        LogInfo(f"[TienNga API] Found {len(results)} partner records.")
        return results
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-partners: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-partners", response_model=List[PartnerResponse])
def add_partners(
    partners_in: List[PartnerCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-partners request. Total partners to add: {len(partners_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [p.partner_id for p in partners_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate partner IDs found in the request input."
            )
            
        # Check if any partner ID already exists in the database
        existing_partners = db.query(Partners).filter(Partners.partner_id.in_(input_ids)).all()
        if existing_partners:
            existing_ids = [p.partner_id for p in existing_partners]
            raise HTTPException(
                status_code=400,
                detail=f"Partners with IDs {existing_ids} already exist in the database."
            )
            
        created_partners = []
        for partner_in in partners_in:
            new_partner = create_partner(db, obj_in=partner_in)
            created_partners.append(new_partner)
            
        LogInfo(f"[TienNga API] Successfully added {len(created_partners)} partners.")
        return created_partners
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-partners: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-partners", response_model=List[PartnerResponse])
def update_partners(
    partners_in: List[PartnerUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received update-partners request. Total partners to update: {len(partners_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [p.id for p in partners_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate partner IDs found in the request input."
            )
            
        # Check if all partner IDs exist in the database
        existing_partners = db.query(Partners).filter(Partners.id.in_(input_ids)).all()
        existing_ids = {p.id for p in existing_partners}
        
        missing_ids = [pid for pid in input_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Partners with IDs {missing_ids} not found in the database."
            )
            
        updated_partners = []
        for partner_in in partners_in:
            updated_partner = update_partner(db, partner_uuid=partner_in.id, obj_in=partner_in)
            updated_partners.append(updated_partner)
            
        LogInfo(f"[TienNga API] Successfully updated {len(updated_partners)} partners.")
        return updated_partners
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in update-partners: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-partners", response_model=List[PartnerResponse])
def delete_partners(
    partner_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-partners request. Total partners to delete: {len(partner_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(partner_ids) != len(set(partner_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate partner IDs found in the request input."
            )
            
        # Check if all partner IDs exist in the database
        existing_partners = db.query(Partners).filter(Partners.id.in_(partner_ids)).all()
        existing_ids = {p.id for p in existing_partners}
        
        missing_ids = [pid for pid in partner_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Partners with IDs {missing_ids} not found in the database."
            )
            
        deleted_partners = []
        for partner in existing_partners:
            deleted_partners.append(partner)
            delete_partner(db, partner_uuid=partner.id)
            
        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_partners)} partners.")
        return deleted_partners
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-partners: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-partner-businesses", response_model=List[PartnerBusinessResponse])
def get_partner_businesses(
    product_type: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-partner-businesses request. Filters: product_type={product_type}, transaction_type={transaction_type}, start_date={start_date}, end_date={end_date}")
    try:
        results = get_partner_businesses_detailed(
            db,
            product_type=product_type,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date,
        )
        LogInfo(f"[TienNga API] Found {len(results)} partner business records.")
        return results
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-partner-businesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/add-partner-businesses", response_model=List[PartnerBusinessResponse])
def add_partner_businesses(
    purchases_in: List[PartnerBusinessCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-partner-businesses request. Total purchases: {len(purchases_in)}")
    try:
        # Fetch related Partners to map names in the response
        partner_ids = {p.partner_id for p in purchases_in if p.partner_id}
        partner_map = {}
        if partner_ids:
            partners = db.query(Partners).filter(Partners.partner_id.in_(partner_ids)).all()
            partner_map = {p.partner_id: p.partner_name for p in partners}

        created_records = []
        for purchase_in in purchases_in:
            new_pb = create_partner_business(db, obj_in=purchase_in)
            
            # Form response dictionary containing partner_name
            record_dict = {
                "id": new_pb.id,
                "day": new_pb.day,
                "partner_id": new_pb.partner_id,
                "partner_name": partner_map.get(new_pb.partner_id),
                "import_amount": new_pb.import_amount,
                "export_amount": new_pb.export_amount,
                "order_code": new_pb.order_code,
                "unit_price": new_pb.unit_price,
                "total_amount": new_pb.total_amount,
                "notes": new_pb.notes,
                "product_type": new_pb.product_type,
                "actual_weight": new_pb.actual_weight,
                "dry_rubber": new_pb.dry_rubber,
                "degree": new_pb.degree
            }
            created_records.append(record_dict)

        LogInfo(f"[TienNga API] Successfully added {len(created_records)} partner business records.")
        return created_records
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-partner-businesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-partner-businesses", response_model=List[PartnerBusinessResponse])
def update_partner_businesses(
    purchases_in: List[PartnerBusinessUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received update-partner-businesses request. Total records to update: {len(purchases_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [p.id for p in purchases_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate record IDs found in the request input."
            )
            
        # Check if all record IDs exist in the database
        existing_records = db.query(PartnerBusinesses).filter(PartnerBusinesses.id.in_(input_ids)).all()
        existing_ids = {r.id for r in existing_records}
        
        missing_ids = [rid for rid in input_ids if rid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Partner business records with IDs {missing_ids} not found in the database."
            )
            
        # Fetch related Partners to map names in the response
        partner_ids = set()
        db_records_map = {r.id: r for r in existing_records}
        for p_in in purchases_in:
            db_r = db_records_map[p_in.id]
            p_id = p_in.partner_id if p_in.partner_id is not None else db_r.partner_id
            if p_id:
                partner_ids.add(p_id)
                
        partner_map = {}
        if partner_ids:
            partners = db.query(Partners).filter(Partners.partner_id.in_(partner_ids)).all()
            partner_map = {p.partner_id: p.partner_name for p in partners}
            
        # Update each record
        updated_records = []
        for p_in in purchases_in:
            updated_pb = update_partner_business(db, business_id=p_in.id, obj_in=p_in)
            
            record_dict = {
                "id": updated_pb.id,
                "day": updated_pb.day,
                "partner_id": updated_pb.partner_id,
                "partner_name": partner_map.get(updated_pb.partner_id),
                "import_amount": updated_pb.import_amount,
                "export_amount": updated_pb.export_amount,
                "order_code": updated_pb.order_code,
                "unit_price": updated_pb.unit_price,
                "total_amount": updated_pb.total_amount,
                "notes": updated_pb.notes,
                "product_type": updated_pb.product_type,
                "actual_weight": updated_pb.actual_weight,
                "dry_rubber": updated_pb.dry_rubber,
                "degree": updated_pb.degree
            }
            updated_records.append(record_dict)
            
        LogInfo(f"[TienNga API] Successfully updated {len(updated_records)} partner business records.")
        return updated_records
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in update-partner-businesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-partner-businesses", response_model=List[PartnerBusinessResponse])
def delete_partner_businesses(
    business_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-partner-businesses request. Total records to delete: {len(business_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(business_ids) != len(set(business_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate record IDs found in the request input."
            )
            
        # Check if all record IDs exist in the database
        existing_records = db.query(PartnerBusinesses).filter(PartnerBusinesses.id.in_(business_ids)).all()
        existing_ids = {r.id for r in existing_records}
        
        missing_ids = [rid for rid in business_ids if rid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Partner business records with IDs {missing_ids} not found in the database."
            )
            
        # Map partner names to populate in the response
        partner_ids = {r.partner_id for r in existing_records if r.partner_id}
        partner_map = {}
        if partner_ids:
            partners = db.query(Partners).filter(Partners.partner_id.in_(partner_ids)).all()
            partner_map = {p.partner_id: p.partner_name for p in partners}
            
        deleted_records = []
        for record in existing_records:
            record_dict = {
                "id": record.id,
                "day": record.day,
                "partner_id": record.partner_id,
                "partner_name": partner_map.get(record.partner_id),
                "import_amount": record.import_amount,
                "export_amount": record.export_amount,
                "order_code": record.order_code,
                "unit_price": record.unit_price,
                "total_amount": record.total_amount,
                "notes": record.notes,
                "product_type": record.product_type,
                "actual_weight": record.actual_weight,
                "dry_rubber": record.dry_rubber,
                "degree": record.degree
            }
            deleted_records.append(record_dict)
            delete_partner_business(db, business_id=record.id)
            
        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_records)} partner business records.")
        return deleted_records
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-partner-businesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-investments", response_model=List[InvestmentResponse])
def get_investments_api(
    role: Optional[str] = None,
    parent_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-investments request. Filters: role={role}, parent_id={parent_id}")
    try:
        results = get_investments(db, role=role, parent_id=parent_id)
        LogInfo(f"[TienNga API] Found {len(results)} investment records.")
        return results
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-investments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-investments", response_model=List[InvestmentResponse])
def add_investments(
    investments_in: List[InvestmentCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-investments request. Total investments to add: {len(investments_in)}")
    try:
        # Check for duplicates in the input list itself (by investment_code)
        input_codes = [i.investment_code for i in investments_in]
        if len(input_codes) != len(set(input_codes)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate investment codes found in the request input."
            )
            
        # Check if any investment code already exists in the database
        existing_investments = db.query(Investment).filter(Investment.investment_code.in_(input_codes)).all()
        if existing_investments:
            existing_codes = [i.investment_code for i in existing_investments]
            raise HTTPException(
                status_code=400,
                detail=f"Investments with codes {existing_codes} already exist in the database."
            )
            
        # Also check duplicates for IDs if provided
        input_ids = [i.id for i in investments_in if i.id is not None]
        if input_ids:
            if len(input_ids) != len(set(input_ids)):
                raise HTTPException(
                    status_code=400,
                    detail="Duplicate investment IDs found in the request input."
                )
            existing_by_ids = db.query(Investment).filter(Investment.id.in_(input_ids)).all()
            if existing_by_ids:
                existing_uuid_strings = [str(i.id) for i in existing_by_ids]
                raise HTTPException(
                    status_code=400,
                    detail=f"Investments with IDs {existing_uuid_strings} already exist in the database."
                )

        created_investments = []
        for investment_in in investments_in:
            new_inv = create_investment(db, obj_in=investment_in)
            created_investments.append(new_inv)
            
        LogInfo(f"[TienNga API] Successfully added {len(created_investments)} investments.")
        return created_investments
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-investments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-investments", response_model=List[InvestmentResponse])
def update_investments(
    investments_in: List[InvestmentUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received update-investments request. Total investments to update: {len(investments_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [i.id for i in investments_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate investment IDs found in the request input."
            )
            
        # Check if all investment IDs exist in the database
        existing_investments = db.query(Investment).filter(Investment.id.in_(input_ids)).all()
        existing_ids = {i.id for i in existing_investments}
        
        missing_ids = [iid for iid in input_ids if iid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Investments with IDs {missing_ids} not found in the database."
            )
            
        updated_investments = []
        for i_in in investments_in:
            if i_in.investment_code is not None:
                # Check if this code already exists for another investment
                dup = db.query(Investment).filter(
                    Investment.investment_code == i_in.investment_code,
                    Investment.id != i_in.id
                ).first()
                if dup:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Investment code '{i_in.investment_code}' already exists for another investment."
                    )
            
            updated_inv = update_investment(db, investment_uuid=i_in.id, obj_in=i_in)
            updated_investments.append(updated_inv)
            
        LogInfo(f"[TienNga API] Successfully updated {len(updated_investments)} investments.")
        return updated_investments
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in update-investments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-investments", response_model=List[InvestmentResponse])
def delete_investments(
    investment_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-investments request. Total investments to delete: {len(investment_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(investment_ids) != len(set(investment_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate investment IDs found in the request input."
            )
            
        # Check if all investment IDs exist in the database
        existing_investments = db.query(Investment).filter(Investment.id.in_(investment_ids)).all()
        existing_ids = {i.id for i in existing_investments}
        
        missing_ids = [iid for iid in investment_ids if iid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Investments with IDs {missing_ids} not found in the database."
            )
            
        deleted_investments = []
        for inv in existing_investments:
            deleted_investments.append(inv)
            delete_investment(db, investment_uuid=inv.id)
            
        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_investments)} investments.")
        return deleted_investments
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-investments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-daily-payments", response_model=List[DailyPaymentResponse])
def get_daily_payments_api(
    investment_id: Optional[UUID] = None,
    payment_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-daily-payments request. Filters: investment_id={investment_id}, payment_type={payment_type}, start_date={start_date}, end_date={end_date}")
    try:
        results = get_daily_payments(
            db,
            investment_id=investment_id,
            payment_type=payment_type,
            start_date=start_date,
            end_date=end_date
        )
        LogInfo(f"[TienNga API] Found {len(results)} daily payment records.")
        return results
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-daily-payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-daily-payments", response_model=List[DailyPaymentResponse])
def add_daily_payments(
    payments_in: List[DailyPaymentCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-daily-payments request. Total payments: {len(payments_in)}")
    try:
        # Validate that all investment_ids exist in the database
        inv_ids = {p.investment_id for p in payments_in if p.investment_id}
        if inv_ids:
            existing_invs = db.query(Investment).filter(Investment.id.in_(inv_ids)).all()
            existing_inv_ids = {i.id for i in existing_invs}
            missing_inv_ids = [str(iid) for iid in inv_ids if iid not in existing_inv_ids]
            if missing_inv_ids:
                raise HTTPException(
                    status_code=404,
                    detail=f"Investments with IDs {missing_inv_ids} not found in the database."
                )

        created_records = []
        for payment_in in payments_in:
            new_payment = create_daily_payment(db, obj_in=payment_in)
            created_records.append(new_payment)

        # Update investment financials for APPROVED payments
        for payment in created_records:
            LogInfo(f"[TienNga API] Checking payment id={payment.id}: status='{payment.status}', investment_id={payment.investment_id}, payment_type='{payment.payment_type}', amount={payment.amount}")
            if payment.status == "APPROVED" and payment.investment_id:
                LogInfo(f"[TienNga API] → Payment APPROVED with investment_id, calling update_investment_financials")
                update_investment_financials(
                    db,
                    investment_id=payment.investment_id,
                    payment_type=payment.payment_type,
                    amount=payment.amount
                )
            else:
                LogInfo(f"[TienNga API] → Skipped (status != APPROVED or no investment_id)")

        LogInfo(f"[TienNga API] Successfully added {len(created_records)} daily payment records.")
        return created_records
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-daily-payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-daily-payments", response_model=List[DailyPaymentResponse])
def delete_daily_payments(
    payment_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-daily-payments request. Total payments to delete: {len(payment_ids)}")
    try:
        # Check for duplicates in input list
        if len(payment_ids) != len(set(payment_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate payment IDs found in the request input."
            )

        # Check if all payment IDs exist in the database
        existing_payments = db.query(DailyPayment).filter(DailyPayment.id.in_(payment_ids)).all()
        existing_ids = {p.id for p in existing_payments}
        missing_ids = [str(pid) for pid in payment_ids if pid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Daily payments with IDs {missing_ids} not found in the database."
            )

        deleted_records = []
        for payment in existing_payments:
            # Reverse investment financials for APPROVED payments before deleting
            if payment.status == "APPROVED" and payment.investment_id:
                LogInfo(f"[TienNga API] Reversing financials for payment id={payment.id}: payment_type='{payment.payment_type}', amount={payment.amount}")
                update_investment_financials(
                    db,
                    investment_id=payment.investment_id,
                    payment_type=payment.payment_type,
                    amount=-payment.amount  # Âm để giảm
                )
            deleted_records.append(payment)
            delete_daily_payment(db, payment_id=payment.id)

        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_records)} daily payment records.")
        return deleted_records
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-daily-payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-inventory-exports", response_model=List[InventoryExportResponse])
def get_inventory_exports_api(
    storage_name: Optional[str] = None,
    material_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-inventory-exports request. Filters: storage_name={storage_name}, material_type={material_type}, start_date={start_date}, end_date={end_date}")
    try:
        results = get_inventory_exports(db, storage_name=storage_name, material_type=material_type, start_date=start_date, end_date=end_date)
        LogInfo(f"[TienNga API] Found {len(results)} inventory export records.")
        return results
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-inventory-exports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-inventory-exports", response_model=List[InventoryExportResponse])
def add_inventory_exports_api(
    exports_in: List[InventoryExportCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-inventory-exports request. Total exports: {len(exports_in)}")
    try:
        created_records = []
        for export_in in exports_in:
            # Revert inventory quantity: match by storage_name and material_name ↔ material_type
            inventory = db.query(Inventory).filter(
                Inventory.storage_name == export_in.storage_name,
                Inventory.material_name.ilike(f"%{export_in.material_type}%")
            ).first()

            if not inventory:
                all_invs = db.query(Inventory).filter(
                    Inventory.storage_name == export_in.storage_name
                ).all()
                for inv in all_invs:
                    if inv.material_name and inv.material_name.lower() in (export_in.material_type or "").lower():
                        inventory = inv
                        break

            remaining_weight = 0.0
            if inventory:
                inventory.quantity = (inventory.quantity or 0.0) - (export_in.export_weight or 0.0)
                if inventory.quantity < 0:
                    LogInfo(f"[TienNga API] Warning: Inventory '{inventory.material_name}' in '{inventory.storage_name}' quantity went negative: {inventory.quantity}")
                db.commit()
                db.refresh(inventory)
                remaining_weight = inventory.quantity
                LogInfo(f"[TienNga API] Deducted inventory '{inventory.material_name}' in '{inventory.storage_name}': quantity = {inventory.quantity}")
            else:
                LogInfo(f"[TienNga API] No matching inventory found for storage_name='{export_in.storage_name}', material_type='{export_in.material_type}'. Inventory quantity not updated.")

            new_export = create_inventory_export(db, obj_in=export_in, remaining_weight=remaining_weight)
            created_records.append(new_export)

        LogInfo(f"[TienNga API] Successfully added {len(created_records)} inventory export records.")
        return created_records
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-inventory-exports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-inventory-exports", response_model=List[InventoryExportResponse])
def delete_inventory_exports_api(
    export_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-inventory-exports request. Total exports to delete: {len(export_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(export_ids) != len(set(export_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate export IDs found in the request input."
            )

        # Check if all export IDs exist in the database
        existing_exports = db.query(InventoryExport).filter(InventoryExport.id.in_(export_ids)).all()
        existing_ids = {e.id for e in existing_exports}

        missing_ids = [eid for eid in export_ids if eid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Inventory exports with IDs {missing_ids} not found in the database."
            )

        deleted_records = []
        for export in existing_exports:
            # Revert inventory quantity: match by storage_name and material_name ↔ material_type
            inventory = db.query(Inventory).filter(
                Inventory.storage_name == export.storage_name,
                Inventory.material_name.ilike(f"%{export.material_type}%")
            ).first()

            if not inventory:
                all_invs = db.query(Inventory).filter(
                    Inventory.storage_name == export.storage_name
                ).all()
                for inv in all_invs:
                    if inv.material_name and inv.material_name.lower() in (export.material_type or "").lower():
                        inventory = inv
                        break

            if inventory:
                inventory.quantity = (inventory.quantity or 0.0) + (export.export_weight or 0.0)
                db.commit()
                db.refresh(inventory)
                LogInfo(f"[TienNga API] Reverted (added back) inventory '{inventory.material_name}' in '{inventory.storage_name}': quantity = {inventory.quantity}")
            else:
                LogInfo(f"[TienNga API] No matching inventory found for storage_name='{export.storage_name}', material_type='{export.material_type}'. Inventory quantity not updated.")

            record_dict = {
                "id": export.id,
                "export_date": export.export_date,
                "performer_name": export.performer_name,
                "material_type": export.material_type,
                "storage_name": export.storage_name,
                "export_weight": export.export_weight,
                "remaining_weight": export.remaining_weight,
                "notes": export.notes,
            }
            deleted_records.append(record_dict)

            # Perform the actual deletion in CRUD
            delete_inventory_export(db, export_id=export.id)

        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_records)} inventory export records.")
        return deleted_records

    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-inventory-exports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-product-transactions", response_model=List[ProductTransactionResponse])
def get_product_transactions_api(
    transaction_type: Optional[str] = None,
    material_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    storage_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received get-product-transactions request. Filters: transaction_type={transaction_type}, material_type={material_type}, start_date={start_date}, end_date={end_date}, storage_name={storage_name}")
    try:
        results = get_product_transactions(
            db,
            transaction_type=transaction_type,
            material_type=material_type,
            start_date=start_date,
            end_date=end_date,
            storage_name=storage_name
        )
        LogInfo(f"[TienNga API] Found {len(results)} product transaction records.")
        return results
    except Exception as e:
        LogInfo(f"[TienNga API] Error in get-product-transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-product-transactions", response_model=List[ProductTransactionResponse])
def add_product_transactions_api(
    txns_in: List[ProductTransactionCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-product-transactions request. Total: {len(txns_in)}")
    try:
        created_records = []
        for txn_in in txns_in:
            tt = (txn_in.transaction_type or "").strip().lower()
            if tt in ("nhập", "import"):
                direction = 1
            elif tt in ("xuất", "export"):
                direction = -1
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid transaction_type: '{txn_in.transaction_type}'. Must be one of: Nhập, import, Xuất, export."
                )

            # Create transaction record (commit=False for rollback)
            new_txn = create_product_transaction(db, obj_in=txn_in, commit=False)

            # Find matching inventory - Case 0: storage_id
            inventory = None
            if new_txn.storage_id:
                inventory = db.query(Inventory).filter(Inventory.id == new_txn.storage_id).first()

            # Fetch all inventories in this storage for fallbacks
            all_invs = db.query(Inventory).filter(
                Inventory.storage_name == new_txn.storage_name
            ).all()

            # Case 1: SQL ILIKE
            if not inventory:
                inventory = db.query(Inventory).filter(
                    Inventory.storage_name == new_txn.storage_name,
                    Inventory.material_name.ilike(f"%{new_txn.material_type}%")
                ).first()

            # Case 2: Substring match
            if not inventory:
                for inv in all_invs:
                    if inv.material_name and inv.material_name.lower() in (new_txn.material_type or "").lower():
                        inventory = inv
                        break

            # Case 3: Synonym check ("mủ" ↔ "cao su")
            if not inventory:
                for inv in all_invs:
                    if inv.material_name:
                        name_lower = inv.material_name.lower()
                        type_lower = (new_txn.material_type or "").lower()
                        norm_name = name_lower.replace("mủ", "cao su")
                        norm_type = type_lower.replace("mủ", "cao su")
                        if (norm_name in norm_type) or (norm_type in norm_name):
                            inventory = inv
                            break

            # Case 4: Single inventory in storage fallback
            if not inventory and len(all_invs) == 1:
                inventory = all_invs[0]

            if inventory:
                old_qty = inventory.quantity or 0.0
                inventory.quantity = old_qty + direction * (new_txn.quantity or 0.0)
                if inventory.quantity < 0:
                    LogInfo(f"[TienNga API] Warning: Inventory '{inventory.material_name}' in '{inventory.storage_name}' quantity went negative: {inventory.quantity}")
                LogInfo(f"[TienNga API] Updated inventory '{inventory.material_name}' in '{inventory.storage_name}': {old_qty} -> {inventory.quantity} (direction={direction}, tx_qty={new_txn.quantity})")
            else:
                LogInfo(f"[TienNga API] Match FAILED: No matching inventory found for storage_name='{new_txn.storage_name}' and material_type='{new_txn.material_type}'. Inventory quantity was NOT updated.")

            # Enforce debt sign: Nhập is positive, Xuất is negative
            if direction == 1:
                new_txn.debt = abs(new_txn.debt or 0.0)
            else:
                new_txn.debt = -abs(new_txn.debt or 0.0)

            # Update Customer or Partner debt
            if new_txn.customer_id:
                debt_change = new_txn.debt or 0.0
                if debt_change != 0.0:
                    # 1. Search in Customers
                    customer = db.query(Customers).filter(
                        (Customers.hoursehold_id == new_txn.customer_id) | (Customers.id == new_txn.customer_id)
                    ).first()
                    if customer:
                        if customer.total_debt is None:
                            customer.total_debt = 0.0
                        customer.total_debt += int(round(debt_change))
                        LogInfo(f"[TienNga API] Updated customer '{customer.fullname}' total_debt by {debt_change}: new_debt={customer.total_debt}")
                    else:
                        # 2. Search in Partners
                        partner = db.query(Partners).filter(Partners.partner_id == new_txn.customer_id).first()
                        if partner:
                            if partner.total_debt is None:
                                partner.total_debt = 0.0
                            partner.total_debt += debt_change
                            LogInfo(f"[TienNga API] Updated partner '{partner.partner_name}' total_debt by {debt_change}: new_debt={partner.total_debt}")
                        else:
                            LogInfo(f"[TienNga API] customer_id '{new_txn.customer_id}' not found in Customers or Partners. Debt not updated.")

            created_records.append(new_txn)

        # Commit everything atomically
        db.commit()

        # Refresh objects
        for rec in created_records:
            db.refresh(rec)

        LogInfo(f"[TienNga API] Successfully added {len(created_records)} product transaction records.")
        return created_records

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        LogInfo(f"[TienNga API] Error in add-product-transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-product-transactions", response_model=List[ProductTransactionResponse])
def delete_product_transactions_api(
    transaction_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-product-transactions request. Total: {len(transaction_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(transaction_ids) != len(set(transaction_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate transaction IDs found in the request input."
            )

        # Check if all transaction IDs exist in the database
        existing_txns = db.query(ProductTransaction).filter(ProductTransaction.id.in_(transaction_ids)).all()
        existing_ids = {t.id for t in existing_txns}

        missing_ids = [tid for tid in transaction_ids if tid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Product transactions with IDs {missing_ids} not found in the database."
            )

        deleted_records = []
        for txn in existing_txns:
            tt = (txn.transaction_type or "").strip().lower()
            if tt in ("nhập", "import"):
                direction = -1
            elif tt in ("xuất", "export"):
                direction = 1
            else:
                direction = 0

            # Find matching inventory - Case 0: storage_id
            inventory = None
            if txn.storage_id:
                inventory = db.query(Inventory).filter(Inventory.id == txn.storage_id).first()

            # Fetch all inventories in this storage for fallbacks
            all_invs = db.query(Inventory).filter(
                Inventory.storage_name == txn.storage_name
            ).all()

            # Case 1: SQL ILIKE
            if not inventory:
                inventory = db.query(Inventory).filter(
                    Inventory.storage_name == txn.storage_name,
                    Inventory.material_name.ilike(f"%{txn.material_type}%")
                ).first()

            # Case 2: Substring match
            if not inventory:
                for inv in all_invs:
                    if inv.material_name and inv.material_name.lower() in (txn.material_type or "").lower():
                        inventory = inv
                        break

            # Case 3: Synonym check ("mủ" ↔ "cao su")
            if not inventory:
                for inv in all_invs:
                    if inv.material_name:
                        name_lower = inv.material_name.lower()
                        type_lower = (txn.material_type or "").lower()
                        norm_name = name_lower.replace("mủ", "cao su")
                        norm_type = type_lower.replace("mủ", "cao su")
                        if (norm_name in norm_type) or (norm_type in norm_name):
                            inventory = inv
                            break

            # Case 4: Single inventory in storage fallback
            if not inventory and len(all_invs) == 1:
                inventory = all_invs[0]

            if inventory and direction != 0:
                old_qty = inventory.quantity or 0.0
                inventory.quantity = old_qty + direction * (txn.quantity or 0.0)
                if inventory.quantity < 0:
                    LogInfo(f"[TienNga API] Warning: Inventory '{inventory.material_name}' in '{inventory.storage_name}' quantity went negative: {inventory.quantity}")
                db.commit()
                db.refresh(inventory)
                LogInfo(f"[TienNga API] Reverted inventory '{inventory.material_name}' in '{inventory.storage_name}': {old_qty} -> {inventory.quantity} (direction={direction}, tx_qty={txn.quantity})")
            else:
                LogInfo(f"[TienNga API] Matching inventory not found or direction is 0. Inventory quantity was NOT updated.")

            record_dict = {
                "id": txn.id,
                "product_code": txn.product_code,
                "transaction_date": txn.transaction_date,
                "customer_id": txn.customer_id,
                "transaction_type": txn.transaction_type,
                "material_type": txn.material_type,
                "storage_id": txn.storage_id,
                "storage_name": txn.storage_name,
                "quantity": txn.quantity,
                "unit_price": txn.unit_price,
                "total_amount": txn.total_amount,
                "debt": txn.debt,
                "note": txn.note,
            }
            deleted_records.append(record_dict)

            # Revert Customer or Partner debt
            if txn.customer_id:
                debt_change = txn.debt or 0.0
                if debt_change != 0.0:
                    # 1. Search in Customers
                    customer = db.query(Customers).filter(
                        (Customers.hoursehold_id == txn.customer_id) | (Customers.id == txn.customer_id)
                    ).first()
                    if customer:
                        if customer.total_debt is None:
                            customer.total_debt = 0.0
                        customer.total_debt -= int(round(debt_change))
                        LogInfo(f"[TienNga API] Reverted customer '{customer.fullname}' total_debt by {-debt_change}: new_debt={customer.total_debt}")
                    else:
                        # 2. Search in Partners
                        partner = db.query(Partners).filter(Partners.partner_id == txn.customer_id).first()
                        if partner:
                            if partner.total_debt is None:
                                partner.total_debt = 0.0
                            partner.total_debt -= debt_change
                            LogInfo(f"[TienNga API] Reverted partner '{partner.partner_name}' total_debt by {-debt_change}: new_debt={partner.total_debt}")
                        else:
                            LogInfo(f"[TienNga API] customer_id '{txn.customer_id}' not found in Customers or Partners during delete. Debt not updated.")

            # Perform the actual deletion in CRUD
            delete_product_transaction(db, transaction_id=txn.id)

        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_records)} product transaction records.")
        return deleted_records

    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-product-transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-debt", response_model=ProcessDebtResponse)
def process_debt(
    request: ProcessDebtRequest,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received process-debt request. hoursehold_id={request.hoursehold_id}, employee_id={request.employee_id}, partner_id={request.partner_id}, amount={request.amount}, type_transaction={request.type_transaction}, start_date={request.start_date}, end_date={request.end_date}")

    try:
        # Validate type_transaction
        if request.type_transaction not in ("thu", "chi"):
            raise HTTPException(
                status_code=400,
                detail="type_transaction phải là 'thu' hoặc 'chi'."
            )

        if request.amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="amount phải lớn hơn 0."
            )

        # --- Xử lý cho hoursehold_id (customer) ---
        if request.hoursehold_id:
            customer = db.query(Customers).filter(
                Customers.hoursehold_id == request.hoursehold_id
            ).first()

            if not customer:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy khách hàng với mã hộ '{request.hoursehold_id}'."
                )

            old_debt = customer.total_debt or 0

            if request.type_transaction == "thu":
                # Thu công nợ: debt tăng (cộng amount)
                new_debt = old_debt + int(request.amount)
                customer.total_debt = new_debt
                db.commit()

                return ProcessDebtResponse(
                    success=True,
                    message=f"Thu công nợ thành công cho khách hàng {customer.fullname or customer.hoursehold_id}.",
                    target_id=customer.hoursehold_id,
                    target_name=customer.fullname,
                    type_transaction="thu",
                    amount=request.amount,
                    old_debt=old_debt,
                    new_debt=new_debt,
                )

            else:
                # Chi (trả) công nợ: debt giảm (trừ amount) + phân bổ FIFO vào daily_purchases
                new_debt = old_debt - int(request.amount)
                customer.total_debt = new_debt

                # === Phân bổ FIFO vào daily_purchases ===
                pending_query = db.query(DailyPurchases).filter(
                    DailyPurchases.hoursehold_id == request.hoursehold_id,
                    DailyPurchases.saved_amount > 0
                )
                if request.start_date:
                    pending_query = pending_query.filter(DailyPurchases.day >= request.start_date)
                if request.end_date:
                    pending_query = pending_query.filter(DailyPurchases.day <= request.end_date)
                pending_records = pending_query.order_by(DailyPurchases.day.asc()).all()

                remaining = request.amount
                allocations = []

                for record in pending_records:
                    if remaining <= 0:
                        break

                    current_saved = record.saved_amount or 0
                    if current_saved <= 0:
                        continue

                    allocated = min(remaining, current_saved)
                    record.paid_amount = (record.paid_amount or 0) + allocated
                    record.saved_amount = current_saved - allocated
                    remaining -= allocated

                    allocations.append(DailyPurchaseAllocation(
                        day=record.day,
                        allocated=allocated,
                        new_saved=record.saved_amount,
                    ))

                db.commit()

                return ProcessDebtResponse(
                    success=True,
                    message=f"Trả công nợ thành công cho khách hàng {customer.fullname or customer.hoursehold_id}.",
                    target_id=customer.hoursehold_id,
                    target_name=customer.fullname,
                    type_transaction="chi",
                    amount=request.amount,
                    old_debt=old_debt,
                    new_debt=new_debt,
                    allocations=allocations if allocations else None,
                    unallocated_amount=remaining if remaining > 0 else None,
                )

        # --- employee_id, partner_id: logic sẽ được bổ sung sau ---
        if request.employee_id:
            raise HTTPException(
                status_code=501,
                detail="Xử lý công nợ cho employee chưa được triển khai."
            )

        if request.partner_id:
            raise HTTPException(
                status_code=501,
                detail="Xử lý công nợ cho partner chưa được triển khai."
            )

        raise HTTPException(
            status_code=400,
            detail="Vui lòng cung cấp ít nhất một trong: hoursehold_id, employee_id, partner_id."
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in process-debt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-loss-control", response_model=ProcessLossControlResponse)
def process_loss_control(
    request: ProcessLossControlRequest,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received process-loss-control request. collection_point_id={request.collection_point_id}, start_date={request.start_date}, end_date={request.end_date}")
    try:
        # 1. Validate date range
        if request.start_date > request.end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date phải nhỏ hơn hoặc bằng end_date."
            )

        collection_name = None
        code_prefix = None

        # 2. Build LossControls query
        lc_query = db.query(LossControls).filter(
            LossControls.day >= request.start_date,
            LossControls.day <= request.end_date
        )

        if request.collection_point_id:
            # Validate UUID format
            try:
                uuid_val = UUID(str(request.collection_point_id))
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=400,
                    detail=f"collection_point_id không đúng định dạng UUID: {request.collection_point_id}"
                )

            # Lấy CollectionPoint → code_prefix
            collection_point = db.query(CollectionPoint).filter(
                CollectionPoint.id == uuid_val
            ).first()

            if not collection_point:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy điểm thu mua với ID: {request.collection_point_id}"
                )

            code_prefix = collection_point.code_prefix
            collection_name = collection_point.collection_name

            if not code_prefix:
                raise HTTPException(
                    status_code=400,
                    detail=f"Điểm thu mua '{collection_name}' chưa có code_prefix."
                )

            lc_query = lc_query.filter(
                LossControls.product_code.like(f"{code_prefix}%")
            )

        # 3. Execute query
        loss_controls = lc_query.order_by(LossControls.day.asc()).all()

        # 4. Với mỗi LossControl → query ProductTransaction + tính % hao hụt
        items = []
        for lc in loss_controls:
            total_import_quantity = 0.0

            if lc.estimated_completion:
                import_txns = db.query(ProductTransaction).filter(
                    ProductTransaction.product_code == lc.product_code,
                    ProductTransaction.transaction_date == lc.estimated_completion,
                    ProductTransaction.transaction_type.in_(["Nhập", "nhập", "Import", "import"])
                ).all()
                total_import_quantity = sum(txn.quantity or 0 for txn in import_txns)

            # Tính % hao hụt
            total_dry_rubber = lc.total_dry_rubber or 0
            if total_dry_rubber > 0:
                loss_percentage = round((total_dry_rubber - total_import_quantity) / total_dry_rubber * 100, 2)
            else:
                loss_percentage = 0.0

            items.append(LossControlItem(
                product_code=lc.product_code,
                day=lc.day,
                estimated_completion=lc.estimated_completion,
                total_dry_rubber=total_dry_rubber,
                total_import_quantity=total_import_quantity,
                loss_percentage=loss_percentage,
                total_amount=lc.total_amount,
                avg_unit_price=lc.avg_unit_price,
                processing_type=lc.processing_type,
                transaction_count=lc.transaction_count,
            ))

        log_suffix = f"prefix '{code_prefix}'" if code_prefix else "all collection points"
        LogInfo(f"[TienNga API] process-loss-control: found {len(items)} loss control records for {log_suffix}.")

        return ProcessLossControlResponse(
            collection_point_id=request.collection_point_id,
            collection_name=collection_name,
            code_prefix=code_prefix,
            start_date=request.start_date,
            end_date=request.end_date,
            total_items=len(items),
            items=items,
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in process-loss-control: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-inventories", response_model=List[InventoryResponse])
def add_inventories(
    inventories_in: List[InventoryCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received add-inventories request. Total inventories to add: {len(inventories_in)}")
    try:
        created_inventories = []
        for inv_in in inventories_in:
            new_inv = create_inventory(db, obj_in=inv_in)
            created_inventories.append(new_inv)
            
        LogInfo(f"[TienNga API] Successfully added {len(created_inventories)} inventories.")
        return created_inventories
    except Exception as e:
        LogInfo(f"[TienNga API] Error in add-inventories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-inventories", response_model=List[InventoryResponse])
def update_inventories(
    inventories_in: List[InventoryUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received update-inventories request. Total inventories to update: {len(inventories_in)}")
    try:
        # Check for duplicate IDs in the input list itself
        input_ids = [inv.id for inv in inventories_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate inventory IDs found in the request input."
            )
            
        # Check if all inventory IDs exist in the database
        existing_inventories = db.query(Inventory).filter(Inventory.id.in_(input_ids)).all()
        existing_ids = {inv.id for inv in existing_inventories}
        
        missing_ids = [iid for iid in input_ids if iid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Inventories with IDs {missing_ids} not found in the database."
            )
            
        # Update all inventories
        updated_inventories = []
        for inv_in in inventories_in:
            updated_inv = update_inventory(db, inventory_id=inv_in.id, obj_in=inv_in)
            if updated_inv:
                updated_inventories.append(updated_inv)
                
        LogInfo(f"[TienNga API] Successfully updated {len(updated_inventories)} inventories.")
        return updated_inventories
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in update-inventories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-inventories", response_model=List[InventoryResponse])
def delete_inventories(
    inventory_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    LogInfo(f"[TienNga API] Received delete-inventories request. Total inventories to delete: {len(inventory_ids)}")
    try:
        # Check for duplicates in input list itself
        if len(inventory_ids) != len(set(inventory_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate inventory IDs found in the request input."
            )
            
        # Check if all inventory IDs exist in the database
        existing_inventories = db.query(Inventory).filter(Inventory.id.in_(inventory_ids)).all()
        existing_ids = {inv.id for inv in existing_inventories}
        
        missing_ids = [iid for iid in inventory_ids if iid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Inventories with IDs {missing_ids} not found in the database."
            )
            
        deleted_inventories = []
        for inv in existing_inventories:
            deleted_inventories.append(inv)
            delete_inventory(db, inventory_id=inv.id)
            
        LogInfo(f"[TienNga API] Successfully deleted {len(deleted_inventories)} inventories.")
        return deleted_inventories
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[TienNga API] Error in delete-inventories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ProcessAdvanceAmountRequest(BaseModel):
    hoursehold_id: str
    amount: float


@router.post("/process-advance-amount")
def process_advance_amount(
    payloads: List[ProcessAdvanceAmountRequest],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    import calendar
    from datetime import date
    from sqlalchemy import func
    from app.core.config import settings
    from bot.utils.utils import fmt_money

    results = []

    for payload in payloads:
        hoursehold_id = payload.hoursehold_id.strip()
        cash_advance_requested = payload.amount

        customer = db.query(Customers).filter(Customers.hoursehold_id == hoursehold_id).first()
        if not customer:
            results.append({
                "hoursehold_id": hoursehold_id,
                "success": False,
                "message": f"Không tìm thấy hộ dân có mã {hoursehold_id}."
            })
            continue

        current_date = date.today()
        if current_date.month >= 5:
            start_year = current_date.year - 1
        else:
            start_year = current_date.year - 2

        start_date = date(start_year, 5, 1)
        end_year = start_year + 1
        end_month = 2
        last_day = calendar.monthrange(end_year, end_month)[1]
        end_date = date(end_year, end_month, last_day)

        total_sales = db.query(func.sum(DailyPurchases.total_amount)).filter(
            DailyPurchases.hoursehold_id == hoursehold_id,
            DailyPurchases.day >= start_date,
            DailyPurchases.day <= end_date
        ).scalar() or 0.0

        max_cash_advance_rate = settings.IMP_Config.MaxCashAdvance
        max_cash_advance = total_sales * max_cash_advance_rate
        current_advance = customer.cash_advance or 0
        total_after_advance = current_advance + cash_advance_requested

        if total_after_advance > max_cash_advance:
            reason = (
                f"Theo quy định, tổng số tiền ứng tối đa bằng {max_cash_advance_rate * 100:.0f}% tổng số tiền bán mủ mùa vụ trước.\n"
                f"Mùa vụ trước (từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}):\n"
                f"Tổng số tiền bán mủ: {fmt_money(total_sales)}\n"
                f"Hạn mức ứng tối đa: {fmt_money(max_cash_advance)}\n"
            )
            if current_advance > 0:
                reason += f"Đã ứng trước đó: {fmt_money(current_advance)}\n"
                reason += f"Còn lại có thể ứng: {fmt_money(max_cash_advance - current_advance)}"
            
            results.append({
                "hoursehold_id": hoursehold_id,
                "success": False,
                "exceeded": True,
                "message": f"Số tiền ứng vượt quá hạn mức cho phép ({fmt_money(max_cash_advance)}).",
                "reason": reason,
                "max_cash_advance": max_cash_advance,
                "current_advance": current_advance,
                "allowed_remaining": max_cash_advance - current_advance if max_cash_advance > current_advance else 0
            })
            continue

        customer.cash_advance = total_after_advance
        db.commit()
        db.refresh(customer)

        LogInfo(f"[TienNga API] User {current_user.username} processed cash advance {cash_advance_requested} for household {hoursehold_id}")

        results.append({
            "hoursehold_id": hoursehold_id,
            "success": True,
            "message": "Ứng tiền thành công!",
            "new_advance": total_after_advance
        })

    return results


class ProcessDeductionAdvanceAmountRequest(BaseModel):
    hoursehold_id: str
    amount: float


@router.post("/process-deduction-advance-amount")
def process_deduction_advance_amount(
    payloads: List[ProcessDeductionAdvanceAmountRequest],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    results = []

    for payload in payloads:
        hoursehold_id = payload.hoursehold_id.strip()
        amount = payload.amount

        customer = db.query(Customers).filter(Customers.hoursehold_id == hoursehold_id).first()
        if not customer:
            results.append({
                "hoursehold_id": hoursehold_id,
                "success": False,
                "message": f"Không tìm thấy hộ dân có mã {hoursehold_id}."
            })
            continue

        current_debt = customer.total_debt or 0

        if amount > current_debt:
            results.append({
                "hoursehold_id": hoursehold_id,
                "success": False,
                "message": "Công nợ không đủ dư."
            })
            continue

        customer.total_debt = current_debt - int(amount)
        customer.cash_advance = (customer.cash_advance or 0) - int(amount)
        db.commit()
        db.refresh(customer)

        LogInfo(f"[TienNga API] User {current_user.username} processed deduction advance amount {amount} for household {hoursehold_id}")

        results.append({
            "hoursehold_id": hoursehold_id,
            "success": True,
            "message": "Khấu trừ công nợ thành công!",
            "new_debt": customer.total_debt,
            "new_advance": customer.cash_advance
        })

    return results


class BillRecord(BaseModel):
    ngay: str
    tuan: Optional[str] = "—"
    tro_gia: Optional[float] = 0.0
    kl: Optional[float] = 0.0
    bi: Optional[float] = 0.0
    kl_tt: Optional[float] = 0.0
    so_do: Optional[float] = 0.0
    mu_kho: Optional[float] = 0.0
    don_gia: Optional[float] = 0.0
    gia_ht: Optional[float] = 0.0
    thanh_tien: Optional[float] = 0.0
    thanh_toan: Optional[float] = 0.0
    thanh_tien_kht: Optional[float] = 0.0
    luu_so: Optional[float] = 0.0


class BillReportRequest(BaseModel):
    ten_kh: str
    ma_ho: str
    diem_thu_mua: str
    timeframe: str
    records: List[BillRecord]
    tong_kl: Optional[float] = 0.0
    tong_kl_tt: Optional[float] = 0.0
    tong_thanh_tien: Optional[float] = 0.0
    tong_thanh_toan: Optional[float] = 0.0
    tong_thanh_tien_kht: Optional[float] = 0.0
    tien_da_ung: Optional[float] = 0.0


@router.post("/export-paid-bill")
async def export_paid_bill(
    payload: BillReportRequest,
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    from fastapi import Response
    from bot.utils.paid_bill_report_generator import generate_paid_bill_report_image
    try:
        data = payload.dict()
        img_buf = await generate_paid_bill_report_image(data)
        return Response(content=img_buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate paid bill report: {str(e)}")


@router.post("/export-saved-bill")
async def export_saved_bill(
    payload: BillReportRequest,
    current_user: Credential = Depends(require_permission("tien-nga"))
):
    from fastapi import Response
    from bot.utils.saved_bill_report_generator import generate_saved_bill_report_image
    try:
        data = payload.dict()
        img_buf = await generate_saved_bill_report_image(data)
        return Response(content=img_buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate saved bill report: {str(e)}")





