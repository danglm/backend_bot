from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
from bot.utils.bot import bot
from bot.utils.utils import check_command_target, require_user_type, require_project_name, require_group_role
from bot.utils.enums import UserType
from bot.utils.logger import LogInfo, LogError, LogType
from app.db.session import SessionLocal
import datetime

# --- Rental: Create Customer ---
@bot.on_message(filters.command(["rental_create_customer", "rental_tao_khach_hang"]) | filters.regex(r"^@\w+\s+/(rental_create_customer|rental_tao_khach_hang)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
@require_group_role("main")
async def rental_create_customer_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_create_customer", "rental_tao_khach_hang"])
    if args is None: return

    lines = message.text.strip().split("\n")
    if len(lines) < 3:
        form_template = """<b>FORM TẠO KHÁCH HÀNG CHO THUÊ</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/rental_create_customer
Tên Nhóm: 
Tên Khách Hàng: 
Liên Hệ Khách Hàng: 
Số Điện Thoại: 
</pre>

<i>Ví dụ liên hệ: @username hoặc ID số. Tên nhóm (tuỳ chọn)</i>"""
        await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        return

    # Parse Form
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    group_name = data.get("Tên Nhóm", "")
    customer_name = data.get("Tên Khách Hàng", "")
    contact_info = data.get("Liên Hệ Khách Hàng", "")
    number_phone = data.get("Số Điện Thoại", "")

    if not customer_name or not contact_info:
        await message.reply_text("⚠️ <b>Tên Khách Hàng</b> và <b>Liên Hệ Khách Hàng</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.rental import RentalCustomer

        chat_id = str(message.chat.id)
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        if not current_project_member:
            await message.reply_text("⚠️ Nhóm này chưa được đồng bộ vào dự án nào. Vui lòng sử dụng lệnh /syncchat trước.")
            return

        project_id = current_project_member.project_id

        # Check if contact is in the valid member list
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member",
            TelegramProjectMember.slot_name.like("member%")
        ).all()

        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))
            
        if contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Khách hàng <b>{contact_info}</b> chưa có mặt trong nhóm thành viên (member) của dự án. Vui lòng mời họ vào nhóm member và dùng lệnh /syncchat để hệ thống cập nhật trước khi tạo khách.", parse_mode=ParseMode.HTML)
            return

        # Check duplicate
        existing = db.query(RentalCustomer).filter(RentalCustomer.contact_info == contact_info).first()
        if existing:
            await message.reply_text(f"⚠️ Khách hàng cho thuê có thông tin liên hệ <b>{contact_info}</b> đã tồn tại trong hệ thống.", parse_mode=ParseMode.HTML)
            return

        new_customer = RentalCustomer(
            group_name=group_name,
            customer_name=customer_name,
            contact_info=contact_info,
            number_phone=number_phone
        )
        db.add(new_customer)
        db.commit()

        await message.reply_text(f"✅ Đã tạo khách hàng cho thuê <b>{customer_name}</b> thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[RentalCreateCustomer] Created rental customer {customer_name} ({contact_info}) by {message.from_user.id}", LogType.SYSTEM_STATUS)
    except Exception as e:
        db.rollback()
        LogError(f"Error in rental_create_customer_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý lưu khách hàng.")
    finally:
        db.close()


import re

def _parse_float_rental(val_str: str) -> float:
    if not val_str: return 0.0
    v = re.sub(r'[^\d\.,-]', '', str(val_str))
    if not v: return 0.0
    if "," in v and "." in v:
        if v.rfind(",") > v.rfind("."):
            v = v.replace(".", "").replace(",", ".")
        else:
            v = v.replace(",", "")
    elif "," in v:
        if len(v.split(",")[-1]) == 3:
            v = v.replace(",", "")
        else:
            v = v.replace(",", ".")
    elif "." in v:
        if len(v.split(".")[-1]) == 3:
            v = v.replace(".", "")
    if v.count('.') > 1:
        parts = v.split('.')
        v = "".join(parts[:-1]) + "." + parts[-1]
    return float(v)


# --- Rental: Create Contract ---
@bot.on_message(filters.command(["rental_create_contract", "rental_tao_hop_dong"]) | filters.regex(r"^@\w+\s+/(rental_create_contract|rental_tao_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
@require_group_role("main")
async def rental_create_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_create_contract", "rental_tao_hop_dong"])
    if args is None: return

    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.rental import RentalCustomer, Rental, RentalStatus

        lines = message.text.strip().split("\n")
        if len(lines) < 3:
            if len(args) < 2:
                await message.reply_text("⚠️ Vui lòng cung cấp thông tin liên hệ của khách hàng. Lệnh ví dụ: <code>/rental_create_contract @username</code>", parse_mode=ParseMode.HTML)
                return

            contact_info = args[1]
            customer = db.query(RentalCustomer).filter(RentalCustomer.contact_info == contact_info).first()
            if not customer:
                await message.reply_text(f"⚠️ Khách hàng <b>{contact_info}</b> chưa tồn tại trong hệ thống cho thuê. Vui lòng tạo khách hàng bằng lệnh /rental_create_customer trước.", parse_mode=ParseMode.HTML)
                return

            form_template = f"""<b>FORM TẠO HỢP ĐỒNG CHO THUÊ</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/rental_create_contract {customer.contact_info}
Tên Nhóm: {customer.group_name or ""}
Tên Khách Hàng: {customer.customer_name or ""}
Liên Hệ Khách Hàng: {customer.contact_info}
Mã Hợp Đồng: 
Mã Bất Động Sản: 
Loại Hợp Đồng: 
Ngày Bắt Đầu Thuê (dd/mm/yyyy): 
Ngày Kết Thúc Thuê (dd/mm/yyyy): 
Tiền Cọc: 
Tiền Thuê / Tháng: 
Công Nợ: 0
</pre>

<i>Ví dụ mã hợp đồng: LMD-HD220101. Loại hợp đồng gồm (Nhà nguyên căn, Phòng trọ, Căn hộ, Mặt bằng, v.v.)</i>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return

        # If user actually submitted data in the form format
        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        contact_info = data.get("Liên Hệ Khách Hàng", "")
        if not contact_info and len(args) > 1:
            contact_info = args[1]

        customer = db.query(RentalCustomer).filter(RentalCustomer.contact_info == contact_info).first()
        if not customer:
            await message.reply_text(f"⚠️ Khách hàng <b>{contact_info}</b> chưa tồn tại trong hệ thống cho thuê. Vui lòng tạo khách trước.", parse_mode=ParseMode.HTML)
            return

        parse_float = _parse_float_rental

        def parse_date(date_str: str):
            if not date_str: return None
            try:
                import datetime
                return datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
            except:
                return None

        contract_id = data.get("Mã Hợp Đồng", "")
        if not contract_id:
            await message.reply_text("⚠️ <b>Mã Hợp Đồng</b> là bắt buộc.", parse_mode=ParseMode.HTML)
            return

        existing_contract = db.query(Rental).filter(Rental.contract_id == contract_id).first()
        if existing_contract:
            await message.reply_text(f"⚠️ Hợp đồng cho thuê mã <b>{contract_id}</b> đã tồn tại.", parse_mode=ParseMode.HTML)
            return

        real_estate_id = data.get("Mã Bất Động Sản", "")
        type_contract = data.get("Loại Hợp Đồng", "")
        start_rental = parse_date(data.get("Ngày Bắt Đầu Thuê (dd/mm/yyyy)", ""))
        end_rental = parse_date(data.get("Ngày Kết Thúc Thuê (dd/mm/yyyy)", ""))
        deposit = parse_float(data.get("Tiền Cọc", "0"))
        monthly_rental = parse_float(data.get("Tiền Thuê / Tháng", "0"))
        rental_debt = parse_float(data.get("Công Nợ", "0"))

        from app.schemas.rental import RentalCreate
        from app.crud.rental import create_rental

        new_contract = RentalCreate(
            customer_id=customer.id,
            contract_id=contract_id,
            real_estate_id=real_estate_id,
            type_contract=type_contract,
            start_rental=start_rental,
            end_rental=end_rental,
            deposit=deposit,
            monthly_rental=monthly_rental,
            rental_debt=rental_debt,
            status=RentalStatus.ACTIVE.value
        )

        create_rental(db, obj_in=new_contract)
        await message.reply_text(f"✅ Đã tạo hợp đồng cho thuê <b>{contract_id}</b> cho khách hàng <b>{customer.customer_name}</b> thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[RentalCreateContract] Created rental contract {contract_id} for {customer.customer_name} by {message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in rental_create_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý tạo hợp đồng cho thuê.")
    finally:
        db.close()


# --- Rental: Check Customer ---
@bot.on_message(filters.command(["rental_check_customer", "rental_kiem_tra_khach_hang"]) | filters.regex(r"^@\w+\s+/(rental_check_customer|rental_kiem_tra_khach_hang)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
async def rental_check_customer_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_check_customer", "rental_kiem_tra_khach_hang"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp thông tin liên hệ. Lệnh ví dụ: <code>/rental_check_customer @username</code>", parse_mode=ParseMode.HTML)
        return

    contact_info = args[1]
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.rental import RentalCustomer, Rental, RentalStatus

        chat_id = str(message.chat.id)
        current_group = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()
        project_id = current_group.project_id

        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member",
            TelegramProjectMember.slot_name.like("member%")
        ).all()

        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))

        if contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Không tìm thấy <b>{contact_info}</b> trong nhóm thành viên (member) của dự án này.", parse_mode=ParseMode.HTML)
            return

        customer = db.query(RentalCustomer).filter(RentalCustomer.contact_info == contact_info).first()
        if not customer:
            await message.reply_text(f"⚠️ Khách hàng <b>{contact_info}</b> chưa tồn tại trong hệ thống cho thuê.", parse_mode=ParseMode.HTML)
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        def fmt_dt(dt):
            if not dt: return "N/A"
            return dt.strftime('%d/%m/%Y')

        reply_lines = [
            f"<b>THÔNG TIN KHÁCH HÀNG CHO THUÊ</b>",
            f"Tên Nhóm: <b>{customer.group_name or 'N/A'}</b>",
            f"Tên Khách Hàng: <b>{customer.customer_name}</b>",
            f"Liên Hệ: <b>{customer.contact_info}</b>",
            f"Số Điện Thoại: <b>{customer.number_phone or 'N/A'}</b>",
            f"---------------------------",
            f"<b>DANH SÁCH HỢP ĐỒNG CHO THUÊ</b>"
        ]

        rentals = db.query(Rental).filter(Rental.customer_id == customer.id).all()
        if not rentals:
            reply_lines.append("<i>Khách hàng chưa có hợp đồng cho thuê nào.</i>")
        else:
            for idx, r in enumerate(rentals, 1):
                if r.status == RentalStatus.ACTIVE.value:
                    status_label = "Đang thuê"
                elif r.status == RentalStatus.EXPIRED.value:
                    status_label = "Hết hạn"
                elif r.status == RentalStatus.CANCELLED.value:
                    status_label = "Đã hủy"
                elif r.status == RentalStatus.BAD_DEBT.value:
                    status_label = "Nợ xấu"
                else:
                    status_label = "Không rõ"

                reply_lines.append(
                    f"{idx}. {status_label} <b>{r.contract_id}</b>"
                    f" ({r.type_contract or 'N/A'})"
                    f"\n        BĐS: {r.real_estate_id or 'N/A'}"
                    f"\n        Thời gian thuê: {fmt_dt(r.start_rental)} - {fmt_dt(r.end_rental)}"
                    f"\n        Tiền thuê: <b>{fmt_num(r.monthly_rental):,}</b>/tháng"
                    f"\n        Cọc: {fmt_num(r.deposit):,}"
                    f"\n        Công nợ: <b>{fmt_num(r.rental_debt):,}</b>"
                )

        await message.reply_text("\n".join(reply_lines), parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in rental_check_customer_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình truy xuất khách hàng cho thuê.")
    finally:
        db.close()


# --- Rental: Check Contract ---
@bot.on_message(filters.command(["rental_check_contract", "rental_kiem_tra_hop_dong"]) | filters.regex(r"^@\w+\s+/(rental_check_contract|rental_kiem_tra_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)
@require_project_name("Rental")
@require_group_role("main", "member")
async def rental_check_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_check_contract", "rental_kiem_tra_hop_dong"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng. Lệnh ví dụ: <code>/rental_check_contract LMD-HD220101</code>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1]
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.rental import RentalCustomer, Rental, RentalStatus

        # Check if chat is a "main" group
        chat_id = str(message.chat.id)
        current_group = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()
        project_id = current_group.project_id

        # Get valid contacts for project isolation
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member",
            TelegramProjectMember.slot_name.like("member%")
        ).all()

        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))

        contract = db.query(Rental).filter(Rental.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng cho thuê <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        # Find customer for this contract
        customer = db.query(RentalCustomer).filter(RentalCustomer.id == contract.customer_id).first()
        if not customer or customer.contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không thuộc về khách hàng trong dự án hiện tại.", parse_mode=ParseMode.HTML)
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        def fmt_dt(dt):
            if not dt: return "N/A"
            return dt.strftime('%d/%m/%Y')

        if contract.status == RentalStatus.ACTIVE.value:
            status_label = "Đang thuê"
        elif contract.status == RentalStatus.EXPIRED.value:
            status_label = "Hết hạn"
        elif contract.status == RentalStatus.CANCELLED.value:
            status_label = "Đã hủy"
        elif contract.status == RentalStatus.BAD_DEBT.value:
            status_label = "Nợ xấu"
        else:
            status_label = "Không rõ"

        reply_lines = [
            f"<b>THÔNG TIN HỢP ĐỒNG CHO THUÊ: {contract.contract_id}</b>",
            f"Trạng thái: <b>{status_label}</b>",
            f"Loại hợp đồng: <b>{contract.type_contract or 'N/A'}</b>",
            f"Tên: <b>{customer.customer_name}</b>",
            f"Liên hệ: <b>{customer.contact_info}</b>",
            f"Số Điện Thoại: <b>{customer.number_phone or 'N/A'}</b>",
            f"Mã BĐS: <b>{contract.real_estate_id or 'N/A'}<b>",
            f"Tiền Cọc: <b>{fmt_num(contract.deposit):,} VNĐ</b>",
            f"Tiền Thuê / Tháng: <b>{fmt_num(contract.monthly_rental):,} VNĐ</b>",
            f"Công Nợ: <b>{fmt_num(contract.rental_debt):,} VNĐ</b>",
            f"Ngày Bắt Đầu Thuê: <b>{fmt_dt(contract.start_rental)}</b>",
            f"Ngày Kết Thúc Thuê: <b>{fmt_dt(contract.end_rental)}</b>",
        ]

        await message.reply_text("\n".join(reply_lines), parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in rental_check_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình truy xuất hợp đồng cho thuê.")
    finally:
        db.close()


# --- Rental: Check Debt (Xem Công Nợ Hiện Tại) ---
@bot.on_message(filters.command(["rental_check_debt", "rental_xem_cong_no"]) | filters.regex(r"^@\w+\s+/(rental_check_debt|rental_xem_cong_no)\b"))
@require_user_type(UserType.MEMBER)
@require_project_name("Rental")
@require_group_role("member")
async def rental_check_debt_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_check_debt", "rental_xem_cong_no"])
    if args is None: return

    db = SessionLocal()
    try:
        from app.models.rental import RentalCustomer, Rental, RentalStatus

        # Lấy @username của người gọi lệnh
        username = message.from_user.username
        if not username:
            await message.reply_text("⚠️ Tài khoản của bạn chưa có username Telegram. Vui lòng cài đặt username trước.", parse_mode=ParseMode.HTML)
            return

        contact_info = f"@{username}"

        # Tìm khách hàng theo contact_info
        customer = db.query(RentalCustomer).filter(RentalCustomer.contact_info == contact_info).first()
        if not customer:
            await message.reply_text(f"ℹ️ Không tìm thấy thông tin khách hàng cho <b>{contact_info}</b>.", parse_mode=ParseMode.HTML)
            return

        # Lấy các hợp đồng đang thuê / hết hạn (chưa hủy)
        active_rentals = db.query(Rental).filter(
            Rental.customer_id == customer.id,
            Rental.status.in_([RentalStatus.ACTIVE.value, RentalStatus.EXPIRED.value])
        ).all()

        if not active_rentals:
            await message.reply_text(f"ℹ️ <b>{customer.customer_name}</b>, bạn hiện không có hợp đồng cho thuê nào.", parse_mode=ParseMode.HTML)
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        def fmt_dt(dt):
            if not dt: return "N/A"
            return dt.strftime('%d/%m/%Y')

        total_debt = sum([(r.rental_debt or 0) for r in active_rentals])
        total_monthly = sum([(r.monthly_rental or 0) for r in active_rentals])

        contract_lines = []
        for idx, r in enumerate(active_rentals, 1):
            status_label = "Đang thuê" if r.status == RentalStatus.ACTIVE.value else "Hết hạn"
            contract_lines.append(
                f"{idx}. <b>{r.contract_id}</b> ({r.type_contract or 'N/A'}) - {status_label}\n"
                f"   Tiền thuê: <b>{fmt_num(r.monthly_rental):,}</b>/tháng\n"
                f"   Công nợ: <b>{fmt_num(r.rental_debt or 0):,}</b>\n"
                f"   BĐS: {r.real_estate_id or 'N/A'}\n"
                f"   Thuê: {fmt_dt(r.start_rental)} - {fmt_dt(r.end_rental)}"
            )

        reply_lines = [
            f"<b>CÔNG NỢ HIỆN TẠI</b>",
            f"Khách hàng: <b>{customer.customer_name}</b> ({contact_info})",
            f"---------------------------",
            f"Tổng hợp đồng: <b>{len(active_rentals)}</b>",
            f"Tổng tiền thuê: <b>{fmt_num(total_monthly):,}</b>/tháng",
            f"Tổng nợ: <b>{fmt_num(total_debt):,}</b>",
            f"---------------------------",
        ] + contract_lines

        await message.reply_text("\n".join(reply_lines), parse_mode=ParseMode.HTML)
        LogInfo(f"[RentalCheckDebt] {contact_info} checked their debt: {len(active_rentals)} contracts, total: {total_debt}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in rental_check_debt_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra khi truy xuất công nợ.")
    finally:
        db.close()


# --- Rental: Extend Contract ---
@bot.on_message(filters.command(["rental_extend_contract", "rental_gia_han_hop_dong"]) | filters.regex(r"^@\w+\s+/(rental_extend_contract|rental_gia_han_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
@require_group_role("main")
async def rental_extend_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_extend_contract", "rental_gia_han_hop_dong"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng.\nCú pháp: <code>/rental_extend_contract [Mã HĐ] [Số tháng]</code>\nVí dụ: <code>/rental_extend_contract LMD-HD220101 3</code>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1].strip()
    months_to_add = 1
    if len(args) >= 3:
        try:
            months_to_add = int(args[2].strip())
            if months_to_add <= 0 or months_to_add > 60:
                raise ValueError()
        except ValueError:
            await message.reply_text("⚠️ Số tháng gia hạn không hợp lệ (phải là số nguyên từ 1 đến 60).", parse_mode=ParseMode.HTML)
            return

    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.rental import RentalCustomer, Rental, RentalStatus


        contract = db.query(Rental).filter(Rental.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng cho thuê nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        if contract.status == RentalStatus.CANCELLED.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã bị hủy, không thể gia hạn.", parse_mode=ParseMode.HTML)
            return

        if not contract.end_rental:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> chưa có ngày kết thúc thuê, không thể gia hạn.", parse_mode=ParseMode.HTML)
            return

        def add_months_to_date(source_date, months):
            import calendar
            month = source_date.month - 1 + months
            year = source_date.year + month // 12
            month = month % 12 + 1
            day = min(source_date.day, calendar.monthrange(year, month)[1])
            return datetime.date(year, month, day)

        new_end_rental = add_months_to_date(contract.end_rental, months_to_add)

        customer = db.query(RentalCustomer).filter(RentalCustomer.id == contract.customer_id).first()

        text = (
            f"<b>THÔNG TIN GIA HẠN HỢP ĐỒNG CHO THUÊ</b>\n\n"
            f"- Tên Khách Hàng: <b>{customer.customer_name if customer else 'N/A'}</b>\n"
            f"- Mã Hợp Đồng: <b>{contract.contract_id}</b>\n"
            f"- Loại Hợp Đồng: <b>{contract.type_contract or 'N/A'}</b>\n"
            f"- Thời gian gia hạn thêm: <b>{months_to_add} Tháng</b>\n\n"
            f"- Ngày kết thúc thuê: <b>{contract.end_rental.strftime('%d/%m/%Y')}</b>\n"
            f"- Ngày kết thúc thuê mới: <b>{new_end_rental.strftime('%d/%m/%Y')}</b>\n\n"
            f"<i>Lưu ý: Nếu hợp đồng đang Hết hạn, bot sẽ tự động đưa về Đang thuê.</i>"
        )

        buttons = [
            [
                InlineKeyboardButton("Xác nhận gia hạn", callback_data=f"rec_confirm_{contract.id}_{months_to_add}"),
                InlineKeyboardButton("Hủy", callback_data="rec_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in rental_extend_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rec_confirm_([^_]+)_(\d+)$"))
async def rental_extend_contract_confirm_callback(client, callback_query: CallbackQuery):
    contract_uuid = callback_query.matches[0].group(1)
    months_to_add = int(callback_query.matches[0].group(2))
    db = SessionLocal()
    try:
        from app.models.rental import Rental, RentalCustomer, RentalStatus
        from app.models.telegram import TelegramProjectMember

        contract = db.query(Rental).filter(Rental.id == contract_uuid).first()
        if not contract:
            await callback_query.message.edit_text("⚠️ Hợp đồng không tồn tại hoặc đã bị xóa.")
            return

        def add_months_to_date(source_date, months):
            import calendar
            month = source_date.month - 1 + months
            year = source_date.year + month // 12
            month = month % 12 + 1
            day = min(source_date.day, calendar.monthrange(year, month)[1])
            return datetime.date(year, month, day)

        new_end_rental = add_months_to_date(contract.end_rental, months_to_add)
        old_end_rental_str = contract.end_rental.strftime('%d/%m/%Y')
        new_end_rental_str = new_end_rental.strftime('%d/%m/%Y')

        contract.end_rental = new_end_rental

        # Reset expired back to active
        if contract.status == RentalStatus.EXPIRED.value:
            contract.status = RentalStatus.ACTIVE.value

        customer = db.query(RentalCustomer).filter(RentalCustomer.id == contract.customer_id).first()

        # Find member group for notification
        customer_contact = customer.contact_info if customer else ""
        member_chat_id = None

        if customer_contact:
            customer_links = db.query(TelegramProjectMember).filter(
                TelegramProjectMember.role == "member",
                TelegramProjectMember.slot_name.like("member%")
            ).all()
            for link in customer_links:
                link_username = f"@{link.user_name}" if link.user_name else ""
                link_userid = str(link.user_id)
                if customer_contact == link_username or customer_contact == link_userid:
                    member_chat_id = link.chat_id
                    break

        db.commit()

        success_text = (
            f"✅ <b>Gia hạn thành công hợp đồng cho thuê {contract.contract_id}</b>\n\n"
            f"- Khách hàng: <b>{customer.customer_name if customer else 'N/A'}</b>\n"
            f"- Phương thức: <b>Gia hạn {months_to_add} tháng</b>\n"
            f"- Ngày kết thúc thuê mới: <b>{new_end_rental_str}</b> (cũ: {old_end_rental_str})\n"
        )

        await callback_query.message.edit_text(success_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[RentalExtendContract] User {callback_query.from_user.id} extended rental contract {contract.contract_id}", LogType.SYSTEM_STATUS)

        # Send Member Notification
        if member_chat_id:
            member_alert = (
                f"🔔 <b>THÔNG BÁO TỪ QUẢN TRỊ VIÊN</b>\n\n"
                f"Hợp đồng cho thuê mã <b>{contract.contract_id}</b> của Quý khách đã được gia hạn thành công thêm <b>{months_to_add} tháng</b>.\n\n"
                f"<b>Ngày kết thúc thuê cập nhật mới nhất: {new_end_rental_str}</b>\n"
                f"Quý khách vui lòng lưu ý thời gian kết thúc mới. Xin cảm ơn!"
            )
            try:
                await client.send_message(
                    chat_id=int(member_chat_id),
                    text=member_alert,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                LogError(f"Failed to send rental extend alert to member group {member_chat_id}: {e}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in rec_confirm callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi xác nhận gia hạn.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rec_cancel$"))
async def rental_extend_contract_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("❌ Đã hủy thao tác gia hạn.")


# --- Rental: Cancel Contract ---
@bot.on_message(filters.command(["rental_cancel_contract", "rental_huy_hop_dong"]) | filters.regex(r"^@\w+\s+/(rental_cancel_contract|rental_huy_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
@require_group_role("main")
async def rental_cancel_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_cancel_contract", "rental_huy_hop_dong"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng. Lệnh ví dụ: <code>/rental_cancel_contract LMD-HD220101</code>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1]
    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.rental import RentalCustomer, Rental, RentalStatus

        current_group = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()
        project_id = current_group.project_id

        # Get valid contacts for project isolation
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member",
            TelegramProjectMember.slot_name.like("member%")
        ).all()

        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))

        contract = db.query(Rental).filter(Rental.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng cho thuê nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        customer = db.query(RentalCustomer).filter(RentalCustomer.id == contract.customer_id).first()
        if not customer or customer.contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không thuộc về khách hàng nào trong dự án hiện tại.", parse_mode=ParseMode.HTML)
            return

        if contract.status == RentalStatus.CANCELLED.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã bị hủy từ trước.", parse_mode=ParseMode.HTML)
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        def fmt_dt(dt):
            if not dt: return "N/A"
            return dt.strftime('%d/%m/%Y')

        if contract.status == RentalStatus.ACTIVE.value:
            status_label = "Đang thuê"
        elif contract.status == RentalStatus.EXPIRED.value:
            status_label = "Hết hạn"
        elif contract.status == RentalStatus.BAD_DEBT.value:
            status_label = "Nợ xấu"
        else:
            status_label = "Không rõ"

        monthly = fmt_num(contract.monthly_rental)
        deposit = fmt_num(contract.deposit)
        debt = fmt_num(contract.rental_debt)

        text = (
            f"<b>THÔNG TIN HỢP ĐỒNG CHO THUÊ</b>\n\n"
            f"- Tên Khách Hàng: <b>{customer.customer_name}</b>\n"
            f"- Mã Hợp Đồng: <b>{contract.contract_id}</b>\n"
            f"- Trạng Thái: <b>{status_label}</b>\n"
            f"- Loại Hợp Đồng: <b>{contract.type_contract or 'N/A'}</b>\n"
            f"- Tiền Thuê / Tháng: <b>{monthly:,} VNĐ</b>\n"
            f"- Tiền Cọc: <b>{deposit:,} VNĐ</b>\n"
            f"- Công Nợ: <b>{debt:,} VNĐ</b>\n"
            f"- Thuê: <b>{fmt_dt(contract.start_rental)} - {fmt_dt(contract.end_rental)}</b>\n\n"
            f"Bạn có chắc chắn muốn hủy hợp đồng này không?"
        )

        buttons = [
            [
                InlineKeyboardButton("Xác nhận hủy", callback_data=f"rcc_confirm_{contract.id}"),
                InlineKeyboardButton("Thoát", callback_data="rcc_exit")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in rental_cancel_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rcc_confirm_(.*)$"))
async def rental_cancel_contract_confirm_callback(client, callback_query: CallbackQuery):
    contract_uuid = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        from app.models.rental import Rental, RentalStatus

        contract = db.query(Rental).filter(Rental.id == contract_uuid).first()
        if not contract:
            await callback_query.message.edit_text("⚠️ Hợp đồng không tồn tại hoặc đã bị xóa.")
            return

        if contract.status == RentalStatus.CANCELLED.value:
            await callback_query.message.edit_text(f"⚠️ Hợp đồng <b>{contract.contract_id}</b> đã bị hủy từ trước.", parse_mode=ParseMode.HTML)
            return

        contract.status = RentalStatus.CANCELLED.value
        db.commit()

        await callback_query.message.edit_text(f"✅ Đã hủy hợp đồng cho thuê <b>{contract.contract_id}</b> thành công.", parse_mode=ParseMode.HTML)
        LogInfo(f"[RentalCancelContract] Cancelled rental contract {contract.contract_id} by user {callback_query.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in rcc_confirm callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi hủy hợp đồng.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rcc_exit$"))
async def rental_cancel_contract_exit_callback(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("❌ Đã hủy thao tác.")


# --- Rental: Payment Confirmed ---
@bot.on_message(filters.command(["rental_payment_confirmed", "rental_xac_nhan_thanh_toan"]) | filters.regex(r"^@\w+\s+/(rental_payment_confirmed|rental_xac_nhan_thanh_toan)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
async def rental_payment_confirmed_handler(client, message: Message) -> None:
    if not message.reply_to_message:
        await message.reply_text("⚠️ Vui lòng <b>Reply</b> (trả lời) lại tin nhắn THÔNG BÁO ĐÓNG TIỀN THUÊ của Bot để sử dụng lệnh này.", parse_mode=ParseMode.HTML)
        return

    replied_text = message.reply_to_message.text or message.reply_to_message.caption
    if not replied_text or "THÔNG BÁO ĐÓNG TIỀN THUÊ" not in replied_text:
        await message.reply_text("⚠️ Lệnh này chỉ dùng để Reply vào tin nhắn THÔNG BÁO ĐÓNG TIỀN THUÊ của Bot.", parse_mode=ParseMode.HTML)
        return

    import re as _re
    match = _re.search(r"Mã Hợp Đồng:\s*([A-Za-z0-9_\-]+)", replied_text)
    if not match:
        await message.reply_text("❌ Không thể trích xuất Mã Hợp Đồng từ tin nhắn.", parse_mode=ParseMode.HTML)
        return

    contract_code = match.group(1).strip()

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp số tiền. Lệnh ví dụ: <code>/rental_payment_confirmed 5000000</code>", parse_mode=ParseMode.HTML)
        return

    amount_str = args[1]
    paid_amount = _parse_float_rental(amount_str)

    if paid_amount <= 0:
        await message.reply_text("⚠️ Số tiền thanh toán không hợp lệ.", parse_mode=ParseMode.HTML)
        return

    db = SessionLocal()
    try:
        from app.models.rental import Rental, RentalCustomer, RentalStatus
        from app.models.telegram import TelegramProjectMember
        import html

        contract = db.query(Rental).filter(Rental.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"❌ Không tìm thấy hợp đồng cho thuê <b>{contract_code}</b> trong CSDL.", parse_mode=ParseMode.HTML)
            return

        if contract.status == RentalStatus.CANCELLED.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã bị hủy, không thể thanh toán.", parse_mode=ParseMode.HTML)
            return

        # Subtract paid amount from rental_debt
        contract.rental_debt = (contract.rental_debt or 0.0) - paid_amount

        # Save payment record for history
        from app.models.rental import RentalPayment
        now = datetime.datetime.now()
        new_payment = RentalPayment(
            contract_id=contract.contract_id,
            payment_date=now.date(),
            payment_time=now,
            payment_amount=paid_amount
        )
        db.add(new_payment)

        db.commit()

        customer = db.query(RentalCustomer).filter(RentalCustomer.id == contract.customer_id).first()

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        remaining = fmt_num(contract.rental_debt)
        date_str = datetime.datetime.now().strftime('%d/%m/%Y')
        amount_fmt = fmt_num(paid_amount)

        reply_msg = (
            f"<b>{date_str}</b>\n"
            f"Đã cập nhật thanh toán: <b>{amount_fmt:,} VNĐ</b> vào hợp đồng cho thuê <b>{contract.contract_id}</b>\n"
            f"Khách hàng: <b>{customer.customer_name if customer else 'N/A'}</b>\n"
            f"Công nợ hiện tại: <b>{remaining:,} VNĐ</b>"
        )

        await message.reply_text(reply_msg, parse_mode=ParseMode.HTML)
        LogInfo(f"[RentalPaymentConfirmed] Contract {contract.contract_id} received {amount_fmt} by user {message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in rental_payment_confirmed_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình cập nhật thanh toán.")
    finally:
        db.close()


# --- Rental: Update Contract ---
@bot.on_message(filters.command(["rental_update_contract", "rental_cap_nhat_hop_dong"]) | filters.regex(r"^@\w+\s+/(rental_update_contract|rental_cap_nhat_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
@require_group_role("main")
async def rental_update_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_update_contract", "rental_cap_nhat_hop_dong"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng. Lệnh ví dụ: <code>/rental_update_contract LMD-HD220101</code>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1]
    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.rental import RentalCustomer, Rental, RentalStatus

        current_group = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()
        project_id = current_group.project_id

        # Get valid contacts for project isolation
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member",
            TelegramProjectMember.slot_name.like("member%")
        ).all()

        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))

        contract = db.query(Rental).filter(Rental.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng cho thuê nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        customer = db.query(RentalCustomer).filter(RentalCustomer.id == contract.customer_id).first()
        if not customer or customer.contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không thuộc về khách hàng nào trong dự án hiện tại.", parse_mode=ParseMode.HTML)
            return

        if contract.status == RentalStatus.CANCELLED.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã bị hủy, không thể cập nhật.", parse_mode=ParseMode.HTML)
            return

        # Handle form requests (just /rental_update_contract HD123) vs form submissions (multiple lines)
        lines = message.text.strip().split("\n")
        if len(lines) < 3:
            # Show pre-filled form
            def fmt_num(val):
                if val is None: return 0
                return int(val) if val == int(val) else val

            def fmt_dt(dt):
                if not dt: return ""
                return dt.strftime('%d/%m/%Y')

            deposit_val = fmt_num(contract.deposit)
            monthly_val = fmt_num(contract.monthly_rental)
            debt_val = fmt_num(contract.rental_debt)

            form_template = f"""<b>FORM CẬP NHẬT HỢP ĐỒNG CHO THUÊ</b>
Vui lòng sao chép toàn bộ form dưới đây, chỉnh sửa thông tin cần thay đổi và gửi lại:

<pre>/rental_update_contract {contract.contract_id}
Tên Nhóm: {customer.group_name or ""}
Tên Khách Hàng: {customer.customer_name or ""}
Liên Hệ Khách Hàng: {customer.contact_info or ""}
Số Điện Thoại: {customer.number_phone or ""}
Mã Hợp Đồng: {contract.contract_id or ""}
Mã Bất Động Sản: {contract.real_estate_id or ""}
Loại Hợp Đồng: {contract.type_contract or ""}
Ngày Bắt Đầu Thuê (dd/mm/yyyy): {fmt_dt(contract.start_rental)}
Ngày Kết Thúc Thuê (dd/mm/yyyy): {fmt_dt(contract.end_rental)}
Tiền Cọc: {deposit_val}
Tiền Thuê / Tháng: {monthly_val}
Công Nợ: {debt_val}
Trạng Thái (active/expired/cancelled): {contract.status or 'active'}
</pre>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return

        # Parse submitted form data
        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        parse_float = _parse_float_rental

        def parse_date(date_str: str):
            if not date_str: return None
            try:
                return datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
            except:
                return None

        new_contract_id = data.get("Mã Hợp Đồng", "").strip()
        if not new_contract_id:
            await message.reply_text("⚠️ <b>Mã Hợp Đồng</b> không được để trống.", parse_mode=ParseMode.HTML)
            return

        # Check duplicate contract code
        if new_contract_id != contract.contract_id:
            dup_contract = db.query(Rental).filter(Rental.contract_id == new_contract_id).first()
            if dup_contract:
                await message.reply_text(f"⚠️ Hợp đồng mã <b>{new_contract_id}</b> đã tồn tại trên một hợp đồng khác.", parse_mode=ParseMode.HTML)
                return

        # Update customer info
        customer.group_name = data.get("Tên Nhóm", customer.group_name)
        customer.customer_name = data.get("Tên Khách Hàng", customer.customer_name)
        customer.contact_info = data.get("Liên Hệ Khách Hàng", customer.contact_info)
        customer.number_phone = data.get("Số Điện Thoại", customer.number_phone)

        # Update contract fields
        contract.contract_id = new_contract_id
        contract.real_estate_id = data.get("Mã Bất Động Sản", contract.real_estate_id)
        contract.type_contract = data.get("Loại Hợp Đồng", contract.type_contract)
        contract.start_rental = parse_date(data.get("Ngày Bắt Đầu Thuê (dd/mm/yyyy)", "")) or contract.start_rental
        contract.end_rental = parse_date(data.get("Ngày Kết Thúc Thuê (dd/mm/yyyy)", "")) or contract.end_rental
        contract.deposit = parse_float(data.get("Tiền Cọc", "")) or contract.deposit
        contract.monthly_rental = parse_float(data.get("Tiền Thuê / Tháng", "")) or contract.monthly_rental

        debt_str = data.get("Công Nợ", "").strip()
        if debt_str:
            contract.rental_debt = parse_float(debt_str)

        # Update status
        status_str = data.get("Trạng Thái (active/expired/cancelled)", "").strip().lower()
        if status_str in [RentalStatus.ACTIVE.value, RentalStatus.EXPIRED.value, RentalStatus.CANCELLED.value]:
            contract.status = status_str

        db.commit()
        await message.reply_text(f"✅ Đã cập nhật hợp đồng cho thuê <b>{new_contract_id}</b> thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[RentalUpdateContract] Updated rental contract {new_contract_id} by {message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in rental_update_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()

# --- Revenue Date Selector ---
async def generate_rental_revenue_report(client, message, project_id, start_date, end_date):
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.rental import RentalCustomer, Rental, RentalStatus, RentalPayment
        
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member",
            TelegramProjectMember.slot_name.like("member%")
        ).all()
        
        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))
            
        customers = db.query(RentalCustomer).filter(RentalCustomer.contact_info.in_(valid_contacts)).all()
        if not customers:
            await message.reply_text("⚠️ Không có khách hàng nào trong dự án cập nhật thông tin trên hệ thống.", parse_mode=ParseMode.HTML)
            return

        all_rentals = db.query(Rental).filter(Rental.customer_id.in_([c.id for c in customers])).all()
        contract_ids = [c.contract_id for c in all_rentals]
        
        payments = db.query(RentalPayment).filter(
            RentalPayment.contract_id.in_(contract_ids)
        ).all()
        
        import datetime
        valid_payments = []
        for payment in payments:
            record_date = payment.payment_date
            if not record_date:
                continue
            if start_date <= record_date <= end_date:
                valid_payments.append(payment)
                
        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val
            
        total_collected = sum([p.payment_amount or 0 for p in valid_payments])
        
        active_rentals = [c for c in all_rentals if c.status in [RentalStatus.ACTIVE.value, RentalStatus.EXPIRED.value]]
        total_outstanding_debt = sum([c.rental_debt or 0 for c in active_rentals])
        
        report_lines = [
            f"<b>BÁO CÁO DOANH THU THUÊ NHÀ</b>",
            f"<i>(Thời gian lọc: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})</i>",
            f"---------------------------",
            f"<b>Tổng Tiền Thuê Đã Thu:</b> <b>{fmt_num(total_collected):,} VND</b>", 
            f"<b>Tổng Công Nợ Khách Hàng:</b> {fmt_num(total_outstanding_debt):,} VND",
        ]
        
        await message.reply_text("\n".join(report_lines), parse_mode=ParseMode.HTML)
        
    except Exception as e:
        LogError(f"Error in generate_rental_revenue_report: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình tính toán báo cáo.")
    finally:
        db.close()


@bot.on_message(filters.command(["rental_revenue", "rental_doanh_thu"]) | filters.regex(r"^@\w+\s+/(rental_revenue|rental_doanh_thu)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
@require_group_role("main")
async def rental_revenue_report_handler(client, message: Message) -> None:
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        chat_id = str(message.chat.id)
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        import re
        match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})", message.text)
        if match:
            import datetime
            start_date_str = match.group(1)
            end_date_str = match.group(2)
            try:
                start_date = datetime.datetime.strptime(start_date_str, "%d/%m/%Y").date()
                end_date = datetime.datetime.strptime(end_date_str, "%d/%m/%Y").date()
                await generate_rental_revenue_report(client, message, current_project_member.project_id, start_date, end_date)
                return
            except ValueError:
                await message.reply_text("⚠️ Định dạng ngày không hợp lệ. Vui lòng dùng dd/mm/yyyy - dd/mm/yyyy", parse_mode=ParseMode.HTML)
                return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("7 ngày qua", callback_data="rental_rev_7d"), InlineKeyboardButton("14 ngày qua", callback_data="rental_rev_14d")],
            [InlineKeyboardButton("21 ngày qua", callback_data="rental_rev_21d"), InlineKeyboardButton("1 tháng qua", callback_data="rental_rev_1m")],
            [InlineKeyboardButton("1 quý qua", callback_data="rental_rev_1q"), InlineKeyboardButton("Năm nay", callback_data="rental_rev_ytd")],
            [InlineKeyboardButton("Năm trước", callback_data="rental_rev_prev")],
            [InlineKeyboardButton("Hủy", callback_data="rental_rev_cancel")]
        ])
        
        await message.reply_text("Vui lòng chọn khoảng thời gian để xem báo cáo doanh thu thuê nhà:", reply_markup=keyboard)
        
    except Exception as e:
        LogError(f"Error in rental_revenue_report_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rental_rev_(.+)$"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def rental_revenue_callback_handler(client, callback_query: CallbackQuery):
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        chat_id = str(callback_query.message.chat.id)
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        data = callback_query.data.split("_", 2)[2]
        
        if data == "cancel":
            await callback_query.message.delete()
            return

        import datetime
        today = datetime.date.today()
        
        start_date = today
        end_date = today
        
        if data == "7d":
            start_date = today - datetime.timedelta(days=7)
        elif data == "14d":
            start_date = today - datetime.timedelta(days=14)
        elif data == "21d":
            start_date = today - datetime.timedelta(days=21)
        elif data == "1m":
            start_date = today - datetime.timedelta(days=30)
        elif data == "1q":
            start_date = today - datetime.timedelta(days=90)
        elif data == "ytd":
            start_date = datetime.date(today.year, 1, 1)
        elif data == "prev":
            start_date = datetime.date(today.year - 1, 1, 1)
            end_date = datetime.date(today.year - 1, 12, 31)
            
        await callback_query.message.delete()
        await generate_rental_revenue_report(client, callback_query.message, current_project_member.project_id, start_date, end_date)
        
    except Exception as e:
        LogError(f"Error in rental_revenue_callback_handler: {e}", LogType.SYSTEM_STATUS)
        await callback_query.message.reply_text("❌ Có lỗi xảy ra.")
    finally:
        db.close()

# --- Report Cashflow Command ---
@bot.on_message(filters.command(["rental_cashflow_report", "rental_bao_cao_dong_tien"]) | filters.regex(r"^@\w+\s+/(rental_cashflow_report|rental_bao_cao_dong_tien)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
@require_group_role("main")
async def rental_cashflow_report_handler(client, message: Message) -> None:
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.rental import RentalCustomer, Rental, RentalStatus, RentalPayment
        
        chat_id = str(message.chat.id)
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        active_project_id = current_project_member.project_id
        
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == active_project_id,
            TelegramProjectMember.role == "member"
        ).all()
        
        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))
            
        customers = db.query(RentalCustomer).filter(RentalCustomer.contact_info.in_(valid_contacts)).all()
        
        if not customers:
            await message.reply_text("⚠️ Không có khách hàng nào trong dự án này.", parse_mode=ParseMode.HTML)
            return
            
        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val
            
        total_contracts = 0
        total_deposit = 0
        total_debt = 0
        project_monthly_totals = {}
        
        customer_lines = []
        
        for customer in customers:
            all_cust_rentals = db.query(Rental).filter(
                Rental.customer_id == customer.id
            ).all()
            
            active_rentals = [c for c in all_cust_rentals if c.status in [RentalStatus.ACTIVE.value, RentalStatus.EXPIRED.value]]
            
            if not active_rentals and not all_cust_rentals:
                continue
                
            cust_contracts = len(active_rentals)
            cust_deposit = sum([(c.deposit or 0) for c in active_rentals])
            cust_debt = sum([(c.rental_debt or 0) for c in active_rentals])
            
            total_contracts += cust_contracts
            total_deposit += cust_deposit
            total_debt += cust_debt
            
            cust_paid_str = ""
            if all_cust_rentals:
                contract_ids = [c.contract_id for c in all_cust_rentals]
                payments = db.query(RentalPayment).filter(RentalPayment.contract_id.in_(contract_ids)).all()
                monthly_totals = {}
                for payment in payments:
                    if payment.payment_date:
                        ym = payment.payment_date.strftime("%m/%Y")
                    else:
                        continue
                    monthly_totals[ym] = monthly_totals.get(ym, 0) + (payment.payment_amount or 0)
                    project_monthly_totals[ym] = project_monthly_totals.get(ym, 0) + (payment.payment_amount or 0)
                    
                if monthly_totals:
                    parts = [f"Tháng {ym}: {fmt_num(amt):,}" for ym, amt in sorted(monthly_totals.items())]
                    cust_paid_str = " | ".join(parts)
            
            if not cust_paid_str:
                cust_paid_str = "Chưa đóng tiền"
                
            if cust_contracts == 0 and cust_paid_str == "Chưa đóng tiền":
                continue
            
            customer_lines.append(
                f"\n<b>{customer.customer_name}</b> ({customer.contact_info})\n"
                f"   Hợp đồng: {cust_contracts} | Tiền Cọc: <b>{fmt_num(cust_deposit):,}</b> | Công Nợ: <b>{fmt_num(cust_debt):,}</b>\n"
                f"   Đã đóng: {cust_paid_str}"
            )
            
        if total_contracts == 0 and not project_monthly_totals:
            await message.reply_text("ℹ️ Không có dữ liệu hợp đồng/dòng tiền nào trong dự án.", parse_mode=ParseMode.HTML)
            return
            
        header_lines = [
            f"<b>BÁO CÁO DÒNG TIỀN DỰ ÁN THUÊ NHÀ</b>",
            f"---------------------------",
            f"<b>Tổng Hợp Đồng Đang Thuê:</b> {total_contracts}",
            f"<b>Tổng Tiền Cọc Đang Giữ:</b> {fmt_num(total_deposit):,}",
            f"<b>Tổng Công Nợ:</b> {fmt_num(total_debt):,}"
        ]
        
        if project_monthly_totals:
            header_lines.append(f"---------------------------")
            header_lines.append(f"<b>TỔNG TIỀN THUÊ ĐÃ THU THEO THÁNG:</b>")
            for ym, amt in sorted(project_monthly_totals.items()):
                header_lines.append(f"Tháng {ym}: <b>{fmt_num(amt):,}</b>")
                
        header_lines.append(f"---------------------------")
        
        full_report_lines = header_lines + customer_lines
        msg_text = "\n".join(full_report_lines)
        
        # Split message if too long
        max_length = 4000
        if len(msg_text) > max_length:
            import math
            import time
            chunks = math.ceil(len(msg_text) / max_length)
            parts = [msg_text[i:i+max_length] for i in range(0, len(msg_text), max_length)]
            for i, part in enumerate(parts):
                tag = f"\n<i>(Phần {i+1}/{chunks})</i>" if chunks > 1 else ""
                await message.reply_text(part + tag, parse_mode=ParseMode.HTML)
                time.sleep(0.3)
        else:
            await message.reply_text(msg_text, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        LogError(f"Error in rental_cashflow_report_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình truy xuất báo cáo.")
    finally:
        db.close()


# --- Rental: List Contracts ---
@bot.on_message(filters.command(["rental_list_contract", "rental_danh_sach_hop_dong"]) | filters.regex(r"^@\w+\s+/(rental_list_contract|rental_danh_sach_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
@require_group_role("main")
async def rental_list_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_list_contract", "rental_danh_sach_hop_dong"])
    if args is None: return

    db = SessionLocal()
    try:
        from app.models.rental import RentalCustomer, Rental, RentalStatus
        from app.models.telegram import TelegramProjectMember

        chat_id = str(message.chat.id)
        current_group = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        if not current_group:
            await message.reply_text("⚠️ Nhóm này chưa được đồng bộ vào dự án nào.", parse_mode=ParseMode.HTML)
            return

        project_id = current_group.project_id

        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member",
            TelegramProjectMember.slot_name.like("member%")
        ).all()

        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))

        customers = db.query(RentalCustomer).filter(RentalCustomer.contact_info.in_(valid_contacts)).all()
        if not customers:
            await message.reply_text("ℹ️ Không có khách hàng nào trong dự án này.", parse_mode=ParseMode.HTML)
            return

        customer_ids = [c.id for c in customers]
        customer_map = {c.id: c for c in customers}

        all_contracts = db.query(Rental).filter(Rental.customer_id.in_(customer_ids)).all()
        if not all_contracts:
            await message.reply_text("ℹ️ Không có hợp đồng cho thuê nào trong dự án.", parse_mode=ParseMode.HTML)
            return

        STATUS_MAP = {
            RentalStatus.ACTIVE.value: "Đang thuê",
            RentalStatus.EXPIRED.value: "Hết hạn",
            RentalStatus.CANCELLED.value: "Đã hủy",
            RentalStatus.BAD_DEBT.value: "Nợ xấu",
        }

        # Group by status
        grouped = {}
        for c in all_contracts:
            label = STATUS_MAP.get(c.status, "Không rõ")
            grouped.setdefault(label, []).append(c)

        # Sort order
        status_order = ["Đang thuê", "Hết hạn", "Nợ xấu", "Đã hủy", "Không rõ"]

        lines = [
            "DANH SÁCH HỢP ĐỒNG CHO THUÊ",
            f"Tổng: {len(all_contracts)} hợp đồng",
            "---------------------------",
        ]

        idx = 1
        for status in status_order:
            contracts = grouped.get(status, [])
            if not contracts:
                continue
            lines.append(f"\n{status} ({len(contracts)})")
            for c in contracts:
                cust = customer_map.get(c.customer_id)
                cust_name = cust.customer_name if cust else "N/A"
                lines.append(f"  {idx}. {c.contract_id} - {cust_name}")
                idx += 1

        if len(all_contracts) > 20:
            import io
            txt_content = "\n".join(lines)
            buf = io.BytesIO(txt_content.encode("utf-8"))
            buf.name = f"danh_sach_hop_dong_{datetime.datetime.now().strftime('%d%m%Y')}.txt"
            await message.reply_document(
                document=buf,
                caption=f"<b>DANH SÁCH HỢP ĐỒNG CHO THUÊ</b>\nTổng: <b>{len(all_contracts)}</b> hợp đồng\n\n<i>File đính kèm bên dưới.</i>",
                parse_mode=ParseMode.HTML
            )
        else:
            # Send as inline message with HTML formatting
            html_lines = [
                f"<b>DANH SÁCH HỢP ĐỒNG CHO THUÊ</b>",
                f"Tổng: <b>{len(all_contracts)}</b> hợp đồng",
                f"---------------------------",
            ]
            idx2 = 1
            for status in status_order:
                contracts = grouped.get(status, [])
                if not contracts:
                    continue
                html_lines.append(f"\n<b>{status} ({len(contracts)})</b>")
                for c in contracts:
                    cust = customer_map.get(c.customer_id)
                    cust_name = cust.customer_name if cust else "N/A"
                    html_lines.append(f"  {idx2}. <code>{c.contract_id}</code> - {cust_name}")
                    idx2 += 1

            msg_text = "\n".join(html_lines)
            await message.reply_text(msg_text, parse_mode=ParseMode.HTML)

        LogInfo(f"[RentalListContract] Listed {len(all_contracts)} contracts by user {message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in rental_list_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra khi truy xuất danh sách hợp đồng.")
    finally:
        db.close()



# --- Rental: Bad Debt / Blacklist ---
@bot.on_message(filters.command(["rental_bad_debt", "rental_xac_nhan_no_xau"]) | filters.regex(r"^@\w+\s+/(rental_bad_debt|rental_xac_nhan_no_xau)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Rental")
@require_group_role("main")
async def rental_bad_debt_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["rental_bad_debt", "rental_xac_nhan_no_xau"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng. Lệnh ví dụ: <code>/rental_bad_debt LMD-HD220101</code>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1].strip()
    db = SessionLocal()
    try:
        from app.models.rental import Rental, RentalCustomer, RentalStatus
        from app.models.telegram import TelegramProjectMember

        # Verify contract belongs to current project
        chat_id = str(message.chat.id)
        current_group = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        if not current_group:
            await message.reply_text("⚠️ Nhóm này chưa được đồng bộ vào dự án nào.", parse_mode=ParseMode.HTML)
            return

        project_id = current_group.project_id

        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member",
            TelegramProjectMember.slot_name.like("member%")
        ).all()

        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))

        contract = db.query(Rental).filter(Rental.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"❌ Không tìm thấy hợp đồng cho thuê <b>{contract_code}</b> trong CSDL.", parse_mode=ParseMode.HTML)
            return

        customer = db.query(RentalCustomer).filter(RentalCustomer.id == contract.customer_id).first()
        if not customer or customer.contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không thuộc về khách hàng nào trong dự án hiện tại.", parse_mode=ParseMode.HTML)
            return

        if contract.status == RentalStatus.BAD_DEBT.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã nằm trong Blacklist Nợ Xấu từ trước rồi.", parse_mode=ParseMode.HTML)
            return

        if contract.status == RentalStatus.CANCELLED.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã bị hủy, không thể đưa vào Blacklist.", parse_mode=ParseMode.HTML)
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        def fmt_dt(dt):
            if not dt: return "N/A"
            return dt.strftime('%d/%m/%Y')

        if contract.status == RentalStatus.ACTIVE.value:
            status_label = "Đang thuê"
        elif contract.status == RentalStatus.EXPIRED.value:
            status_label = "Hết hạn"
        elif contract.status == RentalStatus.BAD_DEBT.value:
            status_label = "Nợ xấu"
        else:
            status_label = "Không rõ"

        debt = fmt_num(contract.rental_debt)
        monthly = fmt_num(contract.monthly_rental)

        text = (
            f"<b>XÁC NHẬN ĐƯA VÀO BLACKLIST NỢ XẤU</b>\n\n"
            f"<b>Khách hàng:</b> {customer.customer_name}\n"
            f"<b>Liên hệ:</b> {customer.contact_info}\n"
            f"<b>Mã Hợp Đồng:</b> <code>{contract_code}</code>\n"
            f"<b>Trạng thái:</b> {status_label}\n"
            f"<b>Loại HĐ:</b> {contract.type_contract or 'N/A'}\n"
            f"<b>Mã BĐS:</b> {contract.real_estate_id or 'N/A'}\n"
            f"<b>Tiền thuê:</b> {monthly:,} VNĐ/tháng\n"
            f"<b>Công nợ:</b> {debt:,} VNĐ\n"
            f"<b>Thời gian thuê:</b> {fmt_dt(contract.start_rental)} - {fmt_dt(contract.end_rental)}\n\n"
            f"Bạn có chắc chắn muốn đưa hợp đồng này vào <b>BLACKLIST NỢ XẤU</b> không?"
        )

        buttons = [
            [
                InlineKeyboardButton("Xác nhận nợ xấu", callback_data=f"rbd_confirm_{contract.id}"),
                InlineKeyboardButton("Hủy", callback_data="rbd_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in rental_bad_debt_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rbd_confirm_(.*)$"))
async def rental_bad_debt_confirm_callback(client, callback_query: CallbackQuery):
    contract_uuid = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        from app.models.rental import Rental, RentalCustomer, RentalStatus

        contract = db.query(Rental).filter(Rental.id == contract_uuid).first()
        if not contract:
            await callback_query.message.edit_text("⚠️ Hợp đồng không tồn tại hoặc đã bị xóa.")
            return

        if contract.status == RentalStatus.BAD_DEBT.value:
            await callback_query.message.edit_text(f"⚠️ Hợp đồng <b>{contract.contract_id}</b> đã nằm trong Blacklist Nợ Xấu từ trước.", parse_mode=ParseMode.HTML)
            return

        contract.status = RentalStatus.BAD_DEBT.value
        db.commit()

        customer = db.query(RentalCustomer).filter(RentalCustomer.id == contract.customer_id).first()

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        debt = fmt_num(contract.rental_debt)

        await callback_query.message.edit_text(
            f"✅ Đã đưa hợp đồng cho thuê <b>{contract.contract_id}</b> và Khách hàng <b>{customer.customer_name if customer else 'N/A'}</b> vào <b>BLACKLIST NỢ XẤU</b> thành công!\n\n"
            f"<b>Công nợ:</b> {debt:,} VNĐ\n\n"
            f"<i>Thông tin vẫn được lưu giữ nguyên trạng để tiếp tục truy thu hoặc tra soát.</i>",
            parse_mode=ParseMode.HTML
        )
        LogInfo(f"[RentalBadDebt] Contract {contract.contract_id} marked as BAD_DEBT by user {callback_query.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in rbd_confirm callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi xác nhận nợ xấu.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rbd_cancel$"))
async def rental_bad_debt_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("❌ Đã hủy thao tác đưa vào Blacklist.")
