from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas import credit as schemas_credit
from app.crud import credit as crud_credit
from app.models.employee import Credential

router = APIRouter()

@router.post("/create", response_model=schemas_credit.Credit)
async def api_create_credit(
    credit_in: schemas_credit.CreditCreate,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Create a new credit contract.
    """
    try:
        return crud_credit.create_credit(db, obj_in=credit_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=list[schemas_credit.Credit])
async def api_get_credits(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all credit contracts.
    """
    try:
        return crud_credit.get_credits(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interest/create", response_model=schemas_credit.CreditInterest)
async def api_create_credit_interest(
    interest_in: schemas_credit.CreditInterestCreate,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Add a monthly interest payment.
    """
    try:
        return crud_credit.create_credit_interest(db, obj_in=interest_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interests", response_model=list[schemas_credit.CreditInterest])
async def api_get_credit_interests(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all interest payments.
    """
    try:
        return crud_credit.get_credit_interests(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
