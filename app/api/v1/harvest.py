from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas import harvest as schemas_harvest
from app.crud import harvest as crud_harvest
from app.models.employee import Credential
from app.models.business import AgriculturalLand, Households, DailyHarvest, SuppliesExpense
from bot.utils.logger import LogInfo
from typing import Optional
from uuid import UUID
from datetime import datetime

router = APIRouter()

@router.get("/get-agricultural-lands", response_model=list[schemas_harvest.AgriculturalLandResponse])
async def api_get_agricultural_lands(
    land_code: Optional[str] = None,
    status: Optional[str] = None,
    affiliation: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Lấy danh sách đất trồng trọt (agricultural lands).
    """
    LogInfo(f"[Harvest API] Received get-agricultural-lands request. land_code: {land_code}, status: {status}, affiliation: {affiliation}")
    try:
        lands = crud_harvest.get_agricultural_lands(
            db,
            land_code=land_code,
            status=status,
            affiliation=affiliation
        )
        LogInfo(f"[Harvest API] Found {len(lands)} agricultural lands.")
        return lands
    except Exception as e:
        LogInfo(f"[Harvest API] Error in get-agricultural-lands: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-agricultural-lands", response_model=list[schemas_harvest.AgriculturalLandResponse])
async def api_add_agricultural_lands(
    lands_in: list[schemas_harvest.AgriculturalLandCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Thêm mới danh sách đất trồng trọt (bulk).
    """
    LogInfo(f"[Harvest API] Received add-agricultural-lands request. Total: {len(lands_in)}")
    try:
        # Check for duplicates in the input list itself
        input_codes = [l.land_code for l in lands_in if l.land_code]
        if len(input_codes) != len(set(input_codes)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate land_code found in the request input."
            )

        # Check if any land_code already exists in the database
        existing_lands = db.query(AgriculturalLand).filter(AgriculturalLand.land_code.in_(input_codes)).all()
        if existing_lands:
            existing_codes = [l.land_code for l in existing_lands]
            raise HTTPException(
                status_code=400,
                detail=f"Đất trồng trọt với mã {existing_codes} đã tồn tại trong hệ thống."
            )

        created_lands = []
        for land_in in lands_in:
            new_land = crud_harvest.create_agricultural_land(db, obj_in=land_in)
            created_lands.append(new_land)

        LogInfo(f"[Harvest API] Successfully added {len(created_lands)} agricultural lands.")
        return created_lands
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in add-agricultural-lands: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-agricultural-lands", response_model=list[schemas_harvest.AgriculturalLandResponse])
async def api_update_agricultural_lands(
    lands_in: list[schemas_harvest.AgriculturalLandUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Cập nhật danh sách đất trồng trọt (bulk).
    """
    LogInfo(f"[Harvest API] Received update-agricultural-lands request. Total: {len(lands_in)}")
    try:
        # Check for duplicates in the input list itself
        input_ids = [l.id for l in lands_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        # Check if all land IDs exist in the database
        existing_lands = db.query(AgriculturalLand).filter(AgriculturalLand.id.in_(input_ids)).all()
        existing_ids = {l.id for l in existing_lands}

        missing_ids = [lid for lid in input_ids if lid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Agricultural lands with IDs {missing_ids} not found in the database."
            )

        updated_lands = []
        for land_in in lands_in:
            updated_land = crud_harvest.update_agricultural_land(db, land_uuid=land_in.id, obj_in=land_in)
            if updated_land:
                updated_lands.append(updated_land)

        LogInfo(f"[Harvest API] Successfully updated {len(updated_lands)} agricultural lands.")
        return updated_lands
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in update-agricultural-lands: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-agricultural-lands", response_model=list[schemas_harvest.AgriculturalLandResponse])
async def api_delete_agricultural_lands(
    land_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Xóa danh sách đất trồng trọt (bulk).
    """
    LogInfo(f"[Harvest API] Received delete-agricultural-lands request. Total: {len(land_ids)}")
    try:
        # Check for duplicates in the input list itself
        if len(land_ids) != len(set(land_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        # Check if all land IDs exist in the database
        existing_lands = db.query(AgriculturalLand).filter(AgriculturalLand.id.in_(land_ids)).all()
        existing_ids = {l.id for l in existing_lands}

        missing_ids = [lid for lid in land_ids if lid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Agricultural lands with IDs {missing_ids} not found in the database."
            )

        deleted_lands = []
        for land_uuid in land_ids:
            deleted_land = crud_harvest.delete_agricultural_land(db, land_uuid=land_uuid)
            if deleted_land:
                deleted_lands.append(deleted_land)

        LogInfo(f"[Harvest API] Successfully deleted {len(deleted_lands)} agricultural lands.")
        return deleted_lands
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in delete-agricultural-lands: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-households", response_model=list[schemas_harvest.HouseholdResponse])
async def api_get_households(
    household_code: Optional[str] = None,
    purchase_code: Optional[str] = None,
    status: Optional[str] = None,
    has_purchase_code: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Lấy danh sách hộ dân (households).
    """
    LogInfo(f"[Harvest API] Received get-households request. household_code: {household_code}, purchase_code: {purchase_code}, status: {status}, has_purchase_code: {has_purchase_code}")
    try:
        households = crud_harvest.get_households(
            db,
            household_code=household_code,
            purchase_code=purchase_code,
            status=status,
            has_purchase_code=has_purchase_code
        )
        LogInfo(f"[Harvest API] Found {len(households)} households.")
        return households
    except Exception as e:
        LogInfo(f"[Harvest API] Error in get-households: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-households", response_model=list[schemas_harvest.HouseholdResponse])
async def api_add_households(
    households_in: list[schemas_harvest.HouseholdCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Thêm mới danh sách hộ dân (bulk).
    """
    LogInfo(f"[Harvest API] Received add-households request. Total: {len(households_in)}")
    try:
        # Check duplicate household_code/purchase_code in input
        input_h_codes = [h.household_code for h in households_in if h.household_code]
        if len(input_h_codes) != len(set(input_h_codes)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate household_code found in the request input."
            )

        input_p_codes = [h.purchase_code.strip() for h in households_in if h.purchase_code and h.purchase_code.strip()]
        if len(input_p_codes) != len(set(input_p_codes)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate purchase_code found in the request input."
            )

        # Check existing codes in database
        existing_h = db.query(Households).filter(Households.household_code.in_(input_h_codes)).all()
        if existing_h:
            existing_codes = [h.household_code for h in existing_h]
            raise HTTPException(
                status_code=400,
                detail=f"Hộ dân với mã {existing_codes} đã tồn tại trong hệ thống."
            )

        if input_p_codes:
            existing_p = db.query(Households).filter(Households.purchase_code.in_(input_p_codes)).all()
            if existing_p:
                existing_codes = [h.purchase_code for h in existing_p]
                raise HTTPException(
                    status_code=400,
                    detail=f"Hộ thu mua với mã {existing_codes} đã tồn tại trong hệ thống."
                )

        created_households = []
        for h_in in households_in:
            new_h = crud_harvest.create_household(db, obj_in=h_in)
            created_households.append(new_h)

        LogInfo(f"[Harvest API] Successfully added {len(created_households)} households.")
        return created_households
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in add-households: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-households", response_model=list[schemas_harvest.HouseholdResponse])
async def api_update_households(
    households_in: list[schemas_harvest.HouseholdUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Cập nhật danh sách hộ dân (bulk).
    """
    LogInfo(f"[Harvest API] Received update-households request. Total: {len(households_in)}")
    try:
        # Check duplicate IDs in input
        input_ids = [h.id for h in households_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        # Check all IDs exist in database
        existing_households = db.query(Households).filter(Households.id.in_(input_ids)).all()
        existing_ids = {h.id for h in existing_households}

        missing_ids = [hid for hid in input_ids if hid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Households with IDs {missing_ids} not found in the database."
            )

        updated_households = []
        for h_in in households_in:
            updated_h = crud_harvest.update_household(db, household_uuid=h_in.id, obj_in=h_in)
            if updated_h:
                updated_households.append(updated_h)

        LogInfo(f"[Harvest API] Successfully updated {len(updated_households)} households.")
        return updated_households
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in update-households: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-households", response_model=list[schemas_harvest.HouseholdResponse])
async def api_delete_households(
    household_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Xóa danh sách hộ dân (bulk).
    """
    LogInfo(f"[Harvest API] Received delete-households request. Total: {len(household_ids)}")
    try:
        # Check duplicate IDs in input
        if len(household_ids) != len(set(household_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        # Check all IDs exist in database
        existing_households = db.query(Households).filter(Households.id.in_(household_ids)).all()
        existing_ids = {h.id for h in existing_households}

        missing_ids = [hid for hid in household_ids if hid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Households with IDs {missing_ids} not found in the database."
            )

        deleted_households = []
        for h_uuid in household_ids:
            deleted_h = crud_harvest.delete_household(db, household_uuid=h_uuid)
            if deleted_h:
                deleted_households.append(deleted_h)

        LogInfo(f"[Harvest API] Successfully deleted {len(deleted_households)} households.")
        return deleted_households
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in delete-households: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-daily-harvests", response_model=list[schemas_harvest.DailyHarvestResponse])
async def api_get_daily_harvests(
    household_code: Optional[str] = None,
    land_code: Optional[str] = None,
    crop_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Lấy danh sách lịch sử thu hoạch (daily harvests) kèm tên khách hàng.
    """
    LogInfo(f"[Harvest API] Received get-daily-harvests request. household_code: {household_code}, land_code: {land_code}, crop_type: {crop_type}, start_date: {start_date}, end_date: {end_date}")

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
        harvests = crud_harvest.get_daily_harvests_detailed(
            db,
            household_code=household_code,
            land_code=land_code,
            crop_type=crop_type,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        LogInfo(f"[Harvest API] Found {len(harvests)} daily harvests.")
        return harvests
    except Exception as e:
        LogInfo(f"[Harvest API] Error in get-daily-harvests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-daily-harvests", response_model=list[schemas_harvest.DailyHarvestResponse])
async def api_add_daily_harvests(
    harvests_in: list[schemas_harvest.DailyHarvestCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Thêm mới danh sách lịch sử thu hoạch (bulk).
    """
    LogInfo(f"[Harvest API] Received add-daily-harvests request. Total: {len(harvests_in)}")
    try:
        # Validate household codes and land codes exist in database
        hh_codes = list({h.household_code for h in harvests_in if h.household_code})
        if hh_codes:
            existing_hh = db.query(Households).filter(Households.household_code.in_(hh_codes)).all()
            existing_hh_codes = {h.household_code for h in existing_hh}
            missing_hh = [c for c in hh_codes if c not in existing_hh_codes]
            if missing_hh:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy hộ dân với mã: {missing_hh}"
                )

        land_codes = list({h.land_code for h in harvests_in if h.land_code})
        if land_codes:
            existing_lands = db.query(AgriculturalLand).filter(AgriculturalLand.land_code.in_(land_codes)).all()
            existing_land_codes = {l.land_code for l in existing_lands}
            missing_lands = [c for c in land_codes if c not in existing_land_codes]
            if missing_lands:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy đất trồng trọt với mã: {missing_lands}"
                )

        created_harvests = []
        for h_in in harvests_in:
            new_h = crud_harvest.create_daily_harvest(db, obj_in=h_in)
            created_harvests.append(new_h)

        # Retrieve detailed structures with household names
        created_ids = [h.id for h in created_harvests]
        detailed_harvests = crud_harvest.get_daily_harvests_detailed(db)
        detailed_harvests_filtered = [h for h in detailed_harvests if h["id"] in created_ids]

        LogInfo(f"[Harvest API] Successfully added {len(created_harvests)} daily harvests.")
        return detailed_harvests_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in add-daily-harvests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-daily-harvests", response_model=list[schemas_harvest.DailyHarvestResponse])
async def api_update_daily_harvests(
    harvests_in: list[schemas_harvest.DailyHarvestUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Cập nhật danh sách lịch sử thu hoạch (bulk).
    """
    LogInfo(f"[Harvest API] Received update-daily-harvests request. Total: {len(harvests_in)}")
    try:
        # Check duplicate IDs in input
        input_ids = [h.id for h in harvests_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        # Check all IDs exist in database
        existing_harvests = db.query(DailyHarvest).filter(DailyHarvest.id.in_(input_ids)).all()
        existing_ids = {h.id for h in existing_harvests}

        missing_ids = [hid for hid in input_ids if hid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Daily harvests with IDs {missing_ids} not found in the database."
            )

        # Validate household codes and land codes exist in database
        hh_codes = list({h.household_code for h in harvests_in if h.household_code})
        if hh_codes:
            existing_hh = db.query(Households).filter(Households.household_code.in_(hh_codes)).all()
            existing_hh_codes = {h.household_code for h in existing_hh}
            missing_hh = [c for c in hh_codes if c not in existing_hh_codes]
            if missing_hh:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy hộ dân với mã: {missing_hh}"
                )

        land_codes = list({h.land_code for h in harvests_in if h.land_code})
        if land_codes:
            existing_lands = db.query(AgriculturalLand).filter(AgriculturalLand.land_code.in_(land_codes)).all()
            existing_land_codes = {l.land_code for l in existing_lands}
            missing_lands = [c for c in land_codes if c not in existing_land_codes]
            if missing_lands:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy đất trồng trọt với mã: {missing_lands}"
                )

        updated_harvests = []
        for h_in in harvests_in:
            updated_h = crud_harvest.update_daily_harvest(db, harvest_uuid=h_in.id, obj_in=h_in)
            if updated_h:
                updated_harvests.append(updated_h)

        # Retrieve detailed structures with household names
        updated_ids = [h.id for h in updated_harvests]
        detailed_harvests = crud_harvest.get_daily_harvests_detailed(db)
        detailed_harvests_filtered = [h for h in detailed_harvests if h["id"] in updated_ids]

        LogInfo(f"[Harvest API] Successfully updated {len(updated_harvests)} daily harvests.")
        return detailed_harvests_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in update-daily-harvests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-daily-harvests", response_model=list[schemas_harvest.DailyHarvestResponse])
async def api_delete_daily_harvests(
    harvest_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Xóa danh sách lịch sử thu hoạch (bulk).
    """
    LogInfo(f"[Harvest API] Received delete-daily-harvests request. Total: {len(harvest_ids)}")
    try:
        # Check duplicate IDs in input
        if len(harvest_ids) != len(set(harvest_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        # Check all IDs exist in database
        existing_harvests = db.query(DailyHarvest).filter(DailyHarvest.id.in_(harvest_ids)).all()
        existing_ids = {h.id for h in existing_harvests}

        missing_ids = [hid for hid in harvest_ids if hid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Daily harvests with IDs {missing_ids} not found in the database."
            )

        # Retrieve details before deletion to return them
        detailed_harvests = crud_harvest.get_daily_harvests_detailed(db)
        detailed_harvests_filtered = [h for h in detailed_harvests if h["id"] in existing_ids]

        for h_uuid in harvest_ids:
            crud_harvest.delete_daily_harvest(db, harvest_uuid=h_uuid)

        LogInfo(f"[Harvest API] Successfully deleted {len(harvest_ids)} daily harvests.")
        return detailed_harvests_filtered
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in delete-daily-harvests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-supplies-expenses", response_model=list[schemas_harvest.SuppliesExpenseResponse])
async def api_get_supplies_expenses(
    land_code: Optional[str] = None,
    crop_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Lấy danh sách chi phí vật tư (supplies expenses).
    """
    LogInfo(f"[Harvest API] Received get-supplies-expenses request. land_code: {land_code}, crop_type: {crop_type}, start_date: {start_date}, end_date: {end_date}")
    
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
        expenses = crud_harvest.get_supplies_expenses(
            db,
            land_code=land_code,
            crop_type=crop_type,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        LogInfo(f"[Harvest API] Found {len(expenses)} supplies expenses.")
        return expenses
    except Exception as e:
        LogInfo(f"[Harvest API] Error in get-supplies-expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-supplies-expenses", response_model=list[schemas_harvest.SuppliesExpenseResponse])
async def api_add_supplies_expenses(
    expenses_in: list[schemas_harvest.SuppliesExpenseCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Thêm mới danh sách chi phí vật tư (bulk).
    """
    LogInfo(f"[Harvest API] Received add-supplies-expenses request. Total: {len(expenses_in)}")
    try:
        # Validate land codes exist if provided
        land_codes = list({h.land_code for h in expenses_in if h.land_code})
        if land_codes:
            existing_lands = db.query(AgriculturalLand).filter(AgriculturalLand.land_code.in_(land_codes)).all()
            existing_land_codes = {l.land_code for l in existing_lands}
            missing_lands = [c for c in land_codes if c not in existing_land_codes]
            if missing_lands:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy đất trồng trọt với mã: {missing_lands}"
                )

        created_expenses = []
        for e_in in expenses_in:
            new_expense = crud_harvest.create_supplies_expense(db, obj_in=e_in)
            created_expenses.append(new_expense)

        LogInfo(f"[Harvest API] Successfully added {len(created_expenses)} supplies expenses.")
        return created_expenses
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in add-supplies-expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-supplies-expenses", response_model=list[schemas_harvest.SuppliesExpenseResponse])
async def api_update_supplies_expenses(
    expenses_in: list[schemas_harvest.SuppliesExpenseUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Cập nhật danh sách chi phí vật tư (bulk).
    """
    LogInfo(f"[Harvest API] Received update-supplies-expenses request. Total: {len(expenses_in)}")
    try:
        # Check duplicate IDs in input
        input_ids = [h.id for h in expenses_in]
        if len(input_ids) != len(set(input_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        # Check all IDs exist in database
        existing_expenses = db.query(SuppliesExpense).filter(SuppliesExpense.id.in_(input_ids)).all()
        existing_ids = {h.id for h in existing_expenses}

        missing_ids = [eid for eid in input_ids if eid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Supplies expenses with IDs {missing_ids} not found in the database."
            )

        # Validate land codes exist if provided
        land_codes = list({h.land_code for h in expenses_in if h.land_code})
        if land_codes:
            existing_lands = db.query(AgriculturalLand).filter(AgriculturalLand.land_code.in_(land_codes)).all()
            existing_land_codes = {l.land_code for l in existing_lands}
            missing_lands = [c for c in land_codes if c not in existing_land_codes]
            if missing_lands:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy đất trồng trọt với mã: {missing_lands}"
                )

        updated_expenses = []
        for e_in in expenses_in:
            updated_expense = crud_harvest.update_supplies_expense(db, expense_uuid=e_in.id, obj_in=e_in)
            if updated_expense:
                updated_expenses.append(updated_expense)

        LogInfo(f"[Harvest API] Successfully updated {len(updated_expenses)} supplies expenses.")
        return updated_expenses
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in update-supplies-expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-supplies-expenses", response_model=list[schemas_harvest.SuppliesExpenseResponse])
async def api_delete_supplies_expenses(
    expense_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Xóa danh sách chi phí vật tư (bulk).
    """
    LogInfo(f"[Harvest API] Received delete-supplies-expenses request. Total: {len(expense_ids)}")
    try:
        # Check duplicate IDs in input
        if len(expense_ids) != len(set(expense_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate IDs found in the request input."
            )

        # Check all IDs exist in database
        existing_expenses = db.query(SuppliesExpense).filter(SuppliesExpense.id.in_(expense_ids)).all()
        existing_ids = {h.id for h in existing_expenses}

        missing_ids = [eid for eid in expense_ids if eid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Supplies expenses with IDs {missing_ids} not found in the database."
            )

        deleted_expenses = []
        for e_uuid in expense_ids:
            deleted_expense = crud_harvest.delete_supplies_expense(db, expense_uuid=e_uuid)
            if deleted_expense:
                deleted_expenses.append(deleted_expense)

        LogInfo(f"[Harvest API] Successfully deleted {len(deleted_expenses)} supplies expenses.")
        return deleted_expenses
    except HTTPException as he:
        raise he
    except Exception as e:
        LogInfo(f"[Harvest API] Error in delete-supplies-expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))
