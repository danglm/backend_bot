from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.models.business import AgriculturalLand, Households, DailyHarvest, SuppliesExpense
from app.schemas.harvest import AgriculturalLandCreate, AgriculturalLandUpdate, HouseholdCreate, HouseholdUpdate, DailyHarvestCreate, DailyHarvestUpdate, SuppliesExpenseCreate, SuppliesExpenseUpdate
from uuid import UUID

def get_agricultural_lands(
    db: Session,
    land_code: Optional[str] = None,
    status: Optional[str] = None,
    affiliation: Optional[str] = None,
    crop_type: Optional[str] = None
):
    query = db.query(AgriculturalLand)
    if land_code is not None:
        query = query.filter(AgriculturalLand.land_code == land_code)
    if status is not None:
        query = query.filter(AgriculturalLand.status == status)
    if affiliation is not None:
        query = query.filter(AgriculturalLand.affiliation == affiliation)
    if crop_type is not None:
        query = query.filter(AgriculturalLand.crop_type == crop_type)
    return query.all()

def create_agricultural_land(db: Session, obj_in: AgriculturalLandCreate):
    db_obj = AgriculturalLand(
        land_code=obj_in.land_code,
        land_name=obj_in.land_name,
        address=obj_in.address,
        total_area=obj_in.total_area,
        harvest_area=obj_in.harvest_area,
        empty_area=obj_in.empty_area,
        planting_area=obj_in.planting_area,
        harvesting_trees=obj_in.harvesting_trees,
        planting_trees=obj_in.planting_trees,
        affiliation=obj_in.affiliation,
        crop_type=obj_in.crop_type,
        status=obj_in.status
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_agricultural_land(db: Session, land_uuid: UUID, obj_in: AgriculturalLandUpdate) -> Optional[AgriculturalLand]:
    db_obj = db.query(AgriculturalLand).filter(AgriculturalLand.id == land_uuid).first()
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

def delete_agricultural_land(db: Session, land_uuid: UUID) -> Optional[AgriculturalLand]:
    db_obj = db.query(AgriculturalLand).filter(AgriculturalLand.id == land_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj

def get_households(
    db: Session,
    household_code: Optional[str] = None,
    purchase_code: Optional[str] = None,
    status: Optional[str] = None,
    has_purchase_code: Optional[bool] = None
):
    query = db.query(Households)
    if household_code is not None:
        query = query.filter(Households.household_code == household_code)
    if purchase_code is not None:
        query = query.filter(Households.purchase_code == purchase_code)
    if status is not None:
        query = query.filter(Households.status == status)
    if has_purchase_code is not None:
        if has_purchase_code:
            query = query.filter(Households.purchase_code.isnot(None), Households.purchase_code != "")
        else:
            query = query.filter((Households.purchase_code.is_(None)) | (Households.purchase_code == ""))
    return query.all()

def create_household(db: Session, obj_in: HouseholdCreate):
    p_code = obj_in.purchase_code
    if p_code is not None:
        p_code = p_code.strip()
        if not p_code:
            p_code = None

    db_obj = Households(
        household_code=obj_in.household_code,
        purchase_code=p_code,
        land_code=obj_in.land_code,
        fullname=obj_in.fullname,
        username=obj_in.username,
        telegram_group=obj_in.telegram_group,
        phone=obj_in.phone,
        address=obj_in.address,
        total_debt=obj_in.total_debt,
        tapping_price=obj_in.tapping_price,
        labor_price=obj_in.labor_price,
        bank_account=obj_in.bank_account,
        bank_name=obj_in.bank_name,
        status=obj_in.status
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_household(db: Session, household_uuid: UUID, obj_in: HouseholdUpdate) -> Optional[Households]:
    db_obj = db.query(Households).filter(Households.id == household_uuid).first()
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]

    if "purchase_code" in update_data:
        p_code = update_data["purchase_code"]
        if p_code is not None:
            p_code = p_code.strip()
            if not p_code:
                p_code = None
        update_data["purchase_code"] = p_code

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_household(db: Session, household_uuid: UUID) -> Optional[Households]:
    db_obj = db.query(Households).filter(Households.id == household_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj

def get_daily_harvests_detailed(
    db: Session,
    household_code: Optional[str] = None,
    land_code: Optional[str] = None,
    crop_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> list[dict]:
    query = db.query(
        DailyHarvest,
        Households.fullname.label("household_name")
    ).outerjoin(
        Households, DailyHarvest.household_code == Households.household_code
    )

    if household_code is not None:
        query = query.filter(DailyHarvest.household_code == household_code)
    if land_code is not None:
        query = query.filter(DailyHarvest.land_code == land_code)
    if crop_type is not None:
        query = query.filter(DailyHarvest.crop_type == crop_type)
    if start_date is not None:
        query = query.filter(DailyHarvest.day >= start_date)
    if end_date is not None:
        query = query.filter(DailyHarvest.day <= end_date)

    results = query.all()

    data = []
    for dh, household_name in results:
        data.append({
            "id": dh.id,
            "day": dh.day,
            "household_code": dh.household_code,
            "household_name": household_name,
            "land_code": dh.land_code,
            "tree_count": dh.tree_count,
            "harvest_weight": dh.harvest_weight,
            "unit_price": dh.unit_price,
            "total_amount": dh.total_amount,
            "crop_type": dh.crop_type,
            "created_at": dh.created_at
        })
    return data

def create_daily_harvest(db: Session, obj_in: DailyHarvestCreate):
    db_obj = DailyHarvest(
        day=obj_in.day,
        household_code=obj_in.household_code,
        land_code=obj_in.land_code,
        tree_count=obj_in.tree_count,
        harvest_weight=obj_in.harvest_weight,
        unit_price=obj_in.unit_price,
        total_amount=obj_in.total_amount,
        crop_type=obj_in.crop_type
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_daily_harvest(db: Session, harvest_uuid: UUID, obj_in: DailyHarvestUpdate) -> Optional[DailyHarvest]:
    db_obj = db.query(DailyHarvest).filter(DailyHarvest.id == harvest_uuid).first()
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

def delete_daily_harvest(db: Session, harvest_uuid: UUID) -> Optional[DailyHarvest]:
    db_obj = db.query(DailyHarvest).filter(DailyHarvest.id == harvest_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def get_supplies_expenses(
    db: Session,
    land_code: Optional[str] = None,
    crop_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    query = db.query(SuppliesExpense)
    if land_code is not None:
        query = query.filter(SuppliesExpense.land_code == land_code)
    if crop_type is not None:
        query = query.filter(SuppliesExpense.crop_type == crop_type)
    if start_date is not None:
        query = query.filter(SuppliesExpense.day >= start_date)
    if end_date is not None:
        query = query.filter(SuppliesExpense.day <= end_date)
    return query.all()


def create_supplies_expense(db: Session, obj_in: SuppliesExpenseCreate):
    qty = obj_in.quantity or 0.0
    price = obj_in.unit_price or 0.0
    total_amount = qty * price

    db_obj = SuppliesExpense(
        day=obj_in.day,
        land_code=obj_in.land_code,
        supplies_name=obj_in.supplies_name,
        supplier=obj_in.supplier,
        quantity=qty,
        unit=obj_in.unit,
        unit_price=price,
        total_amount=total_amount,
        purpose=obj_in.purpose,
        crop_type=obj_in.crop_type or "chung",
        buyer=obj_in.buyer,
        notes=obj_in.notes
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_supplies_expense(db: Session, expense_uuid: UUID, obj_in: SuppliesExpenseUpdate) -> Optional[SuppliesExpense]:
    db_obj = db.query(SuppliesExpense).filter(SuppliesExpense.id == expense_uuid).first()
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]

    qty = update_data.get("quantity", db_obj.quantity) or 0.0
    price = update_data.get("unit_price", db_obj.unit_price) or 0.0
    update_data["total_amount"] = qty * price

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_supplies_expense(db: Session, expense_uuid: UUID) -> Optional[SuppliesExpense]:
    db_obj = db.query(SuppliesExpense).filter(SuppliesExpense.id == expense_uuid).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj
