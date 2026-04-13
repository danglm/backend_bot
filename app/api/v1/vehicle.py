from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas import vehicle as schemas_vehicle
from app.crud import vehicle as crud_vehicle
from app.models.employee import Credential

router = APIRouter()

@router.post("/add_vehicle", response_model=schemas_vehicle.Vehicle)
async def api_add_vehicle(
    vehicle_in: schemas_vehicle.VehicleCreate,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Add a new vehicle.
    """
    try:
        # Check if license plate already exists
        db_vehicle = crud_vehicle.get_vehicle_by_license_plate(db, license_plate=vehicle_in.license_plate)
        if db_vehicle:
            raise HTTPException(
                status_code=400,
                detail="Vehicle with this license plate already exists."
            )
        return crud_vehicle.create_vehicle(db, vehicle=vehicle_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_vehicles", response_model=list[schemas_vehicle.Vehicle])
async def api_get_vehicles(
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all vehicles.
    """
    try:
        return crud_vehicle.get_vehicles(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
