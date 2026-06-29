from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.api.deps import get_db, get_current_user
from app.schemas import vehicle as schemas_vehicle
from app.crud import vehicle as crud_vehicle
from app.models.employee import Credential
from app.models.vehicle import Vehicle

router = APIRouter()

@router.get("/get-vehicles", response_model=list[schemas_vehicle.Vehicle])
async def api_get_vehicles(
    license_plate: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Get vehicles.
    """
    try:
        return crud_vehicle.get_vehicles(db, license_plate=license_plate, status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-vehicles", response_model=List[schemas_vehicle.Vehicle])
async def api_add_vehicles(
    vehicles_in: List[schemas_vehicle.VehicleCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Add a list of new vehicles.
    """
    created_vehicles = []
    try:
        for vehicle_in in vehicles_in:
            # 1. If ID is provided, check if it already exists
            import uuid
            new_id = vehicle_in.id if vehicle_in.id else uuid.uuid4()
            if vehicle_in.id:
                existing_id = db.query(Vehicle).filter(Vehicle.id == vehicle_in.id).first()
                if existing_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Xe với mã '{vehicle_in.id}' đã tồn tại trong hệ thống."
                    )
            
            # 2. Check duplicate license plate
            if vehicle_in.license_plate:
                existing_plate = db.query(Vehicle).filter(Vehicle.license_plate == vehicle_in.license_plate).first()
                if existing_plate:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Biển số xe '{vehicle_in.license_plate}' đã tồn tại trong hệ thống."
                    )

            # Create vehicle db object
            vehicle_data = vehicle_in.dict()
            vehicle_data.pop("id", None)
            db_obj = Vehicle(
                id=new_id,
                **vehicle_data
            )
            db.add(db_obj)
            created_vehicles.append(db_obj)

        db.commit()
        for v in created_vehicles:
            db.refresh(v)
        return created_vehicles
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-vehicles", response_model=List[schemas_vehicle.Vehicle])
async def api_update_vehicles(
    vehicles_in: List[schemas_vehicle.VehicleBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Update a list of vehicles.
    """
    updated_vehicles = []
    try:
        for vehicle_in in vehicles_in:
            # 1. Find by ID
            db_obj = db.query(Vehicle).filter(Vehicle.id == vehicle_in.id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy xe với mã '{vehicle_in.id}'."
                )

            # 2. Check duplicate license plate if changed
            if vehicle_in.license_plate and vehicle_in.license_plate != db_obj.license_plate:
                existing_plate = db.query(Vehicle).filter(Vehicle.license_plate == vehicle_in.license_plate).first()
                if existing_plate:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Biển số xe '{vehicle_in.license_plate}' đã tồn tại ở xe khác."
                    )

            # Update fields
            update_data = vehicle_in.dict(exclude_unset=True)
            update_data.pop("id", None)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            updated_vehicles.append(db_obj)

        db.commit()
        for v in updated_vehicles:
            db.refresh(v)
        return updated_vehicles
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-vehicles")
async def api_delete_vehicles(
    ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Delete a list of vehicles by ID.
    """
    try:
        deleted_ids = []
        for vehicle_id in ids:
            db_obj = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(vehicle_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

