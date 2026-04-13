from sqlalchemy.orm import Session
from app.models.device import (
    Smartphone, Laptop, SimCard, Application, DeviceAssignment, InstalledApp
)
from app.schemas.device import (
    SmartphoneCreate, SmartphoneUpdate,
    LaptopCreate, LaptopUpdate,
    SimCardCreate, SimCardUpdate,
    ApplicationCreate, ApplicationUpdate,
    DeviceAssignmentCreate, DeviceAssignmentUpdate,
    InstalledAppCreate,
)


# ===================== SMARTPHONE CRUD =====================

def get_smartphone(db: Session, smartphone_id: str):
    return db.query(Smartphone).filter(Smartphone.id == smartphone_id).first()


def get_smartphone_by_imei(db: Session, imei: str):
    return db.query(Smartphone).filter(Smartphone.imei_1 == imei).first()


def get_smartphones(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Smartphone).offset(skip).limit(limit).all()


def get_smartphones_by_status(db: Session, status: str):
    return db.query(Smartphone).filter(Smartphone.status == status).all()


def get_smartphones_by_brand(db: Session, brand: str):
    return db.query(Smartphone).filter(Smartphone.brand == brand).all()


def create_smartphone(db: Session, smartphone: SmartphoneCreate):
    db_obj = Smartphone(**smartphone.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_smartphone(db: Session, smartphone_id: str, smartphone: SmartphoneUpdate):
    db_obj = get_smartphone(db, smartphone_id)
    if not db_obj:
        return None
    for field, value in smartphone.dict(exclude_unset=True).items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_smartphone(db: Session, smartphone_id: str):
    db_obj = get_smartphone(db, smartphone_id)
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


# ===================== LAPTOP CRUD =====================

def get_laptop(db: Session, laptop_id: str):
    return db.query(Laptop).filter(Laptop.id == laptop_id).first()


def get_laptops(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Laptop).offset(skip).limit(limit).all()


def get_laptops_by_status(db: Session, status: str):
    return db.query(Laptop).filter(Laptop.status == status).all()


def create_laptop(db: Session, laptop: LaptopCreate):
    db_obj = Laptop(**laptop.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_laptop(db: Session, laptop_id: str, laptop: LaptopUpdate):
    db_obj = get_laptop(db, laptop_id)
    if not db_obj:
        return None
    for field, value in laptop.dict(exclude_unset=True).items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_laptop(db: Session, laptop_id: str):
    db_obj = get_laptop(db, laptop_id)
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


# ===================== SIM CARD CRUD =====================

def get_sim_card(db: Session, sim_card_id: str):
    return db.query(SimCard).filter(SimCard.id == sim_card_id).first()


def get_sim_card_by_phone(db: Session, phone_number: str):
    return db.query(SimCard).filter(SimCard.phone_number == phone_number).first()


def get_sim_cards(db: Session, skip: int = 0, limit: int = 100):
    return db.query(SimCard).offset(skip).limit(limit).all()


def get_sim_cards_by_status(db: Session, status: str):
    return db.query(SimCard).filter(SimCard.status == status).all()


def get_sim_cards_by_smartphone(db: Session, smartphone_id: str):
    return db.query(SimCard).filter(SimCard.smartphone_id == smartphone_id).all()


def create_sim_card(db: Session, sim_card: SimCardCreate):
    db_obj = SimCard(**sim_card.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_sim_card(db: Session, sim_card_id: str, sim_card: SimCardUpdate):
    db_obj = get_sim_card(db, sim_card_id)
    if not db_obj:
        return None
    for field, value in sim_card.dict(exclude_unset=True).items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_sim_card(db: Session, sim_card_id: str):
    db_obj = get_sim_card(db, sim_card_id)
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


# ===================== APPLICATION CRUD =====================

def get_application(db: Session, application_id: str):
    return db.query(Application).filter(Application.id == application_id).first()


def get_applications(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Application).offset(skip).limit(limit).all()


def get_applications_by_status(db: Session, status: str):
    return db.query(Application).filter(Application.status == status).all()


def get_applications_by_smartphone(db: Session, smartphone_id: str):
    return db.query(Application).filter(Application.smartphone_id == smartphone_id).all()


def create_application(db: Session, application: ApplicationCreate):
    db_obj = Application(**application.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_application(db: Session, application_id: str, application: ApplicationUpdate):
    db_obj = get_application(db, application_id)
    if not db_obj:
        return None
    for field, value in application.dict(exclude_unset=True).items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_application(db: Session, application_id: str):
    db_obj = get_application(db, application_id)
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


# ===================== DEVICE ASSIGNMENT CRUD =====================

def get_device_assignment(db: Session, assignment_id: str):
    return db.query(DeviceAssignment).filter(DeviceAssignment.id == assignment_id).first()


def get_device_assignments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(DeviceAssignment).offset(skip).limit(limit).all()


def get_assignments_by_username(db: Session, username: str):
    return db.query(DeviceAssignment).filter(DeviceAssignment.username == username).all()


def get_assignments_by_device(db: Session, device_id: str):
    return db.query(DeviceAssignment).filter(DeviceAssignment.device_id == device_id).all()


def create_device_assignment(db: Session, assignment: DeviceAssignmentCreate):
    db_obj = DeviceAssignment(**assignment.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_device_assignment(db: Session, assignment_id: str, assignment: DeviceAssignmentUpdate):
    db_obj = get_device_assignment(db, assignment_id)
    if not db_obj:
        return None
    for field, value in assignment.dict(exclude_unset=True).items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_device_assignment(db: Session, assignment_id: str):
    db_obj = get_device_assignment(db, assignment_id)
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


# ===================== INSTALLED APP CRUD =====================

def get_installed_apps_by_device(db: Session, device_id: str):
    return db.query(InstalledApp).filter(InstalledApp.device_id == device_id).all()


def get_installed_apps_by_app(db: Session, app_id: str):
    return db.query(InstalledApp).filter(InstalledApp.app_id == app_id).all()


def create_installed_app(db: Session, installed_app: InstalledAppCreate):
    db_obj = InstalledApp(**installed_app.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_installed_app(db: Session, device_id: str, app_id: str):
    db_obj = db.query(InstalledApp).filter(
        InstalledApp.device_id == device_id,
        InstalledApp.app_id == app_id
    ).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj
