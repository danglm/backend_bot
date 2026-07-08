from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from uuid import UUID
from app.api.deps import get_db, require_permission
from app.schemas import device as schemas_device
from app.crud import device as crud_device
from app.models.employee import Credential
from app.models.device import Smartphone, Tablet, Laptop, Screen, Camera, OtherDevice, DeviceAssignment

router = APIRouter()

def generate_next_smartphone_id(db: Session) -> str:
    count = db.query(Smartphone).count()
    while True:
        candidate = f"SP{str(count + 1).zfill(4)}"
        if not db.query(Smartphone).filter(Smartphone.id == candidate).first():
            return candidate
        count += 1

@router.get("/get-smartphones", response_model=List[schemas_device.Smartphone])
async def api_get_smartphones(
    classification: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Get all smartphones, optionally filtered by classification.
    """
    try:
        return crud_device.get_smartphones(db, classification=classification)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-smartphones", response_model=List[schemas_device.Smartphone])
async def api_add_smartphones(
    smartphones_in: List[schemas_device.SmartphoneCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Add a list of new smartphones.
    """
    created_phones = []
    try:
        for phone_in in smartphones_in:
            # Clean empty strings to None
            phone_data = phone_in.dict()
            for key, val in phone_data.items():
                if val == "":
                    phone_data[key] = None

            # 1. If ID is provided, check if it already exists in the database
            req_id = phone_data.get("id")
            if req_id:
                existing_id = db.query(Smartphone).filter(Smartphone.id == req_id).first()
                if existing_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Điện thoại với mã '{req_id}' đã tồn tại trong hệ thống."
                    )
                new_id = req_id
            else:
                # Generate unique ID if not provided
                new_id = generate_next_smartphone_id(db)

            # 2. Check duplicate IMEI 1
            imei_1 = phone_data.get("imei_1")
            if imei_1:
                existing_imei1 = crud_device.get_smartphone_by_imei(db, imei_1)
                if existing_imei1:
                    raise HTTPException(
                        status_code=400,
                        detail=f"IMEI 1 '{imei_1}' đã tồn tại trong hệ thống (Model: {existing_imei1.model_name})."
                    )

            # 3. Check duplicate IMEI 2
            imei_2 = phone_data.get("imei_2")
            if imei_2:
                existing_imei2 = crud_device.get_smartphone_by_imei(db, imei_2)
                if existing_imei2:
                    raise HTTPException(
                        status_code=400,
                        detail=f"IMEI 2 '{imei_2}' đã tồn tại trong hệ thống (Model: {existing_imei2.model_name})."
                    )

            # Create smartphone db object
            phone_data.pop("id", None)
            db_obj = Smartphone(
                id=new_id,
                **phone_data
            )
            db.add(db_obj)
            created_phones.append(db_obj)

        db.commit()
        for p in created_phones:
            db.refresh(p)
        return created_phones
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-smartphones", response_model=List[schemas_device.Smartphone])
async def api_update_smartphones(
    smartphones_in: List[schemas_device.SmartphoneBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Update a list of smartphones.
    """
    updated_phones = []
    try:
        for phone_in in smartphones_in:
            # Clean empty strings to None
            phone_data = phone_in.dict(exclude_unset=True)
            for key, val in phone_data.items():
                if val == "":
                    phone_data[key] = None

            # 1. Find the smartphone by ID
            req_id = phone_data.get("id")
            db_obj = db.query(Smartphone).filter(Smartphone.id == req_id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy điện thoại với mã '{req_id}'."
                )

            # 2. Check duplicate IMEI 1 (excluding itself)
            imei_1 = phone_data.get("imei_1")
            if imei_1 and imei_1 != db_obj.imei_1:
                existing_imei1 = crud_device.get_smartphone_by_imei(db, imei_1)
                if existing_imei1 and existing_imei1.id != db_obj.id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"IMEI 1 '{imei_1}' đã tồn tại ở thiết bị khác."
                    )

            # 3. Check duplicate IMEI 2 (excluding itself)
            imei_2 = phone_data.get("imei_2")
            if imei_2 and imei_2 != db_obj.imei_2:
                existing_imei2 = crud_device.get_smartphone_by_imei(db, imei_2)
                if existing_imei2 and existing_imei2.id != db_obj.id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"IMEI 2 '{imei_2}' đã tồn tại ở thiết bị khác."
                    )

            # Update fields
            phone_data.pop("id", None)
            for field, value in phone_data.items():
                setattr(db_obj, field, value)
            
            updated_phones.append(db_obj)

        db.commit()
        for p in updated_phones:
            db.refresh(p)
        return updated_phones
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-smartphones")
async def api_delete_smartphones(
    ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Delete a list of smartphones by ID.
    """
    try:
        deleted_ids = []
        for phone_id in ids:
            db_obj = db.query(Smartphone).filter(Smartphone.id == phone_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(phone_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def generate_next_tablet_id(db: Session) -> str:
    count = db.query(Tablet).count()
    while True:
        candidate = f"TAB{str(count + 1).zfill(4)}"
        if not db.query(Tablet).filter(Tablet.id == candidate).first():
            return candidate
        count += 1

# ===================== TABLET ENDPOINTS =====================
@router.get("/get-tablets", response_model=List[schemas_device.Tablet])
async def api_get_tablets(
    classification: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Get all tablets, optionally filtered by classification.
    """
    try:
        return crud_device.get_tablets(db, classification=classification)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-tablets", response_model=List[schemas_device.Tablet])
async def api_add_tablets(
    tablets_in: List[schemas_device.TabletCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Add a list of new tablets.
    """
    created_tablets = []
    try:
        for tablet_in in tablets_in:
            # Clean empty strings to None
            tablet_data = tablet_in.dict()
            for key, val in tablet_data.items():
                if val == "":
                    tablet_data[key] = None

            # 1. If ID is provided, check if it already exists in the database
            req_id = tablet_data.get("id")
            if req_id:
                existing_id = db.query(Tablet).filter(Tablet.id == req_id).first()
                if existing_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Máy tính bảng với mã '{req_id}' đã tồn tại trong hệ thống."
                    )
                new_id = req_id
            else:
                # Generate unique ID if not provided
                new_id = generate_next_tablet_id(db)

            # 2. Check duplicate IMEI 1
            imei_1 = tablet_data.get("imei_1")
            if imei_1:
                existing_imei1 = crud_device.get_tablet_by_imei(db, imei_1)
                if existing_imei1:
                    raise HTTPException(
                        status_code=400,
                        detail=f"IMEI 1 '{imei_1}' đã tồn tại trong hệ thống (Model: {existing_imei1.model_name})."
                    )

            # 3. Check duplicate IMEI 2
            imei_2 = tablet_data.get("imei_2")
            if imei_2:
                existing_imei2 = crud_device.get_tablet_by_imei(db, imei_2)
                if existing_imei2:
                    raise HTTPException(
                        status_code=400,
                        detail=f"IMEI 2 '{imei_2}' đã tồn tại trong hệ thống (Model: {existing_imei2.model_name})."
                    )

            # Create tablet db object
            tablet_data.pop("id", None)
            db_obj = Tablet(
                id=new_id,
                **tablet_data
            )
            db.add(db_obj)
            created_tablets.append(db_obj)

        db.commit()
        for t in created_tablets:
            db.refresh(t)
        return created_tablets
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-tablets", response_model=List[schemas_device.Tablet])
async def api_update_tablets(
    tablets_in: List[schemas_device.TabletBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Update a list of tablets.
    """
    updated_tablets = []
    try:
        for tablet_in in tablets_in:
            # Clean empty strings to None
            tablet_data = tablet_in.dict(exclude_unset=True)
            for key, val in tablet_data.items():
                if val == "":
                    tablet_data[key] = None

            # 1. Find the tablet by ID
            req_id = tablet_data.get("id")
            db_obj = db.query(Tablet).filter(Tablet.id == req_id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy máy tính bảng với mã '{req_id}'."
                )

            # 2. Check duplicate IMEI 1 (excluding itself)
            imei_1 = tablet_data.get("imei_1")
            if imei_1 and imei_1 != db_obj.imei_1:
                existing_imei1 = crud_device.get_tablet_by_imei(db, imei_1)
                if existing_imei1 and existing_imei1.id != db_obj.id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"IMEI 1 '{imei_1}' đã tồn tại ở thiết bị khác."
                    )

            # 3. Check duplicate IMEI 2 (excluding itself)
            imei_2 = tablet_data.get("imei_2")
            if imei_2 and imei_2 != db_obj.imei_2:
                existing_imei2 = crud_device.get_tablet_by_imei(db, imei_2)
                if existing_imei2 and existing_imei2.id != db_obj.id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"IMEI 2 '{imei_2}' đã tồn tại ở thiết bị khác."
                    )

            # Update fields
            tablet_data.pop("id", None)
            for field, value in tablet_data.items():
                setattr(db_obj, field, value)
            
            updated_tablets.append(db_obj)

        db.commit()
        for t in updated_tablets:
            db.refresh(t)
        return updated_tablets
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-tablets")
async def api_delete_tablets(
    ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Delete a list of tablets by ID.
    """
    try:
        deleted_ids = []
        for tablet_id in ids:
            db_obj = db.query(Tablet).filter(Tablet.id == tablet_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(tablet_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def generate_next_laptop_id(db: Session) -> str:
    count = db.query(Laptop).count()
    while True:
        candidate = f"LT{str(count + 1).zfill(4)}"
        if not db.query(Laptop).filter(Laptop.id == candidate).first():
            return candidate
        count += 1

def generate_next_screen_id(db: Session) -> str:
    count = db.query(Screen).count()
    while True:
        candidate = f"SC{str(count + 1).zfill(4)}"
        if not db.query(Screen).filter(Screen.id == candidate).first():
            return candidate
        count += 1

def generate_next_camera_id(db: Session) -> str:
    count = db.query(Camera).count()
    while True:
        candidate = f"CAM{str(count + 1).zfill(4)}"
        if not db.query(Camera).filter(Camera.id == candidate).first():
            return candidate
        count += 1

def generate_next_other_device_id(db: Session) -> str:
    count = db.query(OtherDevice).count()
    while True:
        candidate = f"OD{str(count + 1).zfill(4)}"
        if not db.query(OtherDevice).filter(OtherDevice.id == candidate).first():
            return candidate
        count += 1

# ===================== LAPTOP ENDPOINTS =====================
@router.get("/get-laptops", response_model=List[schemas_device.Laptop])
async def api_get_laptops(
    classification: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    try:
        return crud_device.get_laptops(db, classification=classification)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-laptops", response_model=List[schemas_device.Laptop])
async def api_add_laptops(
    laptops_in: List[schemas_device.LaptopCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    created_items = []
    try:
        for item_in in laptops_in:
            if item_in.id:
                existing_id = db.query(Laptop).filter(Laptop.id == item_in.id).first()
                if existing_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Laptop với mã '{item_in.id}' đã tồn tại trong hệ thống."
                    )
                new_id = item_in.id
            else:
                new_id = generate_next_laptop_id(db)

            item_data = item_in.dict()
            item_data.pop("id", None)
            db_obj = Laptop(id=new_id, **item_data)
            db.add(db_obj)
            created_items.append(db_obj)

        db.commit()
        for item in created_items:
            db.refresh(item)
        return created_items
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-laptops", response_model=List[schemas_device.Laptop])
async def api_update_laptops(
    laptops_in: List[schemas_device.LaptopBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    updated_items = []
    try:
        for item_in in laptops_in:
            db_obj = db.query(Laptop).filter(Laptop.id == item_in.id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy laptop với mã '{item_in.id}'."
                )

            update_data = item_in.dict(exclude_unset=True)
            update_data.pop("id", None)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            updated_items.append(db_obj)

        db.commit()
        for item in updated_items:
            db.refresh(item)
        return updated_items
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-laptops")
async def api_delete_laptops(
    ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    try:
        deleted_ids = []
        for item_id in ids:
            db_obj = db.query(Laptop).filter(Laptop.id == item_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(item_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===================== SCREEN ENDPOINTS =====================
@router.get("/get-screens", response_model=List[schemas_device.Screen])
async def api_get_screens(
    classification: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    try:
        return crud_device.get_screens(db, classification=classification)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-screens", response_model=List[schemas_device.Screen])
async def api_add_screens(
    screens_in: List[schemas_device.ScreenCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    created_items = []
    try:
        for item_in in screens_in:
            if item_in.id:
                existing_id = db.query(Screen).filter(Screen.id == item_in.id).first()
                if existing_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Màn hình với mã '{item_in.id}' đã tồn tại trong hệ thống."
                    )
                new_id = item_in.id
            else:
                new_id = generate_next_screen_id(db)

            item_data = item_in.dict()
            item_data.pop("id", None)
            db_obj = Screen(id=new_id, **item_data)
            db.add(db_obj)
            created_items.append(db_obj)

        db.commit()
        for item in created_items:
            db.refresh(item)
        return created_items
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-screens", response_model=List[schemas_device.Screen])
async def api_update_screens(
    screens_in: List[schemas_device.ScreenBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    updated_items = []
    try:
        for item_in in screens_in:
            db_obj = db.query(Screen).filter(Screen.id == item_in.id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy màn hình với mã '{item_in.id}'."
                )

            update_data = item_in.dict(exclude_unset=True)
            update_data.pop("id", None)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            updated_items.append(db_obj)

        db.commit()
        for item in updated_items:
            db.refresh(item)
        return updated_items
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-screens")
async def api_delete_screens(
    ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    try:
        deleted_ids = []
        for item_id in ids:
            db_obj = db.query(Screen).filter(Screen.id == item_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(item_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===================== CAMERA ENDPOINTS =====================
@router.get("/get-cameras", response_model=List[schemas_device.Camera])
async def api_get_cameras(
    classification: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    try:
        return crud_device.get_cameras(db, classification=classification)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-cameras", response_model=List[schemas_device.Camera])
async def api_add_cameras(
    cameras_in: List[schemas_device.CameraCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    created_items = []
    try:
        for item_in in cameras_in:
            if item_in.id:
                existing_id = db.query(Camera).filter(Camera.id == item_in.id).first()
                if existing_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Camera với mã '{item_in.id}' đã tồn tại trong hệ thống."
                    )
                new_id = item_in.id
            else:
                new_id = generate_next_camera_id(db)

            item_data = item_in.dict()
            item_data.pop("id", None)
            db_obj = Camera(id=new_id, **item_data)
            db.add(db_obj)
            created_items.append(db_obj)

        db.commit()
        for item in created_items:
            db.refresh(item)
        return created_items
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-cameras", response_model=List[schemas_device.Camera])
async def api_update_cameras(
    cameras_in: List[schemas_device.CameraBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    updated_items = []
    try:
        for item_in in cameras_in:
            db_obj = db.query(Camera).filter(Camera.id == item_in.id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy camera với mã '{item_in.id}'."
                )

            update_data = item_in.dict(exclude_unset=True)
            update_data.pop("id", None)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            updated_items.append(db_obj)

        db.commit()
        for item in updated_items:
            db.refresh(item)
        return updated_items
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-cameras")
async def api_delete_cameras(
    ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    try:
        deleted_ids = []
        for item_id in ids:
            db_obj = db.query(Camera).filter(Camera.id == item_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(item_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===================== OTHER DEVICE ENDPOINTS =====================
@router.get("/get-other-devices", response_model=List[schemas_device.OtherDevice])
async def api_get_other_devices(
    classification: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    try:
        return crud_device.get_other_devices(db, classification=classification)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-other-devices", response_model=List[schemas_device.OtherDevice])
async def api_add_other_devices(
    devices_in: List[schemas_device.OtherDeviceCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    created_items = []
    try:
        for item_in in devices_in:
            if item_in.id:
                existing_id = db.query(OtherDevice).filter(OtherDevice.id == item_in.id).first()
                if existing_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Thiết bị khác với mã '{item_in.id}' đã tồn tại trong hệ thống."
                    )
                new_id = item_in.id
            else:
                new_id = generate_next_other_device_id(db)

            item_data = item_in.dict()
            item_data.pop("id", None)
            db_obj = OtherDevice(id=new_id, **item_data)
            db.add(db_obj)
            created_items.append(db_obj)

        db.commit()
        for item in created_items:
            db.refresh(item)
        return created_items
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-other-devices", response_model=List[schemas_device.OtherDevice])
async def api_update_other_devices(
    devices_in: List[schemas_device.OtherDeviceBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    updated_items = []
    try:
        for item_in in devices_in:
            db_obj = db.query(OtherDevice).filter(OtherDevice.id == item_in.id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy thiết bị khác với mã '{item_in.id}'."
                )

            update_data = item_in.dict(exclude_unset=True)
            update_data.pop("id", None)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            updated_items.append(db_obj)

        db.commit()
        for item in updated_items:
            db.refresh(item)
        return updated_items
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-other-devices")
async def api_delete_other_devices(
    ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    try:
        deleted_ids = []
        for item_id in ids:
            db_obj = db.query(OtherDevice).filter(OtherDevice.id == item_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(item_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===================== DEVICE ASSIGNMENT ENDPOINTS =====================
@router.get("/get-device-assignments", response_model=List[schemas_device.DeviceAssignment])
async def api_get_device_assignments(
    username: Optional[str] = None,
    device_id: Optional[str] = None,
    assigned_at: Optional[date] = None,
    returned_at: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Get device assignments, optionally filtered by username, device_id, assigned_at, or returned_at.
    """
    try:
        from sqlalchemy import Date, cast
        query = db.query(DeviceAssignment)
        if username:
            query = query.filter(DeviceAssignment.username == username)
        if device_id:
            query = query.filter(DeviceAssignment.device_id == device_id)
        if assigned_at:
            query = query.filter(cast(DeviceAssignment.assigned_at, Date) == assigned_at)
        if returned_at:
            query = query.filter(cast(DeviceAssignment.returned_at, Date) == returned_at)
        return query.all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-device-assignments", response_model=List[schemas_device.DeviceAssignment])
async def api_add_device_assignments(
    assignments_in: List[schemas_device.DeviceAssignmentCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Add a list of device assignments.
    """
    created_items = []
    try:
        for item_in in assignments_in:
            db_obj = DeviceAssignment(**item_in.dict())
            db.add(db_obj)
            created_items.append(db_obj)
        db.commit()
        for item in created_items:
            db.refresh(item)
        return created_items
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-device-assignments", response_model=List[schemas_device.DeviceAssignment])
async def api_update_device_assignments(
    assignments_in: List[schemas_device.DeviceAssignmentBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Update a list of device assignments.
    """
    updated_items = []
    try:
        for item_in in assignments_in:
            db_obj = db.query(DeviceAssignment).filter(DeviceAssignment.id == item_in.id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy phân công thiết bị với ID '{item_in.id}'."
                )
            
            update_data = item_in.dict(exclude_unset=True)
            update_data.pop("id", None)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            updated_items.append(db_obj)
        db.commit()
        for item in updated_items:
            db.refresh(item)
        return updated_items
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-device-assignments")
async def api_delete_device_assignments(
    ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(require_permission("other"))
):
    """
    Delete device assignments by ID.
    """
    try:
        deleted_ids = []
        for item_id in ids:
            db_obj = db.query(DeviceAssignment).filter(DeviceAssignment.id == item_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(item_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
