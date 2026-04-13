from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas import rental as schemas_rental
from app.crud import rental as crud_rental
from app.models.employee import Credential

router = APIRouter()

# ========== Real Estate ==========

@router.post("/real-estate/create", response_model=schemas_rental.RealEstate)
async def api_create_real_estate(
    obj_in: schemas_rental.RealEstateCreate,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Thêm mới Bất Động Sản.
    """
    try:
        return crud_rental.create_real_estate(db, obj_in=obj_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/real-estate/", response_model=list[schemas_rental.RealEstate])
async def api_get_real_estates(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Lấy danh sách Bất Động Sản.
    """
    try:
        return crud_rental.get_real_estates(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/real-estate/{real_estate_id}", response_model=schemas_rental.RealEstate)
async def api_get_real_estate_by_id(
    real_estate_id: str,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Lấy thông tin Bất Động Sản theo Mã BĐS.
    """
    try:
        result = crud_rental.get_real_estate_by_id(db, real_estate_id=real_estate_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy BĐS với mã: {real_estate_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Rental Customer ==========

@router.post("/customer/create", response_model=schemas_rental.RentalCustomer)
async def api_create_rental_customer(
    obj_in: schemas_rental.RentalCustomerCreate,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Thêm mới Khách Hàng Thuê.
    """
    try:
        return crud_rental.create_rental_customer(db, obj_in=obj_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/", response_model=list[schemas_rental.RentalCustomer])
async def api_get_rental_customers(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Lấy danh sách Khách Hàng Thuê.
    """
    try:
        return crud_rental.get_rental_customers(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Rental Contract ==========

@router.post("/create", response_model=schemas_rental.Rental)
async def api_create_rental(
    obj_in: schemas_rental.RentalCreate,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Thêm mới Hợp Đồng Thuê.
    """
    try:
        return crud_rental.create_rental(db, obj_in=obj_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[schemas_rental.Rental])
async def api_get_rentals(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Lấy danh sách Hợp Đồng Thuê.
    """
    try:
        return crud_rental.get_rentals(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
