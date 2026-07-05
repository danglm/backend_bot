from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_permission
from app.schemas import credit as schemas_credit
from app.crud import credit as crud_credit
from app.models.employee import Credential
from app.models.credit import CreditCustomer, Credit, CreditStatus, CreditInterest
from bot.utils.logger import LogInfo
from typing import Optional
from uuid import UUID
from datetime import datetime

router = APIRouter()


@router.get("/get-credit-interests", response_model=list[schemas_credit.CreditInterestResponse])
async def api_get_credit_interests(
    contract_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Lấy danh sách lịch sử thu lãi kèm thông tin hợp đồng và khách hàng.
    """
    LogInfo(f"[Credit API] Received get-credit-interests request. Contract ID: {contract_id}, Start date: {start_date}, End date: {end_date}")

    parsed_start_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            try:
                parsed_start_date = datetime.strptime(start_date, "%d/%m/%Y").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Expected YYYY-MM-DD or dd/mm/yyyy."
                )

    parsed_end_date = None
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            try:
                parsed_end_date = datetime.strptime(end_date, "%d/%m/%Y").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Expected YYYY-MM-DD or dd/mm/yyyy."
                )

    try:
        interests = crud_credit.get_credit_interests_detailed(
            db,
            contract_id=contract_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        LogInfo(f"[Credit API] Found {len(interests)} credit interest records.")
        return interests
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in get-credit-interests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-credit-interests", response_model=list[schemas_credit.CreditInterest])
async def api_add_credit_interests(
    interests_in: list[schemas_credit.CreditInterestCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Thêm mới danh sách lịch sử thu lãi (bulk).
    """
    LogInfo(f"[Credit API] Received add-credit-interests request. Total: {len(interests_in)}")
    try:
        # Validate all contract_ids exist
        contract_ids = list({i.contract_id for i in interests_in if i.contract_id})
        if contract_ids:
            existing_contracts = db.query(Credit).filter(Credit.contract_id.in_(contract_ids)).all()
            existing_contract_ids = {c.contract_id for c in existing_contracts}
            missing = [cid for cid in contract_ids if cid not in existing_contract_ids]
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy hợp đồng với mã: {missing}"
                )

        # Build contracts map for updating interest_debt
        contracts_map = {}
        if contract_ids:
            contracts_map = {c.contract_id: c for c in existing_contracts}

        created = []
        for item in interests_in:
            new_interest = crud_credit.create_credit_interest(db, obj_in=item)
            created.append(new_interest)
            
            # Giảm nợ lãi (interest_debt) trên hợp đồng
            contract = contracts_map.get(item.contract_id)
            if contract:
                paid_amount = item.interest_amount or 0.0
                contract.interest_debt = max((contract.interest_debt or 0.0) - paid_amount, 0.0)
                db.commit()
                LogInfo(f"[Credit API] Reduced interest_debt by {paid_amount:,.0f} for contract {item.contract_id} -> {contract.interest_debt:,.0f}")

        LogInfo(f"[Credit API] Successfully added {len(created)} credit interest records.")
        return created
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in add-credit-interests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-credit-customers", response_model=list[schemas_credit.CreditCustomer])
async def api_get_credit_customers(
    customer_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Lấy toàn bộ danh sách khách hàng tín dụng.
    """
    LogInfo(f"[Credit API] Received get-credit-customers request. Customer ID filter: {customer_id}")
    try:
        customers = crud_credit.get_all_credit_customers(db, customer_id=customer_id)
        LogInfo(f"[Credit API] Found {len(customers)} credit customers.")
        return customers
    except Exception as e:
        LogInfo(f"[Credit API] Error in get-credit-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-credits", response_model=list[schemas_credit.CreditResponse])
async def api_get_credits(
    status: Optional[str] = None,
    loan_type: Optional[str] = None,
    contract_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Lấy danh sách các hợp đồng tín dụng kèm thông tin khách hàng.
    """
    LogInfo(f"[Credit API] Received get-credits request. Status: {status}, Loan type: {loan_type}, Contract ID: {contract_id}, Start date: {start_date}, End date: {end_date}")

    parsed_start_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            try:
                parsed_start_date = datetime.strptime(start_date, "%d/%m/%Y").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Expected YYYY-MM-DD or dd/mm/yyyy."
                )

    parsed_end_date = None
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            try:
                parsed_end_date = datetime.strptime(end_date, "%d/%m/%Y").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Expected YYYY-MM-DD or dd/mm/yyyy."
                )

    try:
        credits = crud_credit.get_credits_detailed(
            db,
            status=status,
            loan_type=loan_type,
            contract_id=contract_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        LogInfo(f"[Credit API] Found {len(credits)} credit records.")
        return credits
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in get-credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-credit-customers", response_model=list[schemas_credit.CreditCustomer])
async def api_add_credit_customers(
    customers_in: list[schemas_credit.CreditCustomerCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Thêm mới danh sách khách hàng tín dụng (bulk).
    """
    LogInfo(f"[Credit API] Received add-credit-customers request. Total customers to add: {len(customers_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [c.customer_id for c in customers_in if c.customer_id]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate customer_id found in the request input."
            )
            
        # Check if any customer_id already exists in the database
        existing_customers = db.query(CreditCustomer).filter(CreditCustomer.customer_id.in_(input_ids)).all()
        if existing_customers:
            existing_ids = [c.customer_id for c in existing_customers]
            raise HTTPException(
                status_code=400,
                detail=f"Credit customers with IDs {existing_ids} already exist in the database."
            )
            
        created_customers = []
        for cust_in in customers_in:
            new_cust = crud_credit.create_credit_customer(db, obj_in=cust_in)
            created_customers.append(new_cust)
            
        LogInfo(f"[Credit API] Successfully added {len(created_customers)} credit customers.")
        return created_customers
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in add-credit-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-credit-customers", response_model=list[schemas_credit.CreditCustomer])
async def api_update_credit_customers(
    customers_in: list[schemas_credit.CreditCustomerUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Cập nhật danh sách khách hàng tín dụng (bulk).
    """
    LogInfo(f"[Credit API] Received update-credit-customers request. Total customers to update: {len(customers_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [c.id for c in customers_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all customer IDs exist in the database
        existing_customers = db.query(CreditCustomer).filter(CreditCustomer.id.in_(input_ids)).all()
        existing_ids = {c.id for c in existing_customers}
        
        missing_ids = [cid for cid in input_ids if cid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Credit customers with IDs {missing_ids} not found in the database."
            )
            
        updated_customers = []
        for cust_in in customers_in:
            updated_cust = crud_credit.update_credit_customer(db, customer_uuid=cust_in.id, obj_in=cust_in)
            if updated_cust:
                updated_customers.append(updated_cust)
            
        LogInfo(f"[Credit API] Successfully updated {len(updated_customers)} credit customers.")
        return updated_customers
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in update-credit-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-credit-customers", response_model=list[schemas_credit.CreditCustomer])
async def api_delete_credit_customers(
    customer_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Xóa danh sách khách hàng tín dụng (bulk).
    """
    LogInfo(f"[Credit API] Received delete-credit-customers request. Total customers to delete: {len(customer_ids)}")
    try:
        # Check for duplicates in the input list itself
        if len(customer_ids) != len(set(customer_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all customer IDs exist in the database
        existing_customers = db.query(CreditCustomer).filter(CreditCustomer.id.in_(customer_ids)).all()
        existing_ids = {c.id for c in existing_customers}
        
        missing_ids = [cid for cid in customer_ids if cid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Credit customers with IDs {missing_ids} not found in the database."
            )
            
        deleted_customers = []
        for cust_uuid in customer_ids:
            deleted_cust = crud_credit.delete_credit_customer(db, customer_uuid=cust_uuid)
            if deleted_cust:
                deleted_customers.append(deleted_cust)
            
        LogInfo(f"[Credit API] Successfully deleted {len(deleted_customers)} credit customers.")
        return deleted_customers
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in delete-credit-customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-credits", response_model=list[schemas_credit.Credit])
async def api_add_credits(
    credits_in: list[schemas_credit.CreditCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Thêm mới danh sách hợp đồng tín dụng (bulk).
    """
    LogInfo(f"[Credit API] Received add-credits request. Total credits to add: {len(credits_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [c.contract_id for c in credits_in if c.contract_id]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate contract_id found in the request input."
            )
            
        # Check if any contract_id already exists in the database
        existing_credits = db.query(Credit).filter(Credit.contract_id.in_(input_ids)).all()
        if existing_credits:
            existing_ids = [c.contract_id for c in existing_credits]
            raise HTTPException(
                status_code=400,
                detail=f"Credit contracts with IDs {existing_ids} already exist in the database."
            )
            
        # Pre-fetch customers to optimize queries and support in-memory limit tracking
        customer_ids = [c.customer_id for c in credits_in if c.customer_id]
        customers_map = {}
        if customer_ids:
            customers = db.query(CreditCustomer).filter(CreditCustomer.id.in_(customer_ids)).all()
            customers_map = {c.id: c for c in customers}

        created_credits = []
        for cred_in in credits_in:
            if cred_in.customer_id:
                customer = customers_map.get(cred_in.customer_id)
                if not customer:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Credit customer with ID {cred_in.customer_id} does not exist."
                    )
                
                amount = cred_in.initial_principal or 0.0
                limit_remaining = customer.remaining_credit_limit or 0.0
                
                is_secured = False
                if cred_in.loan_type:
                    loan_type_lower = cred_in.loan_type.lower().strip()
                    if loan_type_lower in ["secured", "thế chấp", "the chap", "collateral"]:
                        is_secured = True
                
                if is_secured:
                    if limit_remaining < amount:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Lỗi Hạn Mức: Hợp đồng thế chấp (secured) yêu cầu số tiền vay ({amount:,.0f}) không được vượt quá Hạn mức còn lại của khách hàng ({limit_remaining:,.0f})."
                        )
                
                customer.remaining_credit_limit = limit_remaining - amount
                customer.total_principal_outstanding = (customer.total_principal_outstanding or 0.0) + amount
            
            new_cred = crud_credit.create_credit(db, obj_in=cred_in)
            created_credits.append(new_cred)
            
        LogInfo(f"[Credit API] Successfully added {len(created_credits)} credit contracts.")
        return created_credits
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in add-credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-credits", response_model=list[schemas_credit.Credit])
async def api_update_credits(
    credits_in: list[schemas_credit.CreditUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Cập nhật danh sách hợp đồng tín dụng (bulk).
    """
    LogInfo(f"[Credit API] Received update-credits request. Total credits to update: {len(credits_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [c.id for c in credits_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all credit IDs exist in the database
        existing_credits = db.query(Credit).filter(Credit.id.in_(input_ids)).all()
        existing_ids = {c.id for c in existing_credits}
        
        missing_ids = [cid for cid in input_ids if cid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Credit contracts with IDs {missing_ids} not found in the database."
            )
            
        # Build a map of existing credits for old status lookup
        existing_credits_map = {c.id: c for c in existing_credits}
        
        # Statuses that mean the contract is "closed" (no longer outstanding)
        closed_statuses = {CreditStatus.PAID.value, CreditStatus.CANCELLED.value}
        # Statuses that mean the contract is "open" (still outstanding)
        open_statuses = {CreditStatus.ACTIVE.value, CreditStatus.BAD_DEBT.value}
            
        updated_credits = []
        for cred_in in credits_in:
            old_credit = existing_credits_map.get(cred_in.id)
            
            # Check if status is changing from open -> closed (paid/cancelled)
            if old_credit and cred_in.credit_status:
                old_status = old_credit.credit_status
                new_status = cred_in.credit_status.value if isinstance(cred_in.credit_status, CreditStatus) else cred_in.credit_status
                
                # Restore remaining_credit_limit when closing an open contract
                if old_status in open_statuses and new_status in closed_statuses:
                    customer = db.query(CreditCustomer).filter(CreditCustomer.id == old_credit.customer_id).first()
                    if customer:
                        restore_amount = old_credit.initial_principal or 0.0
                        new_remaining = (customer.remaining_credit_limit or 0.0) + restore_amount
                        # Cap: remaining_credit_limit không được vượt quá total_credit_limit
                        total_limit = customer.total_credit_limit or 0.0
                        customer.remaining_credit_limit = min(new_remaining, total_limit)
                        customer.total_principal_outstanding = max((customer.total_principal_outstanding or 0.0) - restore_amount, 0.0)
                        LogInfo(f"[Credit API] Restored {restore_amount:,.0f} to customer {customer.customer_id} remaining_credit_limit -> {customer.remaining_credit_limit:,.0f} (contract {old_credit.contract_id} -> {new_status})")
                
                # Deduct remaining_credit_limit when re-opening a closed contract
                elif old_status in closed_statuses and new_status in open_statuses:
                    customer = db.query(CreditCustomer).filter(CreditCustomer.id == old_credit.customer_id).first()
                    if customer:
                        deduct_amount = old_credit.initial_principal or 0.0
                        customer.remaining_credit_limit = (customer.remaining_credit_limit or 0.0) - deduct_amount
                        customer.total_principal_outstanding = (customer.total_principal_outstanding or 0.0) + deduct_amount
                        LogInfo(f"[Credit API] Deducted {deduct_amount:,.0f} from customer {customer.customer_id} remaining_credit_limit (contract {old_credit.contract_id} -> {new_status})")
            
            updated_cred = crud_credit.update_credit(db, credit_uuid=cred_in.id, obj_in=cred_in)
            if updated_cred:
                updated_credits.append(updated_cred)
            
        LogInfo(f"[Credit API] Successfully updated {len(updated_credits)} credit contracts.")
        return updated_credits
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in update-credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-credits", response_model=list[schemas_credit.Credit])
async def api_delete_credits(
    credit_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Xóa danh sách hợp đồng tín dụng (bulk).
    """
    LogInfo(f"[Credit API] Received delete-credits request. Total credits to delete: {len(credit_ids)}")
    try:
        # Check for duplicates in the input list itself
        if len(credit_ids) != len(set(credit_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all credit IDs exist in the database
        existing_credits = db.query(Credit).filter(Credit.id.in_(credit_ids)).all()
        existing_ids = {c.id for c in existing_credits}
        
        missing_ids = [cid for cid in credit_ids if cid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Credit contracts with IDs {missing_ids} not found in the database."
            )
            
        # Block deletion of bad_debt credits
        bad_debt_contracts = [c for c in existing_credits if c.credit_status == CreditStatus.BAD_DEBT.value]
        if bad_debt_contracts:
            bad_debt_ids = [c.contract_id for c in bad_debt_contracts]
            raise HTTPException(
                status_code=400,
                detail=f"Không được phép xóa hợp đồng nợ xấu (bad_debt): {bad_debt_ids}"
            )
            
        # Rollback customer limits only for active credits
        for cred in existing_credits:
            if cred.customer_id and cred.credit_status == CreditStatus.ACTIVE.value:
                customer = db.query(CreditCustomer).filter(CreditCustomer.id == cred.customer_id).first()
                if customer:
                    restore_amount = cred.initial_principal or 0.0
                    new_remaining = (customer.remaining_credit_limit or 0.0) + restore_amount
                    total_limit = customer.total_credit_limit or 0.0
                    customer.remaining_credit_limit = min(new_remaining, total_limit)
                    customer.total_principal_outstanding = max((customer.total_principal_outstanding or 0.0) - restore_amount, 0.0)
                    LogInfo(f"[Credit API] Rollback: restored {restore_amount:,.0f} to customer {customer.customer_id} remaining_credit_limit -> {customer.remaining_credit_limit:,.0f} (deleted contract {cred.contract_id})")
        
        deleted_credits = []
        for cred_uuid in credit_ids:
            deleted_cred = crud_credit.delete_credit(db, credit_uuid=cred_uuid)
            if deleted_cred:
                deleted_credits.append(deleted_cred)
            
        LogInfo(f"[Credit API] Successfully deleted {len(deleted_credits)} credit contracts.")
        return deleted_credits
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in delete-credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-credit-interests", response_model=list[schemas_credit.CreditInterest])
async def api_delete_credit_interests(
    interest_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Xóa danh sách lịch sử thu lãi (bulk) và hoàn lại nợ lãi.
    """
    LogInfo(f"[Credit API] Received delete-credit-interests request. Total: {len(interest_ids)}")
    try:
        # Check for duplicates in the input list itself
        if len(interest_ids) != len(set(interest_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )
            
        # Check if all interest IDs exist in the database
        existing_interests = db.query(CreditInterest).filter(CreditInterest.id.in_(interest_ids)).all()
        existing_ids = {i.id for i in existing_interests}
        
        missing_ids = [iid for iid in interest_ids if iid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Credit interest records with IDs {missing_ids} not found in the database."
            )

        # Get all contract_ids from the existing interests to fetch corresponding credits
        contract_ids = list({i.contract_id for i in existing_interests if i.contract_id})
        contracts_map = {}
        if contract_ids:
            existing_contracts = db.query(Credit).filter(Credit.contract_id.in_(contract_ids)).all()
            contracts_map = {c.contract_id: c for c in existing_contracts}

        # Rollback interest_debt for each contract before deleting the interest record
        for interest in existing_interests:
            contract = contracts_map.get(interest.contract_id)
            if contract:
                refund_amount = interest.interest_amount or 0.0
                contract.interest_debt = (contract.interest_debt or 0.0) + refund_amount
                LogInfo(f"[Credit API] Rollback: restored interest_debt by {refund_amount:,.0f} for contract {contract.contract_id} -> {contract.interest_debt:,.0f} (deleted interest ID {interest.id})")

        # Now perform the deletion
        deleted_interests = []
        for interest_uuid in interest_ids:
            deleted_interest = crud_credit.delete_credit_interest(db, interest_uuid=interest_uuid)
            if deleted_interest:
                deleted_interests.append(deleted_interest)

        LogInfo(f"[Credit API] Successfully deleted {len(deleted_interests)} credit interest records.")
        return deleted_interests
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Credit API] Error in delete-credit-interests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-classifications", response_model=list[str])
async def api_get_credit_classifications(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("credit"))
):
    """
    Lấy danh sách các phân loại tín dụng duy nhất hiện có trong cơ sở dữ liệu.
    """
    LogInfo("[Credit API] Received get-classifications request.")
    try:
        classifications = crud_credit.get_distinct_classifications(db)
        return classifications
    except Exception as e:
        LogInfo(f"[Credit API] Error in get-classifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

