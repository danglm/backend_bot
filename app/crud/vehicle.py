from sqlalchemy.orm import Session
from app.models.vehicle import Vehicle, VehicleActivityLog
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleActivityLogCreate

def create_vehicle_activity_log(db: Session, obj_in: VehicleActivityLogCreate):
    db_obj = VehicleActivityLog(
        vehicle_id=obj_in.vehicle_id,
        telegram_username=obj_in.telegram_username,
        action=obj_in.action
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_vehicle(db: Session, vehicle_id: str):
    return db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

def get_vehicle_by_license_plate(db: Session, license_plate: str):
    return db.query(Vehicle).filter(Vehicle.license_plate == license_plate).first()

def get_vehicles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Vehicle).offset(skip).limit(limit).all()

def create_vehicle(db: Session, vehicle: VehicleCreate):
    db_vehicle = Vehicle(
        license_plate=vehicle.license_plate,
        vehicle_type=vehicle.vehicle_type,
        brand=vehicle.brand,
        model=vehicle.model,
        color=vehicle.color,
        owner_name=vehicle.owner_name,
        status=vehicle.status
    )
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

def update_vehicle(db: Session, vehicle_id: str, vehicle: VehicleUpdate):
    db_vehicle = get_vehicle(db, vehicle_id)
    if not db_vehicle:
        return None
    
    update_data = vehicle.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)
        
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

def remove_vehicle(db: Session, vehicle_id: str):
    db_vehicle = get_vehicle(db, vehicle_id)
    if not db_vehicle:
        return None
    db.delete(db_vehicle)
    db.commit()
    return db_vehicle
