from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from bot.utils.bot import bot
from bot.utils.utils import check_command_target, require_user_type, require_project_name, require_group_role, require_custom_title
from bot.utils.enums import UserType
from bot.utils.logger import LogInfo, LogError, LogType
from app.db.session import SessionLocal
from app.models.device import Smartphone, SmartphoneStatus, Laptop, LaptopStatus, SimCard, SimCardStatus, DeviceAssignment, Application, AppCategory, AppBillingCycle, AppStatus, InstalledApp
from app.models.vehicle import Vehicle, VehicleActivityLog
from app.crud.device import get_smartphone_by_imei, create_smartphone, get_sim_card_by_phone
from app.crud.vehicle import get_vehicle_by_license_plate, create_vehicle_activity_log
from app.schemas.device import SmartphoneCreate
import datetime
import uuid

ACTIVE_SYNC_APP_SESSIONS = {}


# ===================== TẠO ĐIỆN THOẠI =====================

@bot.on_message(filters.command(["other_create_smartphone", "other_tao_dien_thoai"]) | filters.regex(r"^@\w+\s+/(other_create_smartphone|other_tao_dien_thoai)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def create_smartphone_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_create_smartphone", "other_tao_dien_thoai"])
    if args is None: return

    lines = message.text.strip().split("\n")

    # Nếu chỉ gõ lệnh không có form → hiển thị form gợi ý
    if len(lines) < 3:
        form_template = """<b>FORM TẠO ĐIỆN THOẠI MỚI</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<p>/other_create_smartphone
Mã Định Danh: 
Tên Model: 
Thương Hiệu: 
IMEI 1: 
IMEI 2: 
Số Serial: 
Phiên Bản OS: 
Dung Lượng: 
Tình Trạng Pin (%): 
Ngày Mua (dd/mm/yyyy): 
Trạng Thái: available
Phụ Kiện: 
Ghi Chú: 
</p>

<i>Trạng thái gồm: available, assigned, maintenance, broken
Mã Định Danh: mã nội bộ do bạn tự đặt (VD: SP001, DT-001...)
IMEI 1 là bắt buộc và không được trùng</i>"""
        await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        return

    # Parse form data
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    # Validate required fields
    device_id = data.get("Mã Định Danh", "").strip()
    model_name = data.get("Tên Model", "").strip()
    brand = data.get("Thương Hiệu", "").strip()
    imei_1 = data.get("IMEI 1", "").strip()
    imei_2 = data.get("IMEI 2", "").strip()
    serial_number = data.get("Số Serial", "").strip()
    os_version = data.get("Phiên Bản OS", "").strip()
    storage_capacity = data.get("Dung Lượng", "").strip()
    battery_health_str = data.get("Tình Trạng Pin (%)", "").strip()
    purchase_date_str = data.get("Ngày Mua (dd/mm/yyyy)", "").strip()
    status = data.get("Trạng Thái", "available").strip().lower()
    accessories = data.get("Phụ Kiện", "").strip()
    notes = data.get("Ghi Chú", "").strip()

    if not model_name:
        await message.reply_text("⚠️ <b>Tên Model</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    if not imei_1:
        await message.reply_text("⚠️ <b>IMEI 1</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    # Validate status
    valid_statuses = [s.value for s in SmartphoneStatus]
    if status not in valid_statuses:
        await message.reply_text(
            f"⚠️ Trạng thái <b>{status}</b> không hợp lệ. Các trạng thái hợp lệ: {', '.join(valid_statuses)}",
            parse_mode=ParseMode.HTML
        )
        return

    # Parse battery health
    battery_health = None
    if battery_health_str:
        try:
            battery_health = int(battery_health_str)
            if battery_health < 0 or battery_health > 100:
                await message.reply_text("⚠️ <b>Tình trạng pin</b> phải từ 0 đến 100.", parse_mode=ParseMode.HTML)
                return
        except ValueError:
            await message.reply_text("⚠️ <b>Tình trạng pin</b> phải là số nguyên.", parse_mode=ParseMode.HTML)
            return

    # Parse purchase date
    purchase_date = None
    if purchase_date_str:
        try:
            purchase_date = datetime.datetime.strptime(purchase_date_str, "%d/%m/%Y").date()
        except ValueError:
            await message.reply_text("⚠️ <b>Ngày mua</b> không đúng định dạng dd/mm/yyyy.", parse_mode=ParseMode.HTML)
            return

    db = SessionLocal()
    try:
        # Check IMEI duplicate
        existing = get_smartphone_by_imei(db, imei_1)
        if existing:
            await message.reply_text(
                f"⚠️ IMEI 1 <b>{imei_1}</b> đã tồn tại trong hệ thống (Model: {existing.model_name}).",
                parse_mode=ParseMode.HTML
            )
            return

        # Check device_id duplicate
        if device_id:
            existing_id = db.query(Smartphone).filter(Smartphone.id == device_id).first()
            if existing_id:
                await message.reply_text(
                    f"⚠️ Mã định danh <b>{device_id}</b> đã tồn tại trong hệ thống.",
                    parse_mode=ParseMode.HTML
                )
                return

        # Create smartphone
        new_phone = Smartphone(
            id=device_id if device_id else None,
            model_name=model_name,
            brand=brand or None,
            imei_1=imei_1,
            imei_2=imei_2 or None,
            serial_number=serial_number or None,
            os_version=os_version or None,
            storage_capacity=storage_capacity or None,
            battery_health=battery_health,
            purchase_date=purchase_date,
            status=status,
            accessories=accessories or None,
            notes=notes or None,
        )
        db.add(new_phone)
        db.commit()
        db.refresh(new_phone)

        result_text = (
            f"✅ <b>Đã tạo điện thoại thành công!</b>\n\n"
            f"<b>{model_name}</b> ({brand})\n"
            f"Mã: <code>{new_phone.id}</code>\n"
            f"IMEI 1: <code>{imei_1}</code>\n"
            f"Trạng thái: <b>{status}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[CreateSmartphone] Created {model_name} (IMEI: {imei_1}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in create_smartphone_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình tạo điện thoại: {str(e)}")
    finally:
        db.close()


# ===================== CẬP NHẬT ĐIỆN THOẠI =====================

@bot.on_message(filters.command(["other_update_smartphone", "other_cap_nhat_dien_thoai"]) | filters.regex(r"^@\w+\s+/(other_update_smartphone|other_cap_nhat_dien_thoai)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def update_smartphone_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_update_smartphone", "other_cap_nhat_dien_thoai"])
    if args is None: return

    lines = message.text.strip().split("\n")
    db = SessionLocal()
    try:
        # Nếu chỉ gõ lệnh + mã → hiển thị form pre-filled
        if len(lines) < 3:
            if len(args) < 2:
                await message.reply_text(
                    "⚠️ Vui lòng cung cấp <b>Mã Định Danh</b> hoặc <b>IMEI 1</b>.\n"
                    "Ví dụ: <code>/other_update_smartphone SP001</code>",
                    parse_mode=ParseMode.HTML
                )
                return

            lookup = args[1].strip()
            phone = db.query(Smartphone).filter(Smartphone.id == lookup).first()
            if not phone:
                phone = get_smartphone_by_imei(db, lookup)
            if not phone:
                await message.reply_text(
                    f"⚠️ Không tìm thấy điện thoại với mã/IMEI <b>{lookup}</b>.",
                    parse_mode=ParseMode.HTML
                )
                return

            fmt_date = phone.purchase_date.strftime("%d/%m/%Y") if phone.purchase_date else ""

            form_template = f"""<b>FORM CẬP NHẬT ĐIỆN THOẠI</b>
Vui lòng sao chép form dưới đây, chỉnh sửa thông tin cần thay đổi và gửi lại:

<p>/other_update_smartphone {phone.id}
Tên Model: {phone.model_name or ""}
Thương Hiệu: {phone.brand or ""}
IMEI 1: {phone.imei_1 or ""}
IMEI 2: {phone.imei_2 or ""}
Số Serial: {phone.serial_number or ""}
Phiên Bản OS: {phone.os_version or ""}
Dung Lượng: {phone.storage_capacity or ""}
Tình Trạng Pin (%): {phone.battery_health if phone.battery_health is not None else ""}
Ngày Mua (dd/mm/yyyy): {fmt_date}
Trạng Thái: {phone.status or "available"}
Phụ Kiện: {phone.accessories or ""}
Ghi Chú: {phone.notes or ""}
</p>

<i>Trạng thái gồm: available, assigned, maintenance, broken</i>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return

        # Parse form data
        if len(args) < 2:
            await message.reply_text("⚠️ Không tìm thấy mã điện thoại trong lệnh.", parse_mode=ParseMode.HTML)
            return

        lookup = args[1].strip()
        phone = db.query(Smartphone).filter(Smartphone.id == lookup).first()
        if not phone:
            phone = get_smartphone_by_imei(db, lookup)
        if not phone:
            await message.reply_text(
                f"⚠️ Không tìm thấy điện thoại với mã/IMEI <b>{lookup}</b>.",
                parse_mode=ParseMode.HTML
            )
            return

        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        model_name = data.get("Tên Model", "").strip()
        brand = data.get("Thương Hiệu", "").strip()
        imei_1 = data.get("IMEI 1", "").strip()
        imei_2 = data.get("IMEI 2", "").strip()
        serial_number = data.get("Số Serial", "").strip()
        os_version = data.get("Phiên Bản OS", "").strip()
        storage_capacity = data.get("Dung Lượng", "").strip()
        battery_health_str = data.get("Tình Trạng Pin (%)", "").strip()
        purchase_date_str = data.get("Ngày Mua (dd/mm/yyyy)", "").strip()
        status = data.get("Trạng Thái", "").strip().lower()
        accessories = data.get("Phụ Kiện", "").strip()
        notes = data.get("Ghi Chú", "").strip()

        # Validate status if provided
        if status:
            valid_statuses = [s.value for s in SmartphoneStatus]
            if status not in valid_statuses:
                await message.reply_text(
                    f"⚠️ Trạng thái <b>{status}</b> không hợp lệ. Các trạng thái hợp lệ: {', '.join(valid_statuses)}",
                    parse_mode=ParseMode.HTML
                )
                return

        # Validate battery health
        battery_health = None
        if battery_health_str:
            try:
                battery_health = int(battery_health_str)
                if battery_health < 0 or battery_health > 100:
                    await message.reply_text("⚠️ <b>Tình trạng pin</b> phải từ 0 đến 100.", parse_mode=ParseMode.HTML)
                    return
            except ValueError:
                await message.reply_text("⚠️ <b>Tình trạng pin</b> phải là số nguyên.", parse_mode=ParseMode.HTML)
                return

        # Validate purchase date
        purchase_date = None
        if purchase_date_str:
            try:
                purchase_date = datetime.datetime.strptime(purchase_date_str, "%d/%m/%Y").date()
            except ValueError:
                await message.reply_text("⚠️ <b>Ngày mua</b> không đúng định dạng dd/mm/yyyy.", parse_mode=ParseMode.HTML)
                return

        # Check IMEI duplicate if changed
        if imei_1 and imei_1 != phone.imei_1:
            existing = get_smartphone_by_imei(db, imei_1)
            if existing:
                await message.reply_text(
                    f"⚠️ IMEI 1 <b>{imei_1}</b> đã tồn tại trong hệ thống (Model: {existing.model_name}).",
                    parse_mode=ParseMode.HTML
                )
                return

        # Update fields
        if model_name: phone.model_name = model_name
        if brand: phone.brand = brand
        if imei_1: phone.imei_1 = imei_1
        phone.imei_2 = imei_2 if imei_2 else phone.imei_2
        if serial_number: phone.serial_number = serial_number
        if os_version: phone.os_version = os_version
        if storage_capacity: phone.storage_capacity = storage_capacity
        if battery_health is not None: phone.battery_health = battery_health
        if purchase_date: phone.purchase_date = purchase_date
        if status: phone.status = status
        phone.accessories = accessories if accessories else phone.accessories
        phone.notes = notes if notes else phone.notes

        db.commit()
        db.refresh(phone)

        result_text = (
            f"✅ <b>Đã cập nhật điện thoại thành công!</b>\n\n"
            f"<b>{phone.model_name}</b> ({phone.brand})\n"
            f"Mã: <code>{phone.id}</code>\n"
            f"IMEI 1: <code>{phone.imei_1}</code>\n"
            f"Trạng thái: <b>{phone.status}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[UpdateSmartphone] Updated {phone.model_name} (ID: {phone.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in update_smartphone_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình cập nhật điện thoại: {str(e)}")
    finally:
        db.close()


# ===================== XÓA ĐIỆN THOẠI (SOFT DELETE) =====================

@bot.on_message(filters.command(["other_delete_smartphone", "other_xoa_dien_thoai"]) | filters.regex(r"^@\w+\s+/(other_delete_smartphone|other_xoa_dien_thoai)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def delete_smartphone_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_delete_smartphone", "other_xoa_dien_thoai"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Mã Định Danh</b> hoặc <b>IMEI 1</b>.\n"
            "Ví dụ: <code>/other_delete_smartphone SP001</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lookup = args[1].strip()
    db = SessionLocal()
    try:
        phone = db.query(Smartphone).filter(Smartphone.id == lookup).first()
        if not phone:
            phone = get_smartphone_by_imei(db, lookup)
        if not phone:
            await message.reply_text(
                f"⚠️ Không tìm thấy điện thoại với mã/IMEI <b>{lookup}</b>.",
                parse_mode=ParseMode.HTML
            )
            return

        old_status = phone.status
        phone.status = SmartphoneStatus.BROKEN.value
        db.commit()

        result_text = (
            f"✅ <b>Đã xóa (vô hiệu hóa) điện thoại thành công!</b>\n\n"
            f"<b>{phone.model_name}</b> ({phone.brand})\n"
            f"Mã: <code>{phone.id}</code>\n"
            f"IMEI 1: <code>{phone.imei_1}</code>\n"
            f"Trạng thái: <b>{old_status}</b> → <b>{SmartphoneStatus.BROKEN.value}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[DeleteSmartphone] Soft-deleted {phone.model_name} (ID: {phone.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in delete_smartphone_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# ===================== NHẬN THIẾT BỊ =====================

@bot.on_message(filters.command(["other_receive_device", "other_nhan_thiet_bi"]) | filters.regex(r"^@\w+\s+/(other_receive_device|other_nhan_thiet_bi)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)
@require_project_name("Other")
@require_custom_title("main_device")
async def receive_device_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_receive_device", "other_nhan_thiet_bi"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Mã Định Danh</b> (hoặc IMEI cho điện thoại).\n"
            "Ví dụ: <code>/other_receive_device SP001</code>\n"
            "Ví dụ: <code>/other_receive_device LT001</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lookup = args[1].strip()
    db = SessionLocal()
    try:
        # Tìm thiết bị - thử lần lượt: Smartphone (by ID) → Laptop (by ID) → Smartphone (by IMEI)
        device = None
        device_type = None
        device_name = ""
        device_detail = ""
        initial_condition = ""

        # 1. Tìm trong Smartphone theo ID
        phone = db.query(Smartphone).filter(Smartphone.id == lookup).first()
        if phone:
            device = phone
            device_type = "smartphone"
        
        # 2. Tìm trong Laptop theo ID
        if not device:
            laptop = db.query(Laptop).filter(Laptop.id == lookup).first()
            if laptop:
                device = laptop
                device_type = "laptop"

        # 3. Fallback: Tìm Smartphone theo IMEI
        if not device:
            phone = get_smartphone_by_imei(db, lookup)
            if phone:
                device = phone
                device_type = "smartphone"

        if not device:
            await message.reply_text(
                f"⚠️ Không tìm thấy thiết bị với mã/IMEI <b>{lookup}</b>.",
                parse_mode=ParseMode.HTML
            )
            return

        # Kiểm tra trạng thái
        if device.status != "available":
            await message.reply_text(
                f"⚠️ Thiết bị <b>{device.model_name}</b> (<code>{device.id}</code>) hiện đang ở trạng thái <b>{device.status}</b>.\n"
                f"Chỉ có thiết bị ở trạng thái <b>available</b> mới được nhận.",
                parse_mode=ParseMode.HTML
            )
            return

        # Lấy thông tin người nhận
        username = message.from_user.username or str(message.from_user.id)
        today = datetime.datetime.now()

        # Build initial_condition & detail theo loại thiết bị
        if device_type == "smartphone":
            initial_condition = device.notes or ""
            device_name = f"{device.model_name} ({device.brand})"
            device_detail = (
                f"IMEI 1: <code>{device.imei_1}</code>\n"
                f"Phụ kiện: {device.accessories or 'Không có'}\n"
                f"Tình trạng ban đầu: {device.notes or 'Không ghi chú'}"
            )
        elif device_type == "laptop":
            initial_condition = f"CPU: {device.processor_cpu or 'N/A'}, RAM: {device.ram_size or 'N/A'}, Storage: {device.storage_specs or 'N/A'}"
            device_name = f"{device.model_name}"
            device_detail = (
                f"CPU: {device.processor_cpu or 'N/A'}\n"
                f"RAM: {device.ram_size or 'N/A'}\n"
                f"Storage: {device.storage_specs or 'N/A'}\n"
                f"Service Tag: <code>{device.service_tag or 'N/A'}</code>"
            )

        # Tạo bản ghi device_assignment
        assignment = DeviceAssignment(
            id=uuid.uuid4(),
            username=f"@{username}" if message.from_user.username else username,
            device_type=device_type,
            device_id=device.id,
            assigned_at=today,
            returned_at=None,
            initial_condition=initial_condition,
            final_condition=None,
        )
        db.add(assignment)

        # Cập nhật trạng thái thiết bị
        device.status = "assigned"
        db.commit()

        fmt_date = today.strftime("%H:%M %d/%m/%Y")
        result_text = (
            f"✅ <b>Nhận thiết bị thành công!</b>\n\n"
            f"Loại: <b>{device_type.upper()}</b>\n"
            f"<b>{device_name}</b>\n"
            f"Mã: <code>{device.id}</code>\n"
            f"{device_detail}\n"
            f"Người nhận: <b>@{username}</b>\n"
            f"Ngày nhận: <b>{fmt_date}</b>\n"
            f"Trạng thái: <b>available</b> → <b>assigned</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[ReceiveDevice] @{username} received {device_type} {device.model_name} (ID: {device.id})", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in receive_device_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# ===================== TRẢ THIẾT BỊ =====================

@bot.on_message(filters.command(["other_return_device", "other_tra_thiet_bi"]) | filters.regex(r"^@\w+\s+/(other_return_device|other_tra_thiet_bi)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)
@require_project_name("Other")
@require_custom_title("main_device")
async def return_device_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_return_device", "other_tra_thiet_bi"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Mã Định Danh</b> (hoặc IMEI cho điện thoại).\n"
            "Ví dụ: <code>/other_return_device SP001</code>\n"
            "Ví dụ: <code>/other_return_device LT001</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lookup = args[1].strip()
    db = SessionLocal()
    try:
        # Tìm thiết bị - thử lần lượt: Smartphone (by ID) → Laptop (by ID) → Smartphone (by IMEI)
        device = None
        device_type = None
        device_name = ""

        # 1. Tìm trong Smartphone theo ID
        phone = db.query(Smartphone).filter(Smartphone.id == lookup).first()
        if phone:
            device = phone
            device_type = "smartphone"

        # 2. Tìm trong Laptop theo ID
        if not device:
            laptop = db.query(Laptop).filter(Laptop.id == lookup).first()
            if laptop:
                device = laptop
                device_type = "laptop"

        # 3. Fallback: Tìm Smartphone theo IMEI
        if not device:
            phone = get_smartphone_by_imei(db, lookup)
            if phone:
                device = phone
                device_type = "smartphone"

        if not device:
            await message.reply_text(
                f"⚠️ Không tìm thấy thiết bị với mã/IMEI <b>{lookup}</b>.",
                parse_mode=ParseMode.HTML
            )
            return

        # Kiểm tra trạng thái
        if device.status != "assigned":
            await message.reply_text(
                f"⚠️ Thiết bị <b>{device.model_name}</b> (<code>{device.id}</code>) hiện đang ở trạng thái <b>{device.status}</b>.\n"
                f"Chỉ có thiết bị ở trạng thái <b>assigned</b> mới được trả.",
                parse_mode=ParseMode.HTML
            )
            return

        # Tìm bản ghi assignment đang active (chưa trả)
        username = message.from_user.username or str(message.from_user.id)
        assignment = db.query(DeviceAssignment).filter(
            DeviceAssignment.device_id == device.id,
            DeviceAssignment.device_type == device_type,
            DeviceAssignment.returned_at.is_(None)
        ).order_by(DeviceAssignment.assigned_at.desc()).first()

        if not assignment:
            await message.reply_text(
                f"⚠️ Không tìm thấy bản ghi nhận thiết bị cho <code>{device.id}</code>.",
                parse_mode=ParseMode.HTML
            )
            return

        # Kiểm tra người trả có phải người nhận không
        holder = assignment.username.lstrip("@")
        if holder != username:
            await message.reply_text(
                f"⚠️ Bạn không phải là người đang giữ thiết bị <code>{device.id}</code>.\n"
                f"Người giữ hiện tại: <b>{assignment.username}</b>",
                parse_mode=ParseMode.HTML
            )
            return

        # Cập nhật assignment
        today = datetime.datetime.now()
        assignment.returned_at = today
        assignment.final_condition = "Đã trả"

        # Cập nhật trạng thái thiết bị
        device.status = "available"
        db.commit()

        # Build device detail
        if device_type == "smartphone":
            device_name = f"{device.model_name} ({device.brand})"
            device_detail = f"IMEI 1: <code>{device.imei_1}</code>"
        elif device_type == "laptop":
            device_name = f"{device.model_name}"
            device_detail = f"Service Tag: <code>{device.service_tag or 'N/A'}</code>"
        else:
            device_detail = ""

        fmt_date = today.strftime("%H:%M %d/%m/%Y")
        result_text = (
            f"✅ <b>Trả thiết bị thành công!</b>\n\n"
            f"Loại: <b>{device_type.upper()}</b>\n"
            f"<b>{device_name}</b>\n"
            f"Mã: <code>{device.id}</code>\n"
            f"{device_detail}\n"
            f"Người trả: <b>@{username}</b>\n"
            f"Ngày trả: <b>{fmt_date}</b>\n"
            f"Trạng thái: <b>assigned</b> → <b>available</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[ReturnDevice] @{username} returned {device_type} {device.model_name} (ID: {device.id})", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in return_device_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# ===================== XEM LỊCH SỬ THIẾT BỊ =====================

@bot.on_message(filters.command(["other_check_log_device", "other_lich_su_thiet_bi"]) | filters.regex(r"^@\w+\s+/(other_check_log_device|other_lich_su_thiet_bi)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)
@require_project_name("Other")
@require_custom_title("main_device")
async def check_log_device_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_check_log_device", "other_lich_su_thiet_bi"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Mã Định Danh</b> (hoặc IMEI cho điện thoại).\n"
            "Cú pháp: <code>/other_check_log_device [mã thiết bị]</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lookup = args[1].strip()
    db = SessionLocal()
    try:
        # Tìm thiết bị
        device = None
        device_type = None
        device_name = ""
        device_detail = ""

        phone = db.query(Smartphone).filter(Smartphone.id == lookup).first()
        if phone:
            device = phone
            device_type = "smartphone"

        if not device:
            laptop = db.query(Laptop).filter(Laptop.id == lookup).first()
            if laptop:
                device = laptop
                device_type = "laptop"

        if not device:
            phone = get_smartphone_by_imei(db, lookup)
            if phone:
                device = phone
                device_type = "smartphone"

        if not device:
            await message.reply_text(
                f"❌ Không tìm thấy thiết bị với mã/IMEI <b>{lookup}</b>.",
                parse_mode=ParseMode.HTML
            )
            return

        # Build device info
        if device_type == "smartphone":
            device_name = f"{device.model_name} ({device.brand})"
            device_detail = f"IMEI 1: {device.imei_1}"
        elif device_type == "laptop":
            device_name = f"{device.model_name}"
            device_detail = f"Service Tag: {device.service_tag or 'N/A'}"

        # Đếm tổng số lượt nhận
        total_assignments = db.query(DeviceAssignment).filter(
            DeviceAssignment.device_id == device.id,
            DeviceAssignment.device_type == device_type
        ).count()

        if total_assignments == 0:
            await message.reply_text(
                f"ℹ️ Thiết bị <code>{device.id}</code> chưa có lịch sử nhận/trả nào.",
                parse_mode=ParseMode.HTML
            )
            return

        # Nếu > 20 log → xuất file txt
        if total_assignments > 20:
            all_logs = db.query(DeviceAssignment).filter(
                DeviceAssignment.device_id == device.id,
                DeviceAssignment.device_type == device_type
            ).order_by(DeviceAssignment.assigned_at.desc()).all()

            file_content = (
                f"LỊCH SỬ NHẬN/TRẢ THIẾT BỊ\n"
                f"{'='*40}\n"
                f"Loại: {device_type.upper()}\n"
                f"Tên: {device_name}\n"
                f"Mã: {device.id}\n"
                f"{device_detail}\n"
                f"Trạng thái hiện tại: {device.status}\n"
                f"Tổng lượt nhận: {total_assignments}\n"
                f"{'='*40}\n\n"
            )

            for idx, log in enumerate(reversed(all_logs), 1):
                assigned_date = log.assigned_at.strftime('%H:%M %d/%m/%Y') if log.assigned_at else "N/A"
                returned_date = log.returned_at.strftime('%H:%M %d/%m/%Y') if log.returned_at else "Chưa trả"

                file_content += (
                    f"#{idx}\n"
                    f"  Người nhận:  {log.username}\n"
                    f"  Ngày nhận:   {assigned_date}\n"
                    f"  Ngày trả:    {returned_date}\n"
                    f"  TT ban đầu:  {log.initial_condition or 'N/A'}\n"
                    f"  TT khi trả:  {log.final_condition or 'N/A'}\n"
                    f"{'-'*40}\n"
                )

            import os
            file_name = f"log_device_{device.id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            file_path = os.path.join("tmp", file_name)
            os.makedirs("tmp", exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            await message.reply_document(
                document=file_path,
                caption=f"<b>LỊCH SỬ THIẾT BỊ</b>\nMã: <code>{device.id}</code>\nTổng: {total_assignments} lượt nhận",
                parse_mode=ParseMode.HTML
            )

            os.remove(file_path)
            return

        # <= 20 log → hiển thị inline
        logs = db.query(DeviceAssignment).filter(
            DeviceAssignment.device_id == device.id,
            DeviceAssignment.device_type == device_type
        ).order_by(DeviceAssignment.assigned_at.desc()).all()

        response = (
            f"<b>LỊCH SỬ NHẬN/TRẢ THIẾT BỊ</b>\n\n"
            f"<b>Loại:</b> {device_type.upper()}\n"
            f"<b>Tên:</b> {device_name}\n"
            f"<b>Mã:</b> <code>{device.id}</code>\n"
            f"<b>{device_detail}</b>\n"
            f"<b>Trạng thái hiện tại:</b> {device.status}\n"
            f"-------------------\n\n"
        )

        for log in reversed(logs):
            assigned_date = log.assigned_at.strftime('%H:%M %d/%m/%Y') if log.assigned_at else "N/A"
            returned_date = log.returned_at.strftime('%H:%M %d/%m/%Y') if log.returned_at else "<i>Chưa trả</i>"

            response += (
                f"<b>Người nhận:</b> {log.username}\n"
                f"<b>Ngày nhận:</b> {assigned_date}\n"
                f"<b>Ngày trả:</b> {returned_date}\n"
                f"<b>TT ban đầu:</b> {log.initial_condition or 'N/A'}\n"
                f"<b>TT khi trả:</b> {log.final_condition or 'N/A'}\n"
                f"-------------------\n"
            )

        if len(response) > 4096:
            for i in range(0, len(response), 4000):
                await message.reply_text(response[i:i+4000], parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(response, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in check_log_device_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra khi tra cứu lịch sử thiết bị: {str(e)}")
    finally:
        db.close()


# ===================== TẠO SIM =====================

@bot.on_message(filters.command(["other_create_sim", "other_tao_sim"]) | filters.regex(r"^@\w+\s+/(other_create_sim|other_tao_sim)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def create_sim_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_create_sim", "other_tao_sim"])
    if args is None: return

    lines = message.text.strip().split("\n")

    # Hiển thị form mẫu
    if len(lines) < 3:
        form_template = """<b>FORM TẠO SIM MỚI</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<p>/other_create_sim
Mã Định Danh: 
Số Điện Thoại: 
Nhà Mạng: 
ICCID: 
Mã PUK: 
Gói Cước: 
Trạng Thái: active
Loại SIM: 
Đang Ở Thiết Bị: 
</p>

<i>Trạng thái gồm: active, blocked, expired
Loại SIM: eSIM, SIM vật lý, trả trước, trả sau...
Mã Định Danh: mã nội bộ do bạn tự đặt (VD: SIM001)
Đang Ở Thiết Bị: điền mã định danh điện thoại/thiết bị nếu SIM đang gắn trong đó</i>"""
        await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        return

    # Parse form
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    sim_id = data.get("Mã Định Danh", "").strip()
    phone_number = data.get("Số Điện Thoại", "").strip()
    carrier = data.get("Nhà Mạng", "").strip()
    iccid = data.get("ICCID", "").strip()
    puk_code = data.get("Mã PUK", "").strip()
    plan_name = data.get("Gói Cước", "").strip()
    status = data.get("Trạng Thái", "active").strip().lower()
    sim_type = data.get("Loại SIM", "").strip()
    smartphone_id = data.get("Đang Ở Thiết Bị", "").strip()

    if not phone_number:
        await message.reply_text("⚠️ <b>Số Điện Thoại</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    # Validate status
    valid_statuses = [s.value for s in SimCardStatus]
    if status not in valid_statuses:
        await message.reply_text(
            f"⚠️ Trạng thái <b>{status}</b> không hợp lệ. Các trạng thái hợp lệ: {', '.join(valid_statuses)}",
            parse_mode=ParseMode.HTML
        )
        return

    db = SessionLocal()
    try:
        # Check SĐT trùng
        existing = get_sim_card_by_phone(db, phone_number)
        if existing:
            await message.reply_text(
                f"⚠️ Số điện thoại <b>{phone_number}</b> đã tồn tại trong hệ thống (Mã: {existing.id}).",
                parse_mode=ParseMode.HTML
            )
            return

        # Check mã định danh trùng
        if sim_id:
            existing_id = db.query(SimCard).filter(SimCard.id == sim_id).first()
            if existing_id:
                await message.reply_text(
                    f"⚠️ Mã định danh <b>{sim_id}</b> đã tồn tại trong hệ thống.",
                    parse_mode=ParseMode.HTML
                )
                return

        # Check smartphone_id tồn tại nếu có
        if smartphone_id:
            phone_device = db.query(Smartphone).filter(Smartphone.id == smartphone_id).first()
            if not phone_device:
                await message.reply_text(
                    f"⚠️ Không tìm thấy điện thoại với mã <b>{smartphone_id}</b>.",
                    parse_mode=ParseMode.HTML
                )
                return

        new_sim = SimCard(
            id=sim_id if sim_id else None,
            phone_number=phone_number,
            carrier=carrier or None,
            iccid=iccid or None,
            puk_code=puk_code or None,
            plan_name=plan_name or None,
            status=status,
            sim_type=sim_type or None,
            smartphone_id=smartphone_id or None,
        )
        db.add(new_sim)
        db.commit()
        db.refresh(new_sim)

        smartphone_info = f"Đang ở máy: <code>{smartphone_id}</code>" if smartphone_id else "Chưa gắn vào thiết bị nào"
        result_text = (
            f"✅ <b>Đã tạo SIM thành công!</b>\n\n"
            f"Mã: <code>{new_sim.id}</code>\n"
            f"SĐT: <b>{phone_number}</b>\n"
            f"Nhà mạng: <b>{carrier or 'N/A'}</b>\n"
            f"Loại SIM: <b>{sim_type or 'N/A'}</b>\n"
            f"Gói cước: {plan_name or 'N/A'}\n"
            f"Trạng thái: <b>{status}</b>\n"
            f"{smartphone_info}"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[CreateSim] Created SIM {phone_number} (ID: {new_sim.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in create_sim_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình tạo SIM: {str(e)}")
    finally:
        db.close()


# ===================== CẬP NHẬT SIM =====================

@bot.on_message(filters.command(["other_update_sim", "other_cap_nhat_sim"]) | filters.regex(r"^@\w+\s+/(other_update_sim|other_cap_nhat_sim)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def update_sim_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_update_sim", "other_cap_nhat_sim"])
    if args is None: return

    lines = message.text.strip().split("\n")
    db = SessionLocal()
    try:
        # Hiển thị form pre-filled
        if len(lines) < 3:
            if len(args) < 2:
                await message.reply_text(
                    "⚠️ Vui lòng cung cấp <b>Mã Định Danh</b> hoặc <b>Số Điện Thoại</b>.\n"
                    "Ví dụ: <code>/other_update_sim SIM001</code>",
                    parse_mode=ParseMode.HTML
                )
                return

            lookup = args[1].strip()
            sim = db.query(SimCard).filter(SimCard.id == lookup).first()
            if not sim:
                sim = get_sim_card_by_phone(db, lookup)
            if not sim:
                await message.reply_text(
                    f"⚠️ Không tìm thấy SIM với mã/SĐT <b>{lookup}</b>.",
                    parse_mode=ParseMode.HTML
                )
                return

            form_template = f"""<b>FORM CẬP NHẬT SIM</b>
Vui lòng sao chép form dưới đây, chỉnh sửa thông tin cần thay đổi và gửi lại:

<p>/other_update_sim {sim.id}
Số Điện Thoại: {sim.phone_number or ""}
Nhà Mạng: {sim.carrier or ""}
ICCID: {sim.iccid or ""}
Mã PUK: {sim.puk_code or ""}
Gói Cước: {sim.plan_name or ""}
Trạng Thái: {sim.status or "active"}
Loại SIM: {sim.sim_type or ""}
Đang Ở Thiết Bị: {sim.smartphone_id or ""}
</p>

<i>Trạng thái gồm: active, blocked, expired</i>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return

        # Parse form
        if len(args) < 2:
            await message.reply_text("⚠️ Không tìm thấy mã SIM trong lệnh.", parse_mode=ParseMode.HTML)
            return

        lookup = args[1].strip()
        sim = db.query(SimCard).filter(SimCard.id == lookup).first()
        if not sim:
            sim = get_sim_card_by_phone(db, lookup)
        if not sim:
            await message.reply_text(
                f"⚠️ Không tìm thấy SIM với mã/SĐT <b>{lookup}</b>.",
                parse_mode=ParseMode.HTML
            )
            return

        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        phone_number = data.get("Số Điện Thoại", "").strip()
        carrier = data.get("Nhà Mạng", "").strip()
        iccid = data.get("ICCID", "").strip()
        puk_code = data.get("Mã PUK", "").strip()
        plan_name = data.get("Gói Cước", "").strip()
        status = data.get("Trạng Thái", "").strip().lower()
        sim_type = data.get("Loại SIM", "").strip()
        smartphone_id = data.get("Đang Ở Thiết Bị", "").strip()

        # Validate status
        if status:
            valid_statuses = [s.value for s in SimCardStatus]
            if status not in valid_statuses:
                await message.reply_text(
                    f"⚠️ Trạng thái <b>{status}</b> không hợp lệ. Các trạng thái hợp lệ: {', '.join(valid_statuses)}",
                    parse_mode=ParseMode.HTML
                )
                return

        # Check SĐT trùng nếu thay đổi
        if phone_number and phone_number != sim.phone_number:
            existing = get_sim_card_by_phone(db, phone_number)
            if existing:
                await message.reply_text(
                    f"⚠️ Số điện thoại <b>{phone_number}</b> đã tồn tại trong hệ thống (Mã: {existing.id}).",
                    parse_mode=ParseMode.HTML
                )
                return

        # Check smartphone_id tồn tại nếu có
        if smartphone_id:
            phone_device = db.query(Smartphone).filter(Smartphone.id == smartphone_id).first()
            if not phone_device:
                await message.reply_text(
                    f"⚠️ Không tìm thấy điện thoại với mã <b>{smartphone_id}</b>.",
                    parse_mode=ParseMode.HTML
                )
                return

        # Update fields
        if phone_number: sim.phone_number = phone_number
        if carrier: sim.carrier = carrier
        if iccid: sim.iccid = iccid
        if puk_code: sim.puk_code = puk_code
        if plan_name: sim.plan_name = plan_name
        if status: sim.status = status
        if sim_type: sim.sim_type = sim_type
        sim.smartphone_id = smartphone_id if smartphone_id else sim.smartphone_id

        db.commit()
        db.refresh(sim)

        result_text = (
            f"✅ <b>Đã cập nhật SIM thành công!</b>\n\n"
            f"Mã: <code>{sim.id}</code>\n"
            f"SĐT: <b>{sim.phone_number}</b>\n"
            f"Nhà mạng: <b>{sim.carrier or 'N/A'}</b>\n"
            f"Loại SIM: <b>{sim.sim_type or 'N/A'}</b>\n"
            f"Trạng thái: <b>{sim.status}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[UpdateSim] Updated SIM {sim.phone_number} (ID: {sim.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in update_sim_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình cập nhật SIM: {str(e)}")
    finally:
        db.close()


# ===================== XÓA SIM (SOFT DELETE) =====================

@bot.on_message(filters.command(["other_delete_sim", "other_xoa_sim"]) | filters.regex(r"^@\w+\s+/(other_delete_sim|other_xoa_sim)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def delete_sim_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_delete_sim", "other_xoa_sim"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Mã Định Danh</b> hoặc <b>Số Điện Thoại</b>.\n"
            "Ví dụ: <code>/other_delete_sim SIM001</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lookup = args[1].strip()
    db = SessionLocal()
    try:
        sim = db.query(SimCard).filter(SimCard.id == lookup).first()
        if not sim:
            sim = get_sim_card_by_phone(db, lookup)
        if not sim:
            await message.reply_text(
                f"⚠️ Không tìm thấy SIM với mã/SĐT <b>{lookup}</b>.",
                parse_mode=ParseMode.HTML
            )
            return

        old_status = sim.status
        sim.status = SimCardStatus.EXPIRED.value
        db.commit()

        result_text = (
            f"✅ <b>Đã xóa (vô hiệu hóa) SIM thành công!</b>\n\n"
            f"Mã: <code>{sim.id}</code>\n"
            f"SĐT: <b>{sim.phone_number}</b>\n"
            f"Nhà mạng: <b>{sim.carrier or 'N/A'}</b>\n"
            f"Trạng thái: <b>{old_status}</b> → <b>{SimCardStatus.EXPIRED.value}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[DeleteSim] Soft-deleted SIM {sim.phone_number} (ID: {sim.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in delete_sim_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# ===================== TẠO ỨNG DỤNG =====================

@bot.on_message(filters.command(["other_create_application", "other_tao_ung_dung"]) | filters.regex(r"^@\w+\s+/(other_create_application|other_tao_ung_dung)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def create_application_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_create_application", "other_tao_ung_dung"])
    if args is None: return

    lines = message.text.strip().split("\n")

    if len(lines) < 3:
        form_template = """<b>FORM TẠO ỨNG DỤNG MỚI</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<p>/other_create_application
Mã Định Danh (ID): 
Tên Ứng Dụng: 
Tên Gói (Package): 
Phân Loại: other
Email Đăng Ký: 
Mật Khẩu: 
Gói Dịch Vụ: 
Phí Duy Trì (Tháng): 0
Chu Kỳ: monthly
Giới Hạn Thiết Bị: 1
Trả Phí (1/0): 0
Ngày Gia Hạn (dd/mm/yyyy): 
Trạng Thái: active
Đang Ở Thiết Bị (Mã cách nhau bằng dấu phẩy): 
</p>

<i>Phân loại gồm: streaming, social, education, design, other
Chu kỳ gồm: monthly, quarterly, yearly
Trạng thái gồm: active, expired, suspended</i>"""
        await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        return

    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    app_id = data.get("Mã Định Danh (ID)", "").strip()
    app_name = data.get("Tên Ứng Dụng", "").strip()
    package_name = data.get("Tên Gói (Package)", "").strip()
    service_category = data.get("Phân Loại", "other").strip().lower()
    account_email = data.get("Email Đăng Ký", "").strip()
    password = data.get("Mật Khẩu", "").strip()
    subscription_plan = data.get("Gói Dịch Vụ", "").strip()
    monthly_fee_str = data.get("Phí Duy Trì (Tháng)", "0").strip()
    billing_cycle = data.get("Chu Kỳ", "monthly").strip().lower()
    concurrent_limit_str = data.get("Giới Hạn Thiết Bị", "1").strip()
    is_premium_str = data.get("Trả Phí (1/0)", "0").strip()
    renewal_date_str = data.get("Ngày Gia Hạn (dd/mm/yyyy)", "").strip()
    status = data.get("Trạng Thái", "active").strip().lower()
    devices_str = data.get("Đang Ở Thiết Bị (Mã cách nhau bằng dấu phẩy)", "").strip()

    if not app_name:
        await message.reply_text("⚠️ <b>Tên Ứng Dụng</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    # Validate enums
    if service_category not in [s.value for s in AppCategory]:
        await message.reply_text(f"⚠️ Phân loại <b>{service_category}</b> không hợp lệ.", parse_mode=ParseMode.HTML)
        return
    if billing_cycle not in [s.value for s in AppBillingCycle]:
        await message.reply_text(f"⚠️ Chu kỳ <b>{billing_cycle}</b> không hợp lệ.", parse_mode=ParseMode.HTML)
        return
    if status not in [s.value for s in AppStatus]:
        await message.reply_text(f"⚠️ Trạng thái <b>{status}</b> không hợp lệ.", parse_mode=ParseMode.HTML)
        return

    try:
        monthly_fee = int(monthly_fee_str) if monthly_fee_str else 0
        concurrent_limit = int(concurrent_limit_str) if concurrent_limit_str else 1
        is_premium = int(is_premium_str) if is_premium_str else 0
    except ValueError:
        await message.reply_text("⚠️ <b>Phí Duy Trì / Giới Hạn Thiết Bị / Trả Phí</b> phải là số nguyên.", parse_mode=ParseMode.HTML)
        return

    renewal_date = None
    if renewal_date_str:
        try:
            renewal_date = datetime.datetime.strptime(renewal_date_str, "%d/%m/%Y").date()
        except ValueError:
            await message.reply_text("⚠️ <b>Ngày gia hạn</b> không đúng định dạng dd/mm/yyyy.", parse_mode=ParseMode.HTML)
            return

    db = SessionLocal()
    try:
        # Check duplicate ID if provided
        if app_id:
            existing = db.query(Application).filter(Application.id == app_id).first()
            if existing:
                await message.reply_text(f"⚠️ Ứng dụng với ID <b>{app_id}</b> đã tồn tại.", parse_mode=ParseMode.HTML)
                db.close()
                return

        new_app = Application(
            id=app_id if app_id else str(uuid.uuid4()),
            app_name=app_name,
            package_name=package_name or None,
            service_category=service_category,
            account_email=account_email or None,
            password=password or None,
            subscription_plan=subscription_plan or None,
            monthly_fee=monthly_fee,
            billing_cycle=billing_cycle,
            concurrent_limit=concurrent_limit,
            is_premium=is_premium,
            renewal_date=renewal_date,
            status=status,
        )
        db.add(new_app)
        db.commit()
        db.refresh(new_app)

        # Handle InstalledApp logic
        installed_devices = []
        if devices_str:
            device_ids = [d.strip() for d in devices_str.split(",") if d.strip()]
            for d_id in device_ids:
                # Check if device exists
                phone = db.query(Smartphone).filter(Smartphone.id == d_id).first()
                laptop = db.query(Laptop).filter(Laptop.id == d_id).first()
                if phone or laptop:
                    i_app = InstalledApp(
                        device_id=d_id,
                        app_id=new_app.id,
                        install_at=datetime.date.today()
                    )
                    db.add(i_app)
                    installed_devices.append(d_id)
            if installed_devices:
                db.commit()

        installed_info = f"Đang cài trên: <b>{', '.join(installed_devices)}</b>" if installed_devices else "Chưa cài trên thiết bị nào"

        result_text = (
            f"✅ <b>Đã tạo ứng dụng thành công!</b>\n\n"
            f"ID (Mã Ứng Dụng): <code>{new_app.id}</code>\n"
            f"Ứng dụng: <b>{app_name}</b>\n"
            f"Email: {account_email or 'N/A'}\n"
            f"Gói dịch vụ: {subscription_plan or 'N/A'} (Trả phí: {is_premium})\n"
            f"{installed_info}\n"
            f"Trạng thái: <b>{status}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[CreateApp] Created {app_name} (ID: {new_app.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in create_application_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình tạo ứng dụng: {str(e)}")
    finally:
        db.close()


# ===================== CẬP NHẬT ỨNG DỤNG =====================

@bot.on_message(filters.command(["other_update_application", "other_cap_nhat_ung_dung"]) | filters.regex(r"^@\w+\s+/(other_update_application|other_cap_nhat_ung_dung)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def update_application_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_update_application", "other_cap_nhat_ung_dung"])
    if args is None: return

    lines = message.text.strip().split("\n")
    db = SessionLocal()
    try:
        if len(lines) < 3:
            if len(args) < 2:
                await message.reply_text(
                    "⚠️ Vui lòng cung cấp <b>Mã Ứng Dụng (ID)</b>.\n"
                    "Ví dụ: <code>/other_update_application aaaaaa-bbbb-cccc</code>",
                    parse_mode=ParseMode.HTML
                )
                return

            lookup = args[1].strip()
            app = db.query(Application).filter(Application.id == lookup).first()

            if not app:
                await message.reply_text(f"⚠️ Không tìm thấy ứng dụng với ID <b>{lookup}</b>.", parse_mode=ParseMode.HTML)
                return

            fmt_date = app.renewal_date.strftime("%d/%m/%Y") if app.renewal_date else ""

            existing_i_apps = db.query(InstalledApp).filter(InstalledApp.app_id == app.id).all()
            existing_d_ids = [ia.device_id for ia in existing_i_apps]
            existing_devices_str = ", ".join(existing_d_ids)

            form_template = f"""<b>FORM CẬP NHẬT ỨNG DỤNG</b>
Vui lòng sao chép form dưới đây, chỉnh sửa thông tin cần thay đổi và gửi lại:

<p>/other_update_application {app.id}
Tên Ứng Dụng: {app.app_name or ""}
Tên Gói (Package): {app.package_name or ""}
Phân Loại: {app.service_category or "other"}
Email Đăng Ký: {app.account_email or ""}
Mật Khẩu: {app.password or ""}
Gói Dịch Vụ: {app.subscription_plan or ""}
Phí Duy Trì (Tháng): {app.monthly_fee if app.monthly_fee is not None else 0}
Chu Kỳ: {app.billing_cycle or "monthly"}
Giới Hạn Thiết Bị: {app.concurrent_limit if app.concurrent_limit is not None else 1}
Trả Phí (1/0): {app.is_premium if app.is_premium is not None else 0}
Ngày Gia Hạn (dd/mm/yyyy): {fmt_date}
Trạng Thái: {app.status or "active"}
Đang Ở Thiết Bị (Mã cách nhau bằng dấu phẩy): {existing_devices_str}
</p>

<i>Phân loại gồm: streaming, social, education, design, other
Chu kỳ gồm: monthly, quarterly, yearly
Trạng thái gồm: active, expired, suspended</i>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return

        if len(args) < 2:
            await message.reply_text("⚠️ Không tìm thấy Mã Ứng Dụng trong lệnh.", parse_mode=ParseMode.HTML)
            return

        lookup = args[1].strip()
        app = db.query(Application).filter(Application.id == lookup).first()

        if not app:
            await message.reply_text(f"⚠️ Không tìm thấy ứng dụng với ID <b>{lookup}</b>.", parse_mode=ParseMode.HTML)
            return

        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        app_name = data.get("Tên Ứng Dụng", "").strip()
        package_name = data.get("Tên Gói (Package)", "").strip()
        service_category = data.get("Phân Loại", "").strip().lower()
        account_email = data.get("Email Đăng Ký", "").strip()
        password = data.get("Mật Khẩu", "").strip()
        subscription_plan = data.get("Gói Dịch Vụ", "").strip()
        monthly_fee_str = data.get("Phí Duy Trì (Tháng)", "").strip()
        billing_cycle = data.get("Chu Kỳ", "").strip().lower()
        concurrent_limit_str = data.get("Giới Hạn Thiết Bị", "").strip()
        is_premium_str = data.get("Trả Phí (1/0)", "").strip()
        renewal_date_str = data.get("Ngày Gia Hạn (dd/mm/yyyy)", "").strip()
        status = data.get("Trạng Thái", "").strip().lower()
        devices_str_new = data.get("Đang Ở Thiết Bị (Mã cách nhau bằng dấu phẩy)", None)

        # Validate enums if provided
        if service_category and service_category not in [s.value for s in AppCategory]:
            await message.reply_text(f"⚠️ Phân loại <b>{service_category}</b> không hợp lệ.", parse_mode=ParseMode.HTML)
            return
        if billing_cycle and billing_cycle not in [s.value for s in AppBillingCycle]:
            await message.reply_text(f"⚠️ Chu kỳ <b>{billing_cycle}</b> không hợp lệ.", parse_mode=ParseMode.HTML)
            return
        if status and status not in [s.value for s in AppStatus]:
            await message.reply_text(f"⚠️ Trạng thái <b>{status}</b> không hợp lệ.", parse_mode=ParseMode.HTML)
            return

        try:
            if monthly_fee_str: app.monthly_fee = int(monthly_fee_str)
            if concurrent_limit_str: app.concurrent_limit = int(concurrent_limit_str)
            if is_premium_str: app.is_premium = int(is_premium_str)
        except ValueError:
            await message.reply_text("⚠️ <b>Phí Duy Trì / Giới Hạn / Trả Phí</b> phải là số nguyên.", parse_mode=ParseMode.HTML)
            return

        if renewal_date_str:
            try:
                app.renewal_date = datetime.datetime.strptime(renewal_date_str, "%d/%m/%Y").date()
            except ValueError:
                await message.reply_text("⚠️ <b>Ngày gia hạn</b> không đúng định dạng dd/mm/yyyy.", parse_mode=ParseMode.HTML)
                return

        if app_name: app.app_name = app_name
        app.package_name = package_name if package_name else app.package_name
        if service_category: app.service_category = service_category
        app.account_email = account_email if account_email else app.account_email
        app.password = password if password else app.password
        app.subscription_plan = subscription_plan if subscription_plan else app.subscription_plan
        if billing_cycle: app.billing_cycle = billing_cycle
        if status: app.status = status

        db.commit()
        db.refresh(app)

        installed_info = ""
        # Handle InstalledApp logic if field is presented in the update
        if devices_str_new is not None:
            # Drop old records
            db.query(InstalledApp).filter(InstalledApp.app_id == app.id).delete()
            
            # Add new records
            devices_str_clean = devices_str_new.strip()
            installed_devices = []
            if devices_str_clean:
                device_ids = [d.strip() for d in devices_str_clean.split(",") if d.strip()]
                for d_id in device_ids:
                    phone = db.query(Smartphone).filter(Smartphone.id == d_id).first()
                    laptop = db.query(Laptop).filter(Laptop.id == d_id).first()
                    if phone or laptop:
                        i_app = InstalledApp(
                            device_id=d_id,
                            app_id=app.id,
                            install_at=datetime.date.today()
                        )
                        db.add(i_app)
                        installed_devices.append(d_id)
            db.commit()
            installed_info = f"\nĐang cài trên: <b>{', '.join(installed_devices)}</b>" if installed_devices else "\nChưa cài trên thiết bị nào"
        else:
            # If they didn't include the line, keep old info for display
            existing_i_apps = db.query(InstalledApp).filter(InstalledApp.app_id == app.id).all()
            if existing_i_apps:
                installed_info = f"\nĐang cài trên: <b>{', '.join([ia.device_id for ia in existing_i_apps])}</b>"

        result_text = (
            f"✅ <b>Đã cập nhật ứng dụng thành công!</b>\n\n"
            f"ID: <code>{app.id}</code>\n"
            f"Ứng dụng: <b>{app.app_name}</b>\n"
            f"Email: {app.account_email or 'N/A'}{installed_info}\n"
            f"Trạng thái: <b>{app.status}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[UpdateApp] Updated {app.app_name} (ID: {app.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in update_application_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình cập nhật ứng dụng: {str(e)}")
    finally:
        db.close()


# ===================== XÓA ỨNG DỤNG =====================

@bot.on_message(filters.command(["other_delete_application", "other_xoa_ung_dung"]) | filters.regex(r"^@\w+\s+/(other_delete_application|other_xoa_ung_dung)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def delete_application_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_delete_application", "other_xoa_ung_dung"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Mã Ứng Dụng (ID)</b>.\n"
            "Ví dụ: <code>/other_delete_application aaaaaa-bbbb-cccc</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lookup = args[1].strip()
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.id == lookup).first()

        if not app:
            await message.reply_text(f"⚠️ Không tìm thấy ứng dụng với ID <b>{lookup}</b>.", parse_mode=ParseMode.HTML)
            return

        old_status = app.status
        app.status = AppStatus.SUSPENDED.value
        db.commit()

        result_text = (
            f"✅ <b>Đã xóa (vô hiệu hóa) ứng dụng thành công!</b>\n\n"
            f"ID: <code>{app.id}</code>\n"
            f"Ứng dụng: <b>{app.app_name}</b>\n"
            f"Trạng thái: <b>{old_status}</b> → <b>{AppStatus.SUSPENDED.value}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[DeleteApp] Soft-deleted {app.app_name} (ID: {app.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in delete_application_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# ===================== DANH SÁCH THIẾT BỊ =====================

@bot.on_message(filters.command(["other_list_device", "other_danh_sach_thiet_bi"]) | filters.regex(r"^@\w+\s+/(other_list_device|other_danh_sach_thiet_bi)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def list_device_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_list_device", "other_danh_sach_thiet_bi"])
    if args is None: return

    db = SessionLocal()
    try:
        smartphones = db.query(Smartphone).all()
        laptops = db.query(Laptop).all()

        if not smartphones and not laptops:
            await message.reply_text("ℹ️ Chưa có thiết bị nào trong hệ thống.", parse_mode=ParseMode.HTML)
            return

        total_devices = len(smartphones) + len(laptops)
        entries = []

        # Build smartphone entries
        for phone in smartphones:
            # Người đang giữ
            assignment = db.query(DeviceAssignment).filter(
                DeviceAssignment.device_id == phone.id,
                DeviceAssignment.device_type == "smartphone",
                DeviceAssignment.returned_at.is_(None)
            ).order_by(DeviceAssignment.assigned_at.desc()).first()
            holder = assignment.username if assignment else "Chưa giao"

            # SIM cards
            sims = db.query(SimCard).filter(SimCard.smartphone_id == phone.id).all()
            sim_text = ", ".join([f"{s.phone_number} ({s.carrier or 'N/A'})" for s in sims]) if sims else "Không có"

            # Apps
            i_apps = db.query(InstalledApp).filter(InstalledApp.device_id == phone.id).all()
            app_names = []
            if i_apps:
                app_ids = [ia.app_id for ia in i_apps]
                apps = db.query(Application).filter(Application.id.in_(app_ids)).all()
                app_names = [a.app_name for a in apps]
            app_text = ", ".join(app_names) if app_names else "Không có"

            entries.append({
                "type": "SMARTPHONE",
                "id": phone.id,
                "name": f"{phone.model_name} ({phone.brand})",
                "status": phone.status,
                "holder": holder,
                "accessories": phone.accessories or "Không có",
                "sim": sim_text,
                "apps": app_text,
                "imei": phone.imei_1 or "N/A",
            })

        # Build laptop entries
        for lt in laptops:
            assignment = db.query(DeviceAssignment).filter(
                DeviceAssignment.device_id == lt.id,
                DeviceAssignment.device_type == "laptop",
                DeviceAssignment.returned_at.is_(None)
            ).order_by(DeviceAssignment.assigned_at.desc()).first()
            holder = assignment.username if assignment else "Chưa giao"

            i_apps = db.query(InstalledApp).filter(InstalledApp.device_id == lt.id).all()
            app_names = []
            if i_apps:
                app_ids = [ia.app_id for ia in i_apps]
                apps = db.query(Application).filter(Application.id.in_(app_ids)).all()
                app_names = [a.app_name for a in apps]
            app_text = ", ".join(app_names) if app_names else "Không có"

            entries.append({
                "type": "LAPTOP",
                "id": lt.id,
                "name": lt.model_name,
                "status": lt.status,
                "holder": holder,
                "accessories": lt.accessories or "Không có",
                "sim": "N/A",
                "apps": app_text,
                "imei": f"Tag: {lt.service_tag or 'N/A'}",
            })

        # Nếu > 20 thiết bị → xuất file txt
        if total_devices > 20:
            import os
            file_content = (
                f"DANH SÁCH THIẾT BỊ\n"
                f"{'='*50}\n"
                f"Tổng: {total_devices} thiết bị ({len(smartphones)} điện thoại, {len(laptops)} laptop)\n"
                f"{'='*50}\n\n"
            )

            for idx, e in enumerate(entries, 1):
                file_content += (
                    f"#{idx} [{e['type']}] {e['name']}\n"
                    f"  Mã:         {e['id']}\n"
                    f"  IMEI/Tag:   {e['imei']}\n"
                    f"  Trạng thái: {e['status']}\n"
                    f"  Người giữ:  {e['holder']}\n"
                    f"  Phụ kiện:   {e['accessories']}\n"
                    f"  SIM:        {e['sim']}\n"
                    f"  Ứng dụng:   {e['apps']}\n"
                    f"{'-'*50}\n"
                )

            file_name = f"list_device_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            file_path = os.path.join("tmp", file_name)
            os.makedirs("tmp", exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            await message.reply_document(
                document=file_path,
                caption=f"<b>DANH SÁCH THIẾT BỊ</b>\nTổng: {total_devices} thiết bị ({len(smartphones)} ĐT, {len(laptops)} Laptop)",
                parse_mode=ParseMode.HTML
            )
            os.remove(file_path)
            return

        # <= 20 thiết bị → hiển thị inline
        response = (
            f"<b>DANH SÁCH THIẾT BỊ</b>\n"
            f"Tổng: {total_devices} thiết bị ({len(smartphones)} ĐT, {len(laptops)} Laptop)\n"
            f"-------------------\n\n"
        )

        for e in entries:
            response += (
                f"<b>[{e['type']}] {e['name']}</b>\n"
                f"<b>Mã:</b> <code>{e['id']}</code>\n"
                f"<b>Trạng thái:</b> {e['status']}\n"
                f"<b>Người giữ:</b> {e['holder']}\n"
                f"<b>Phụ kiện:</b> {e['accessories']}\n"
            )
            if e['type'] == "SMARTPHONE":
                response += f"<b>SIM:</b> {e['sim']}\n"
            response += (
                f"<b>Ứng dụng:</b> {e['apps']}\n"
                f"-------------------\n"
            )

        if len(response) > 4096:
            for i in range(0, len(response), 4000):
                await message.reply_text(response[i:i+4000], parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(response, parse_mode=ParseMode.HTML)

        LogInfo(f"[ListDevice] Listed {total_devices} devices by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in list_device_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# ===================== TRA CỨU THIẾT BỊ =====================

@bot.on_message(filters.command(["other_check_device", "other_tra_cuu_thiet_bi"]) | filters.regex(r"^@\w+\s+/(other_check_device|other_tra_cuu_thiet_bi)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def check_device_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_check_device", "other_tra_cuu_thiet_bi"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Mã Thiết Bị</b> hoặc <b>IMEI</b>.\n"
            "Ví dụ: <code>/other_check_device SP001</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lookup = args[1].strip()
    db = SessionLocal()
    try:
        device = db.query(Smartphone).filter(Smartphone.id == lookup).first()
        device_type = "smartphone"
        
        if not device:
            device = db.query(Laptop).filter(Laptop.id == lookup).first()
            device_type = "laptop"

        if not device:
            device = get_smartphone_by_imei(db, lookup)
            device_type = "smartphone"

        if not device:
            await message.reply_text(f"⚠️ Không tìm thấy thiết bị nào với mã/IMEI <b>{lookup}</b>.", parse_mode=ParseMode.HTML)
            return

        # 1. Info User Assigned
        current_assignment = db.query(DeviceAssignment).filter(
            DeviceAssignment.device_id == device.id,
            DeviceAssignment.returned_at == None
        ).order_by(DeviceAssignment.assigned_at.desc()).first()

        user_info = "Chưa có người sử dụng"
        if current_assignment:
            user_info = f"<b>{current_assignment.username}</b> (Nhận lúc: {current_assignment.assigned_at.strftime('%H:%M %d/%m/%Y') if current_assignment.assigned_at else 'N/A'})"

        # 2. Build Basic Info
        if device_type == "smartphone":
            base_info = (
                f"<b>ĐIỆN THOẠI: {device.model_name} ({device.brand})</b>\n"
                f"Mã: <code>{device.id}</code> | IMEI: <code>{device.imei_1}</code>\n"
                f"Dung lượng: {device.storage_capacity or 'N/A'} | Pin: {device.battery_health or 'N/A'}%\n"
                f"Trạng thái: <b>{device.status}</b>\n\n"
                f"<b>Người sử dụng:</b> {user_info}\n"
            )
        else:
            base_info = (
                f"<b>LAPTOP: {device.model_name}</b>\n"
                f"Mã: <code>{device.id}</code> | Service Tag: <code>{device.service_tag or 'N/A'}</code>\n"
                f"Cấu hình: {device.processor_cpu or 'N/A'} - {device.ram_size or 'N/A'} - {device.storage_specs or 'N/A'}\n"
                f"Trạng thái: <b>{device.status}</b>\n\n"
                f"<b>Người sử dụng:</b> {user_info}\n"
            )

        # 3. Apps Installed
        i_apps = db.query(InstalledApp).filter(InstalledApp.device_id == device.id).all()
        app_list = []
        if i_apps:
            app_ids = [ia.app_id for ia in i_apps]
            applications = db.query(Application).filter(Application.id.in_(app_ids)).all()
            for app in applications:
                app_list.append(f"- {app.app_name} (Gói: {app.subscription_plan or 'N/A'})")
        
        apps_info = "\n<b>Ứng dụng đang cài:</b>\n" + ("\n".join(app_list) if app_list else "- Không có ứng dụng nào.")

        sim_info = ""
        # 4. SIMs Installed (only smartphone)
        if device_type == "smartphone":
            sims = db.query(SimCard).filter(SimCard.smartphone_id == device.id).all()
            sim_list = []
            if sims:
                for sim in sims:
                    sim_list.append(f"- SĐT: {sim.phone_number} (Mạng: {sim.carrier or 'N/A'} - {sim.plan_name or 'N/A'})")
            sim_info = "\n\n<b>SIM đang gắn:</b>\n" + ("\n".join(sim_list) if sim_list else "- Không có SIM nào.")

        final_msg = base_info + apps_info + sim_info
        await message.reply_text(final_msg, parse_mode=ParseMode.HTML)
        LogInfo(f"[CheckDevice] Checked {device_type} {lookup} by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in check_device_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# ===================== ĐỒNG BỘ ỨNG DỤNG (SYNC APP) =====================

@bot.on_message(filters.command(["other_sync_app", "other_dong_bo_ung_dung"]) | filters.regex(r"^@\w+\s+/(other_sync_app|other_dong_bo_ung_dung)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def sync_app_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_sync_app", "other_dong_bo_ung_dung"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Mã Ứng Dụng (ID)</b>.\n"
            "Ví dụ: <code>/other_sync_app APP001</code>",
            parse_mode=ParseMode.HTML
        )
        return

    app_id = args[1].strip()
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.id == app_id).first()
        if not app:
            await message.reply_text(f"⚠️ Không tìm thấy ứng dụng với ID <b>{app_id}</b>.", parse_mode=ParseMode.HTML)
            return

        # Lấy tất cả thiết bị (Smartphone + Laptop)
        smartphones = db.query(Smartphone).all()
        laptops = db.query(Laptop).all()
        
        # Lấy các thiết bị đã được cài đặt ứng dụng này
        installed = db.query(InstalledApp).filter(InstalledApp.app_id == app.id).all()
        installed_device_ids = {ia.device_id for ia in installed}

        available_devices = []
        for s in smartphones:
            if s.id not in installed_device_ids:
                available_devices.append({"id": s.id, "name": f"{s.model_name}", "group": "SP"})
        for l in laptops:
            if l.id not in installed_device_ids:
                available_devices.append({"id": l.id, "name": f"{l.model_name}", "group": "LT"})

        if not available_devices:
            await message.reply_text("✅ Ứng dụng này đã được cài đặt trên tất cả các thiết bị hiện có.", parse_mode=ParseMode.HTML)
            return

        # Prepare UI
        # Vì giới hạn button, chúng ta có thể phân trang nếu quá dài, tạm thời hiển thị tối đa 50 thiết bị để an toàn cho 1 message
        available_devices = available_devices[:50]
        
        buttons = []
        for dev in available_devices:
            buttons.append([InlineKeyboardButton(f"{dev['name']} ({dev['id']})", callback_data=f"other_sync_toggle|{dev['id']}")])
        
        buttons.append([InlineKeyboardButton("✅ Xác Nhận Đồng Bộ", callback_data=f"other_sync_confirm|{app.id}")])
        buttons.append([InlineKeyboardButton("❌ Huỷ", callback_data=f"other_sync_cancel|{app.id}")])

        reply_markup = InlineKeyboardMarkup(buttons)
        text = (
            f"<b>ĐỒNG BỘ ỨNG DỤNG</b>\n\n"
            f"Ứng dụng: <b>{app.app_name}</b>\n"
            f"ID: <code>{app.id}</code>\n"
            f"Vui lòng tick (chọn) các thiết bị dưới đây để cài ứng dụng:"
        )

        sent_msg = await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        # Save session
        dev_mapping = {d["id"]: d["name"] for d in available_devices}
        ACTIVE_SYNC_APP_SESSIONS[sent_msg.id] = {
            "app_id": app.id,
            "app_name": app.app_name,
            "devices": dev_mapping,
            "selected": set()
        }

    except Exception as e:
        db.rollback()
        LogError(f"Error in sync_app_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^other_sync_(toggle|confirm|cancel)\|(.+)$"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def sync_app_cb_handler(client, callback_query: CallbackQuery):
    action = callback_query.matches[0].group(1)
    payload = callback_query.matches[0].group(2)
    msg_id = callback_query.message.id

    session = ACTIVE_SYNC_APP_SESSIONS.get(msg_id)
    if not session:
        await callback_query.answer("Phiên làm việc đã hết hạn hoặc không tồn tại.", show_alert=True)
        return

    if action == "cancel":
        del ACTIVE_SYNC_APP_SESSIONS[msg_id]
        await callback_query.message.edit_text("❌ <b>Đã huỷ thao tác đồng bộ.</b>", parse_mode=ParseMode.HTML)
        await callback_query.answer()
        return

    if action == "toggle":
        device_id = payload
        if device_id in session["devices"]:
            if device_id in session["selected"]:
                session["selected"].remove(device_id)
            else:
                session["selected"].add(device_id)

            # Rebuild keyboard
            buttons = []
            for d_id, d_name in session["devices"].items():
                icon = "✅" if d_id in session["selected"] else "⬜"
                buttons.append([InlineKeyboardButton(f"{icon} {d_name} ({d_id})", callback_data=f"other_sync_toggle|{d_id}")])
            
            buttons.append([InlineKeyboardButton(f"✅ Xác Nhận Đồng Bộ ({len(session['selected'])})", callback_data=f"other_sync_confirm|{session['app_id']}")])
            buttons.append([InlineKeyboardButton("❌ Huỷ", callback_data=f"other_sync_cancel|{session['app_id']}")])
            
            await callback_query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
        await callback_query.answer()
        return

    if action == "confirm":
        app_id = payload
        if app_id != session["app_id"]:
            await callback_query.answer("Lỗi dữ liệu phiên.", show_alert=True)
            return
            
        selected_devices = session["selected"]
        if not selected_devices:
            await callback_query.answer("Vui lòng chọn ít nhất 1 thiết bị, hoặc chọn Huỷ.", show_alert=True)
            return

        db = SessionLocal()
        try:
            for d_id in selected_devices:
                i_app = InstalledApp(
                    device_id=d_id,
                    app_id=app_id,
                    install_at=datetime.date.today()
                )
                db.add(i_app)
            db.commit()

            success_str = ", ".join(selected_devices)
            text = (
                f"✅ <b>Đã đồng bộ ứng dụng thành công!</b>\n\n"
                f"Ứng dụng: <b>{session['app_name']}</b> (<code>{app_id}</code>)\n"
                f"Đã cài đặt thêm vào <b>{len(selected_devices)}</b> thiết bị:\n"
                f"<b>{success_str}</b>"
            )
            await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML)
            LogInfo(f"[SyncApp] Synced App {app_id} context to {len(selected_devices)} devices by @{callback_query.from_user.username}", LogType.SYSTEM_STATUS)
            
            # Clean up
            del ACTIVE_SYNC_APP_SESSIONS[msg_id]

        except Exception as e:
            db.rollback()
            LogError(f"Error in sync_app_cb_handler: {e}", LogType.SYSTEM_STATUS)
            await callback_query.message.reply_text(f"❌ Có lỗi kết nối DB: {str(e)}")
        finally:
            db.close()
        await callback_query.answer()


# ===================== TẠO LAPTOP =====================

@bot.on_message(filters.command(["other_create_laptop", "other_tao_laptop"]) | filters.regex(r"^@\w+\s+/(other_create_laptop|other_tao_laptop)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def create_laptop_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_create_laptop", "other_tao_laptop"])
    if args is None: return

    lines = message.text.strip().split("\n")

    if len(lines) < 3:
        form_template = """<b>FORM TẠO LAPTOP MỚI</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<p>/other_create_laptop
Mã Thiết Bị (ID): 
Tên Laptop: 
CPU: 
RAM: 
Ổ Cứng: 
Card Đồ Họa: 
Service Tag: 
MAC Address: 
Hạn Bảo Hành (dd/mm/yyyy): 
Phụ Kiện: 
Trạng Thái: available
</p>

<i>Trạng thái gồm: available, assigned, maintenance</i>"""
        await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        return

    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    device_id = data.get("Mã Thiết Bị (ID)", "").strip()
    model_name = data.get("Tên Laptop", "").strip()
    processor_cpu = data.get("CPU", "").strip()
    ram_size = data.get("RAM", "").strip()
    storage_specs = data.get("Ổ Cứng", "").strip()
    gpu_card = data.get("Card Đồ Họa", "").strip()
    service_tag = data.get("Service Tag", "").strip()
    mac_address = data.get("MAC Address", "").strip()
    warranty_expiry_str = data.get("Hạn Bảo Hành (dd/mm/yyyy)", "").strip()
    accessories = data.get("Phụ Kiện", "").strip()
    status = data.get("Trạng Thái", "available").strip().lower()

    if not device_id or not model_name:
        await message.reply_text("⚠️ <b>Mã Thiết Bị (ID)</b> và <b>Tên Laptop</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    if status not in [s.value for s in LaptopStatus]:
        await message.reply_text(f"⚠️ Trạng thái <b>{status}</b> không hợp lệ.", parse_mode=ParseMode.HTML)
        return

    warranty_expiry = None
    if warranty_expiry_str:
        try:
            warranty_expiry = datetime.datetime.strptime(warranty_expiry_str, "%d/%m/%Y").date()
        except ValueError:
            await message.reply_text("⚠️ <b>Hạn bảo hành</b> không đúng định dạng dd/mm/yyyy.", parse_mode=ParseMode.HTML)
            return

    db = SessionLocal()
    try:
        existing = db.query(Laptop).filter(Laptop.id == device_id).first()
        if existing:
            await message.reply_text(f"⚠️ Laptop với mã <b>{device_id}</b> đã tồn tại.", parse_mode=ParseMode.HTML)
            return

        new_laptop = Laptop(
            id=device_id,
            model_name=model_name,
            processor_cpu=processor_cpu or None,
            ram_size=ram_size or None,
            storage_specs=storage_specs or None,
            gpu_card=gpu_card or None,
            service_tag=service_tag or None,
            mac_address=mac_address or None,
            warranty_expiry=warranty_expiry,
            accessories=accessories or None,
            status=status
        )
        db.add(new_laptop)
        db.commit()
        db.refresh(new_laptop)

        result_text = (
            f"✅ <b>Đã thêm Laptop thành công!</b>\n\n"
            f"Mã: <code>{new_laptop.id}</code>\n"
            f"Laptop: <b>{model_name}</b>\n"
            f"Cấu hình: {processor_cpu or 'N/A'} - {ram_size or 'N/A'}\n"
            f"Trạng thái: <b>{status}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[CreateLaptop] Created {model_name} (ID: {new_laptop.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in create_laptop_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình tạo laptop: {str(e)}")
    finally:
        db.close()


# ===================== CẬP NHẬT LAPTOP =====================

@bot.on_message(filters.command(["other_update_laptop", "other_cap_nhat_laptop"]) | filters.regex(r"^@\w+\s+/(other_update_laptop|other_cap_nhat_laptop)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def update_laptop_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_update_laptop", "other_cap_nhat_laptop"])
    if args is None: return

    lines = message.text.strip().split("\n")
    db = SessionLocal()
    try:
        if len(lines) < 3:
            if len(args) < 2:
                await message.reply_text(
                    "⚠️ Vui lòng cung cấp <b>Mã Thiết Bị</b>.\n"
                    "Ví dụ: <code>/other_update_laptop LT001</code>",
                    parse_mode=ParseMode.HTML
                )
                return

            lookup = args[1].strip()
            laptop = db.query(Laptop).filter(Laptop.id == lookup).first()

            if not laptop:
                await message.reply_text(f"⚠️ Không tìm thấy Laptop với mã <b>{lookup}</b>.", parse_mode=ParseMode.HTML)
                return

            fmt_date = laptop.warranty_expiry.strftime("%d/%m/%Y") if laptop.warranty_expiry else ""

            form_template = f"""<b>FORM CẬP NHẬT LAPTOP</b>
Vui lòng sao chép form dưới đây, chỉnh sửa thông tin cần thay đổi và gửi lại:

<p>/other_update_laptop {laptop.id}
Tên Laptop: {laptop.model_name or ""}
CPU: {laptop.processor_cpu or ""}
RAM: {laptop.ram_size or ""}
Ổ Cứng: {laptop.storage_specs or ""}
Card Đồ Họa: {laptop.gpu_card or ""}
Service Tag: {laptop.service_tag or ""}
MAC Address: {laptop.mac_address or ""}
Hạn Bảo Hành (dd/mm/yyyy): {fmt_date}
Phụ Kiện: {laptop.accessories or ""}
Trạng Thái: {laptop.status or "available"}
</p>

<i>Trạng thái gồm: available, assigned, maintenance</i>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return

        if len(args) < 2:
            await message.reply_text("⚠️ Không tìm thấy Mã Thiết Bị trong lệnh.", parse_mode=ParseMode.HTML)
            return

        lookup = args[1].strip()
        laptop = db.query(Laptop).filter(Laptop.id == lookup).first()

        if not laptop:
            await message.reply_text(f"⚠️ Không tìm thấy Laptop với mã <b>{lookup}</b>.", parse_mode=ParseMode.HTML)
            return

        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        model_name = data.get("Tên Laptop", "").strip()
        processor_cpu = data.get("CPU", "").strip()
        ram_size = data.get("RAM", "").strip()
        storage_specs = data.get("Ổ Cứng", "").strip()
        gpu_card = data.get("Card Đồ Họa", "").strip()
        service_tag = data.get("Service Tag", "").strip()
        mac_address = data.get("MAC Address", "").strip()
        warranty_expiry_str = data.get("Hạn Bảo Hành (dd/mm/yyyy)", "").strip()
        accessories = data.get("Phụ Kiện", "").strip()
        status = data.get("Trạng Thái", "").strip().lower()

        if status and status not in [s.value for s in LaptopStatus]:
            await message.reply_text(f"⚠️ Trạng thái <b>{status}</b> không hợp lệ.", parse_mode=ParseMode.HTML)
            return

        if warranty_expiry_str:
            try:
                laptop.warranty_expiry = datetime.datetime.strptime(warranty_expiry_str, "%d/%m/%Y").date()
            except ValueError:
                await message.reply_text("⚠️ <b>Hạn bảo hành</b> không đúng định dạng dd/mm/yyyy.", parse_mode=ParseMode.HTML)
                return

        if model_name: laptop.model_name = model_name
        laptop.processor_cpu = processor_cpu if processor_cpu else laptop.processor_cpu
        laptop.ram_size = ram_size if ram_size else laptop.ram_size
        laptop.storage_specs = storage_specs if storage_specs else laptop.storage_specs
        laptop.gpu_card = gpu_card if gpu_card else laptop.gpu_card
        laptop.service_tag = service_tag if service_tag else laptop.service_tag
        laptop.mac_address = mac_address if mac_address else laptop.mac_address
        laptop.accessories = accessories if accessories else laptop.accessories
        if status: laptop.status = status

        db.commit()
        db.refresh(laptop)

        result_text = (
            f"✅ <b>Đã cập nhật Laptop thành công!</b>\n\n"
            f"Mã: <code>{laptop.id}</code>\n"
            f"Laptop: <b>{laptop.model_name}</b>\n"
            f"Trạng thái: <b>{laptop.status}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[UpdateLaptop] Updated {laptop.model_name} (ID: {laptop.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in update_laptop_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình cập nhật laptop: {str(e)}")
    finally:
        db.close()


# ===================== XÓA LAPTOP =====================

@bot.on_message(filters.command(["other_delete_laptop", "other_xoa_laptop"]) | filters.regex(r"^@\w+\s+/(other_delete_laptop|other_xoa_laptop)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_device")
async def delete_laptop_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_delete_laptop", "other_xoa_laptop"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Mã Thiết Bị</b>.\n"
            "Ví dụ: <code>/other_delete_laptop LT001</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lookup = args[1].strip()
    db = SessionLocal()
    try:
        laptop = db.query(Laptop).filter(Laptop.id == lookup).first()

        if not laptop:
            await message.reply_text(f"⚠️ Không tìm thấy Laptop với mã <b>{lookup}</b>.", parse_mode=ParseMode.HTML)
            return

        old_status = laptop.status
        laptop.status = LaptopStatus.MAINTENANCE.value
        db.commit()

        result_text = (
            f"✅ <b>Đã chuyển trạng thái Laptop thành công! (Xóa mềm)</b>\n\n"
            f"Mã: <code>{laptop.id}</code>\n"
            f"Laptop: <b>{laptop.model_name}</b>\n"
            f"Trạng thái: <b>{old_status}</b> → <b>{LaptopStatus.MAINTENANCE.value}</b>"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[DeleteLaptop] Maintained {laptop.model_name} (ID: {laptop.id}) by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in delete_laptop_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# ===================== TẠO XE =====================

@bot.on_message(filters.command(["other_create_vehicle", "other_tao_xe"]) | filters.regex(r"^@\w+\s+/(other_create_vehicle|other_tao_xe)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_vehicle")
async def create_vehicle_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_create_vehicle", "other_tao_xe"])
    if args is None: return

    lines = message.text.strip().split("\n")

    # Nếu chỉ gõ lệnh không có form → hiển thị form gợi ý
    if len(lines) < 3:
        form_template = """<b>FORM TẠO XE MỚI</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<p>/other_create_vehicle
Biển Số: 
Loại Xe: 
Thương Hiệu: 
Model: 
Màu Sắc: 
Chủ Xe: 
Trạng Thái: inactivity
</p>

<i>Trạng thái gồm: activited (đang hoạt động), inactivity (không hoạt động), is_removed (đã xóa)
Biển Số là bắt buộc và không được trùng</i>"""
        await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        return

    # Parse form data
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    # Validate required fields
    license_plate = data.get("Biển Số", "").strip()
    vehicle_type = data.get("Loại Xe", "").strip()
    brand = data.get("Thương Hiệu", "").strip()
    model = data.get("Model", "").strip()
    color = data.get("Màu Sắc", "").strip()
    owner_name = data.get("Chủ Xe", "").strip()
    status = data.get("Trạng Thái", "inactivity").strip().lower()

    if not license_plate:
        await message.reply_text("⚠️ <b>Biển Số</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    # Validate status
    valid_statuses = ["activited", "inactivity", "is_removed"]
    if status not in valid_statuses:
        await message.reply_text(
            f"⚠️ Trạng thái <b>{status}</b> không hợp lệ. Các trạng thái hợp lệ: {', '.join(valid_statuses)}",
            parse_mode=ParseMode.HTML
        )
        return

    db = SessionLocal()
    try:
        # Check biển số trùng
        existing = get_vehicle_by_license_plate(db, license_plate)
        if existing:
            await message.reply_text(
                f"⚠️ Biển số <b>{license_plate}</b> đã tồn tại trong hệ thống.",
                parse_mode=ParseMode.HTML
            )
            return

        new_vehicle = Vehicle(
            license_plate=license_plate,
            vehicle_type=vehicle_type or None,
            brand=brand or None,
            model=model or None,
            color=color or None,
            owner_name=owner_name or None,
            status=status,
        )
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)

        status_display = "Đang hoạt động" if status == "activited" else "Đã xóa" if status == "is_removed" else "Không hoạt động"
        result_text = (
            f"✅ <b>Đã tạo xe thành công!</b>\n\n"
            f"<b>Biển số:</b> <code>{license_plate}</code>\n"
            f"<b>Loại xe:</b> {vehicle_type or 'N/A'}\n"
            f"<b>Thương hiệu:</b> {brand or 'N/A'} {model or ''}\n"
            f"<b>Màu sắc:</b> {color or 'N/A'}\n"
            f"<b>Chủ xe:</b> {owner_name or 'N/A'}\n"
            f"<b>Trạng thái:</b> {status_display}"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[CreateVehicle] Created vehicle {license_plate} by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in create_vehicle_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình tạo xe: {str(e)}")
    finally:
        db.close()


# ===================== CẬP NHẬT XE =====================

@bot.on_message(filters.command(["other_update_vehicle", "other_cap_nhat_xe"]) | filters.regex(r"^@\w+\s+/(other_update_vehicle|other_cap_nhat_xe)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_vehicle")
async def update_vehicle_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_update_vehicle", "other_cap_nhat_xe"])
    if args is None: return

    lines = message.text.strip().split("\n")
    db = SessionLocal()
    try:
        # Nếu chỉ gõ lệnh + biển số → hiển thị form pre-filled
        if len(lines) < 3:
            if len(args) < 2:
                await message.reply_text(
                    "⚠️ Vui lòng cung cấp <b>Biển Số</b> xe cần cập nhật.\n"
                    "Ví dụ: <code>/other_update_vehicle 30A12345</code>",
                    parse_mode=ParseMode.HTML
                )
                return

            lookup = args[1].strip()
            vehicle = get_vehicle_by_license_plate(db, lookup)
            if not vehicle:
                # Thử tìm bằng ID
                vehicle = db.query(Vehicle).filter(Vehicle.id == lookup).first()
            if not vehicle:
                await message.reply_text(
                    f"⚠️ Không tìm thấy xe với biển số/ID <b>{lookup}</b>.",
                    parse_mode=ParseMode.HTML
                )
                return

            form_template = f"""<b>FORM CẬP NHẬT XE</b>
Vui lòng sao chép form dưới đây, chỉnh sửa thông tin cần thay đổi và gửi lại:

<p>/other_update_vehicle {vehicle.license_plate}
Biển Số: {vehicle.license_plate or ""}
Loại Xe: {vehicle.vehicle_type or ""}
Thương Hiệu: {vehicle.brand or ""}
Model: {vehicle.model or ""}
Màu Sắc: {vehicle.color or ""}
Chủ Xe: {vehicle.owner_name or ""}
Trạng Thái: {vehicle.status or "inactivity"}
</p>

<i>Trạng thái gồm: activited (đang hoạt động), inactivity (không hoạt động), is_removed (đã xóa)</i>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return

        # Parse form data
        if len(args) < 2:
            await message.reply_text("⚠️ Không tìm thấy biển số xe trong lệnh.", parse_mode=ParseMode.HTML)
            return

        lookup = args[1].strip()
        vehicle = get_vehicle_by_license_plate(db, lookup)
        if not vehicle:
            vehicle = db.query(Vehicle).filter(Vehicle.id == lookup).first()
        if not vehicle:
            await message.reply_text(
                f"⚠️ Không tìm thấy xe với biển số/ID <b>{lookup}</b>.",
                parse_mode=ParseMode.HTML
            )
            return

        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        license_plate = data.get("Biển Số", "").strip()
        vehicle_type = data.get("Loại Xe", "").strip()
        brand = data.get("Thương Hiệu", "").strip()
        model_name = data.get("Model", "").strip()
        color = data.get("Màu Sắc", "").strip()
        owner_name = data.get("Chủ Xe", "").strip()
        status = data.get("Trạng Thái", "").strip().lower()

        # Validate status if provided
        if status:
            valid_statuses = ["activited", "inactivity", "is_removed"]
            if status not in valid_statuses:
                await message.reply_text(
                    f"⚠️ Trạng thái <b>{status}</b> không hợp lệ. Các trạng thái hợp lệ: {', '.join(valid_statuses)}",
                    parse_mode=ParseMode.HTML
                )
                return

        # Check biển số trùng nếu thay đổi
        if license_plate and license_plate != vehicle.license_plate:
            existing = get_vehicle_by_license_plate(db, license_plate)
            if existing:
                await message.reply_text(
                    f"⚠️ Biển số <b>{license_plate}</b> đã tồn tại trong hệ thống.",
                    parse_mode=ParseMode.HTML
                )
                return

        # Update fields
        if license_plate: vehicle.license_plate = license_plate
        if vehicle_type: vehicle.vehicle_type = vehicle_type
        if brand: vehicle.brand = brand
        if model_name: vehicle.model = model_name
        if color: vehicle.color = color
        if owner_name: vehicle.owner_name = owner_name
        if status: vehicle.status = status

        db.commit()
        db.refresh(vehicle)

        status_display = "Đang hoạt động" if vehicle.status == "activited" else "Đã xóa" if vehicle.status == "is_removed" else "Không hoạt động"
        result_text = (
            f"✅ <b>Đã cập nhật xe thành công!</b>\n\n"
            f"<b>Biển số:</b> <code>{vehicle.license_plate}</code>\n"
            f"<b>Loại xe:</b> {vehicle.vehicle_type or 'N/A'}\n"
            f"<b>Thương hiệu:</b> {vehicle.brand or 'N/A'} {vehicle.model or ''}\n"
            f"<b>Màu sắc:</b> {vehicle.color or 'N/A'}\n"
            f"<b>Chủ xe:</b> {vehicle.owner_name or 'N/A'}\n"
            f"<b>Trạng thái:</b> {status_display}"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[UpdateVehicle] Updated vehicle {vehicle.license_plate} by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in update_vehicle_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra trong quá trình cập nhật xe: {str(e)}")
    finally:
        db.close()


# ===================== XÓA XE (SOFT DELETE - CHUYỂN TRẠNG THÁI) =====================

@bot.on_message(filters.command(["other_delete_vehicle", "other_xoa_xe"]) | filters.regex(r"^@\w+\s+/(other_delete_vehicle|other_xoa_xe)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_vehicle")
async def delete_vehicle_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_delete_vehicle", "other_xoa_xe"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Biển Số</b> xe cần xóa.\n"
            "Ví dụ: <code>/other_delete_vehicle 30A12345</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lookup = args[1].strip()
    db = SessionLocal()
    try:
        vehicle = get_vehicle_by_license_plate(db, lookup)
        if not vehicle:
            vehicle = db.query(Vehicle).filter(Vehicle.id == lookup).first()
        if not vehicle:
            await message.reply_text(
                f"⚠️ Không tìm thấy xe với biển số/ID <b>{lookup}</b>.",
                parse_mode=ParseMode.HTML
            )
            return

        old_status = vehicle.status
        old_display = "Đang hoạt động" if old_status == "activited" else "Đã xóa" if old_status == "is_removed" else "Không hoạt động"
        vehicle.status = "is_removed"
        db.commit()

        result_text = (
            f"✅ <b>Đã xóa (vô hiệu hóa) xe thành công!</b>\n\n"
            f"<b>Biển số:</b> <code>{vehicle.license_plate}</code>\n"
            f"<b>Loại xe:</b> {vehicle.vehicle_type or 'N/A'}\n"
            f"<b>Thương hiệu:</b> {vehicle.brand or 'N/A'} {vehicle.model or ''}\n"
            f"<b>Chủ xe:</b> {vehicle.owner_name or 'N/A'}\n"
            f"<b>Trạng thái:</b> {old_display} → Đã xóa"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[DeleteVehicle] Soft-deleted vehicle {vehicle.license_plate} by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in delete_vehicle_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# ===================== NHẬN XE =====================

@bot.on_message(filters.command(["other_receive_vehicle", "other_nhan_xe"]) | filters.regex(r"^@\w+\s+/(other_receive_vehicle|other_nhan_xe)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_vehicle")
async def other_receive_vehicle_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_receive_vehicle", "other_nhan_xe"])
    if args is None: return

    if len(args) < 2:
        # Hiển thị danh sách xe có thể nhận
        db = SessionLocal()
        try:
            vehicles = db.query(Vehicle).filter(Vehicle.status == "inactivity").all()
            instruction = (
                "⚠️ Vui lòng cung cấp <b>Biển Số</b> xe cần nhận.\n"
                "Cú pháp: <code>/other_receive_vehicle [biển số]</code>"
            )
            if not vehicles:
                await message.reply_text(
                    f"{instruction}\n\nHiện tại không có xe nào ở trạng thái <b>Không hoạt động</b> để nhận.",
                    parse_mode=ParseMode.HTML
                )
                return

            vehicle_list = "<b>Danh sách xe có thể nhận:</b>\n\n"
            for v in vehicles:
                vehicle_list += (
                    f"<b>Loại xe:</b> {v.vehicle_type or 'N/A'}\n"
                    f"<b>Màu:</b> {v.color or 'N/A'}\n"
                    f"<b>Biển số:</b> <code>{v.license_plate}</code>\n"
                    f"-------------------\n"
                )
            await message.reply_text(f"{instruction}\n\n{vehicle_list}", parse_mode=ParseMode.HTML)
        except Exception as e:
            LogError(f"Error listing vehicles: {e}", LogType.SYSTEM_STATUS)
            await message.reply_text("❌ Có lỗi xảy ra khi tải danh sách xe.")
        finally:
            db.close()
        return

    license_plate = args[1].strip().strip('"').strip("'")
    db = SessionLocal()
    try:
        vehicle = get_vehicle_by_license_plate(db, license_plate)
        if not vehicle:
            await message.reply_text(
                f"❌ Không tìm thấy xe có biển số <code>{license_plate}</code> trong hệ thống.",
                parse_mode=ParseMode.HTML
            )
            return

        # Kiểm tra trạng thái
        if vehicle.status == "activited":
            # Tìm người đang giữ xe
            last_receive = db.query(VehicleActivityLog).filter(
                VehicleActivityLog.vehicle_id == vehicle.id,
                VehicleActivityLog.action == "RECEIVE"
            ).order_by(VehicleActivityLog.timestamp.desc()).first()
            holder = f"@{last_receive.telegram_username}" if last_receive else "Không rõ"
            await message.reply_text(
                f"⚠️ Xe <code>{license_plate}</code> đang ở trạng thái <b>Đang hoạt động</b>.\n"
                f"Người giữ xe hiện tại: <b>{holder}</b>",
                parse_mode=ParseMode.HTML
            )
            return

        if vehicle.status == "is_removed":
            await message.reply_text(
                f"⚠️ Xe <code>{license_plate}</code> đã bị xóa khỏi hệ thống, không thể nhận.",
                parse_mode=ParseMode.HTML
            )
            return

        # Cập nhật trạng thái
        vehicle.status = "activited"
        db.commit()
        db.refresh(vehicle)

        # Ghi log hoạt động
        from app.schemas.vehicle import VehicleActivityLogCreate
        log_in = VehicleActivityLogCreate(
            vehicle_id=vehicle.id,
            telegram_username=message.from_user.username or message.from_user.first_name,
            action="RECEIVE"
        )
        create_vehicle_activity_log(db, obj_in=log_in)

        username = message.from_user.username or message.from_user.first_name
        result_text = (
            f"✅ <b>Nhận xe thành công!</b>\n\n"
            f"<b>Loại xe:</b> {vehicle.vehicle_type or 'N/A'}\n"
            f"<b>Thương hiệu:</b> {vehicle.brand or 'N/A'} {vehicle.model or ''}\n"
            f"<b>Màu:</b> {vehicle.color or 'N/A'}\n"
            f"<b>Biển số:</b> <code>{vehicle.license_plate}</code>\n"
            f"<b>Chủ xe:</b> {vehicle.owner_name or 'N/A'}\n"
            f"<b>Người nhận:</b> @{username}\n"
            f"<b>Trạng thái:</b> Không hoạt động → Đang hoạt động"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[OtherReceiveVehicle] @{username} received vehicle {license_plate}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in other_receive_vehicle_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra khi nhận xe: {str(e)}")
    finally:
        db.close()


# ===================== TRẢ XE =====================

@bot.on_message(filters.command(["other_return_vehicle", "other_tra_xe"]) | filters.regex(r"^@\w+\s+/(other_return_vehicle|other_tra_xe)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_vehicle")
async def other_return_vehicle_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_return_vehicle", "other_tra_xe"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Biển Số</b> xe cần trả.\n"
            "Cú pháp: <code>/other_return_vehicle [biển số]</code>",
            parse_mode=ParseMode.HTML
        )
        return

    license_plate = args[1].strip().strip('"').strip("'")
    db = SessionLocal()
    try:
        vehicle = get_vehicle_by_license_plate(db, license_plate)
        if not vehicle:
            await message.reply_text(
                f"❌ Không tìm thấy xe có biển số <code>{license_plate}</code> trong hệ thống.",
                parse_mode=ParseMode.HTML
            )
            return

        # Kiểm tra trạng thái
        if vehicle.status == "inactivity":
            await message.reply_text(
                f"⚠️ Xe <code>{license_plate}</code> hiện đang ở trạng thái <b>Không hoạt động</b>, không cần trả.",
                parse_mode=ParseMode.HTML
            )
            return

        if vehicle.status == "is_removed":
            await message.reply_text(
                f"⚠️ Xe <code>{license_plate}</code> đã bị xóa khỏi hệ thống.",
                parse_mode=ParseMode.HTML
            )
            return

        # Kiểm tra người trả có phải người nhận không
        current_username = message.from_user.username or message.from_user.first_name
        last_receive = db.query(VehicleActivityLog).filter(
            VehicleActivityLog.vehicle_id == vehicle.id,
            VehicleActivityLog.action == "RECEIVE"
        ).order_by(VehicleActivityLog.timestamp.desc()).first()

        if last_receive and last_receive.telegram_username != current_username:
            await message.reply_text(
                f"⚠️ Bạn không phải là người đang giữ xe <code>{license_plate}</code>.\n"
                f"Người giữ xe hiện tại: <b>@{last_receive.telegram_username}</b>",
                parse_mode=ParseMode.HTML
            )
            return

        # Cập nhật trạng thái
        vehicle.status = "inactivity"
        db.commit()
        db.refresh(vehicle)

        # Ghi log hoạt động
        from app.schemas.vehicle import VehicleActivityLogCreate
        log_in = VehicleActivityLogCreate(
            vehicle_id=vehicle.id,
            telegram_username=current_username,
            action="RETURN"
        )
        create_vehicle_activity_log(db, obj_in=log_in)

        result_text = (
            f"✅ <b>Trả xe thành công!</b>\n\n"
            f"<b>Loại xe:</b> {vehicle.vehicle_type or 'N/A'}\n"
            f"<b>Thương hiệu:</b> {vehicle.brand or 'N/A'} {vehicle.model or ''}\n"
            f"<b>Màu:</b> {vehicle.color or 'N/A'}\n"
            f"<b>Biển số:</b> <code>{vehicle.license_plate}</code>\n"
            f"<b>Người trả:</b> @{current_username}\n"
            f"<b>Trạng thái:</b> Đang hoạt động → Không hoạt động"
        )
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[OtherReturnVehicle] @{current_username} returned vehicle {license_plate}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in other_return_vehicle_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra khi trả xe: {str(e)}")
    finally:
        db.close()


# ===================== XEM LỊCH SỬ XE =====================

@bot.on_message(filters.command(["other_check_log_vehicle", "other_lich_su_xe"]) | filters.regex(r"^@\w+\s+/(other_check_log_vehicle|other_lich_su_xe)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)
@require_project_name("Other")
@require_group_role("main")
@require_custom_title("main_vehicle")
async def other_check_log_vehicle_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["other_check_log_vehicle", "other_lich_su_xe"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text(
            "⚠️ Vui lòng cung cấp <b>Biển Số</b> xe cần xem lịch sử.\n"
            "Cú pháp: <code>/other_check_log_vehicle [biển số]</code>",
            parse_mode=ParseMode.HTML
        )
        return

    license_plate = args[1].strip().strip('"').strip("'")
    db = SessionLocal()
    try:
        vehicle = get_vehicle_by_license_plate(db, license_plate)
        if not vehicle:
            await message.reply_text(
                f"❌ Không tìm thấy xe có biển số <code>{license_plate}</code> trong hệ thống.",
                parse_mode=ParseMode.HTML
            )
            return

        # Đếm tổng số RECEIVE log
        total_receive = db.query(VehicleActivityLog).filter(
            VehicleActivityLog.vehicle_id == vehicle.id,
            VehicleActivityLog.action == "RECEIVE"
        ).count()

        if total_receive == 0:
            await message.reply_text(
                f"ℹ️ Xe <code>{license_plate}</code> chưa có lịch sử hoạt động nào.",
                parse_mode=ParseMode.HTML
            )
            return

        status_display = "Đang hoạt động" if vehicle.status == "activited" else "Đã xóa" if vehicle.status == "is_removed" else "Không hoạt động"

        # Nếu > 20 log → xuất file txt
        if total_receive > 20:
            all_receive_logs = db.query(VehicleActivityLog).filter(
                VehicleActivityLog.vehicle_id == vehicle.id,
                VehicleActivityLog.action == "RECEIVE"
            ).order_by(VehicleActivityLog.timestamp.desc()).all()

            file_content = (
                f"LỊCH SỬ HOẠT ĐỘNG XE\n"
                f"{'='*40}\n"
                f"Biển số: {vehicle.license_plate}\n"
                f"Loại xe: {vehicle.vehicle_type or 'N/A'}\n"
                f"Thương hiệu: {vehicle.brand or 'N/A'} {vehicle.model or ''}\n"
                f"Chủ xe: {vehicle.owner_name or 'N/A'}\n"
                f"Trạng thái hiện tại: {status_display}\n"
                f"Tổng lượt nhận xe: {total_receive}\n"
                f"{'='*40}\n\n"
            )

            for idx, log in enumerate(reversed(all_receive_logs), 1):
                receive_time = log.timestamp.strftime('%H:%M %d/%m/%Y')

                return_log = db.query(VehicleActivityLog).filter(
                    VehicleActivityLog.vehicle_id == vehicle.id,
                    VehicleActivityLog.action == "RETURN",
                    VehicleActivityLog.timestamp > log.timestamp
                ).order_by(VehicleActivityLog.timestamp.asc()).first()

                return_time = return_log.timestamp.strftime('%H:%M %d/%m/%Y') if return_log else "Chưa trả"

                file_content += (
                    f"#{idx}\n"
                    f"  Tài xế:   @{log.telegram_username}\n"
                    f"  Nhận xe:  {receive_time}\n"
                    f"  Trả xe:   {return_time}\n"
                    f"{'-'*40}\n"
                )

            import os
            file_name = f"log_xe_{license_plate.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            file_path = os.path.join("tmp", file_name)
            os.makedirs("tmp", exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            await message.reply_document(
                document=file_path,
                caption=f"<b>LỊCH SỬ HOẠT ĐỘNG XE</b>\nBiển số: <code>{license_plate}</code>\nTổng: {total_receive} lượt nhận xe",
                parse_mode=ParseMode.HTML
            )

            os.remove(file_path)
            return

        # <= 20 log → hiển thị inline
        receive_logs = db.query(VehicleActivityLog).filter(
            VehicleActivityLog.vehicle_id == vehicle.id,
            VehicleActivityLog.action == "RECEIVE"
        ).order_by(VehicleActivityLog.timestamp.desc()).all()

        response = (
            f"<b>LỊCH SỬ HOẠT ĐỘNG XE</b>\n\n"
            f"<b>Biển số:</b> <code>{vehicle.license_plate}</code>\n"
            f"<b>Loại xe:</b> {vehicle.vehicle_type or 'N/A'}\n"
            f"<b>Thương hiệu:</b> {vehicle.brand or 'N/A'} {vehicle.model or ''}\n"
            f"<b>Chủ xe:</b> {vehicle.owner_name or 'N/A'}\n"
            f"<b>Trạng thái hiện tại:</b> {status_display}\n"
            f"-------------------\n\n"
        )

        for log in reversed(receive_logs):
            receive_time = log.timestamp.strftime('%H:%M %d/%m/%Y')

            return_log = db.query(VehicleActivityLog).filter(
                VehicleActivityLog.vehicle_id == vehicle.id,
                VehicleActivityLog.action == "RETURN",
                VehicleActivityLog.timestamp > log.timestamp
            ).order_by(VehicleActivityLog.timestamp.asc()).first()

            return_time = return_log.timestamp.strftime('%H:%M %d/%m/%Y') if return_log else "<i>Chưa trả</i>"

            response += (
                f"<b>Tài xế:</b> @{log.telegram_username}\n"
                f"<b>Nhận xe:</b> {receive_time}\n"
                f"<b>Trả xe:</b> {return_time}\n"
                f"-------------------\n"
            )

        if len(response) > 4096:
            for i in range(0, len(response), 4000):
                await message.reply_text(response[i:i+4000], parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(response, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in other_check_log_vehicle_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra khi tra cứu lịch sử xe: {str(e)}")
    finally:
        db.close()
