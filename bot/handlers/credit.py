from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from bot.utils.bot import bot
from bot.utils.utils import check_command_target, require_user_type, require_project_name, require_group_role
from bot.utils.enums import UserType
from bot.utils.logger import LogInfo, LogError, LogType
from app.db.session import SessionLocal
from app.models.business import Projects
from app.models.telegram import TelegramProjectMember
from app.models.credit import Credit, CreditStatus, CreditCustomer
import datetime
import re

def parse_float_vn(val_str: str) -> float:
    if not val_str: return 0.0
    # Strip symbols like VNĐ, VND, Đ and spaces before parsing
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
            
    # if it still has multiple dots, keep only the last one as decimal
    if v.count('.') > 1:
        parts = v.split('.')
        v = "".join(parts[:-1]) + "." + parts[-1]
            
    clean_str = re.sub(r'[^\d.-]', '', v)
    try:
        return float(clean_str) if clean_str else 0.0
    except:
        return 0.0


# --- Create Customer ---
@bot.on_message(filters.command(["credit_create_customer", "credit_tao_khach_hang"]) | filters.regex(r"^@\w+\s+/(credit_create_customer|credit_tao_khach_hang)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
async def create_customer_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_create_customer", "credit_tao_khach_hang"])
    if args is None: return

    lines = message.text.strip().split("\n")
    if len(lines) < 3:
        form_template = """<b>FORM TẠO KHÁCH HÀNG TÍN DỤNG</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/credit_create_customer
Tên Nhóm: 
Tên Khách Hàng: 
Liên Hệ Khách Hàng: 
Tổng Hạn Mức Tín Dụng: 
Hạn Mức Còn Lại: 
Tổng Nợ Gốc Hiện Tại: 0
</pre>

<i>Ví dụ liên hệ: @username hoặc mã khách hàng</i>"""
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
    total_credit_str = data.get("Tổng Hạn Mức Tín Dụng", "0")
    remain_credit_str = data.get("Hạn Mức Còn Lại", "")
    total_principal_str = data.get("Tổng Nợ Gốc Hiện Tại", "0")

    if not customer_name or not contact_info:
        await message.reply_text("⚠️ <b>Tên Khách Hàng</b> và <b>Liên Hệ Khách Hàng</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    parse_float = parse_float_vn

    total_credit = parse_float(total_credit_str)
    remain_credit = parse_float(remain_credit_str) if remain_credit_str else total_credit
    total_principal = parse_float(total_principal_str)

    db = SessionLocal()
    try:
        chat_id = str(message.chat.id)
        # Check if synced
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
        existing = db.query(CreditCustomer).filter(CreditCustomer.contact_info == contact_info).first()
        if existing:
            await message.reply_text(f"⚠️ Khách hàng có thông tin liên hệ <b>{contact_info}</b> đã tồn tại trong hệ thống.", parse_mode=ParseMode.HTML)
            return

        from app.schemas.credit import CreditCustomerCreate
        from app.crud.credit import create_credit_customer

        new_customer = CreditCustomerCreate(
            group_name=group_name,
            customer_name=customer_name,
            contact_info=contact_info,
            total_credit_limit=total_credit,
            remaining_credit_limit=remain_credit,
            total_principal_outstanding=total_principal
        )
        
        create_credit_customer(db, obj_in=new_customer)
        await message.reply_text(f"✅ Đã tạo khách hàng <b>{customer_name}</b> thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[CreateCustomer] Created customer {customer_name} ({contact_info}) by {message.from_user.id}", LogType.SYSTEM_STATUS)
    except Exception as e:
        LogError(f"Error in create_customer_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý lưu khách hàng.")
    finally:
        db.close()

# --- Check Customer ---
@bot.on_message(filters.command(["credit_check_customer", "credit_xem_khach_hang"]) | filters.regex(r"^@\w+\s+/(credit_check_customer|credit_xem_khach_hang)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
async def check_customer_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_check_customer", "credit_xem_khach_hang"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp thông tin liên hệ. Lệnh ví dụ: <pre>/credit_check_customer @username</pre> hoặc <pre>/credit_check_customer [Tên nhóm khách hàng]</pre>", parse_mode=ParseMode.HTML)
        return

    contact_info = args[1]
    db = SessionLocal()
    try:
        chat_id = str(message.chat.id)
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        if not current_project_member:
            await message.reply_text("⚠️ Nhóm này chưa được đồng bộ vào dự án nào. Vui lòng sử dụng lệnh /syncchat trước.")
            return

        project_id = current_project_member.project_id

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
            
        from sqlalchemy import or_
        customer = db.query(CreditCustomer).filter(
            or_(CreditCustomer.contact_info == contact_info, CreditCustomer.group_name == contact_info)
        ).first()

        if not customer:
            await message.reply_text(f"⚠️ Khách hàng <b>{contact_info}</b> chưa tồn tại trong hệ thống.", parse_mode=ParseMode.HTML)
            return

        if customer.contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Không tìm thấy liên hệ <b>{customer.contact_info}</b> trong nhóm thành viên (member) của dự án này.", parse_mode=ParseMode.HTML)
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        reply_lines = [
            f"<b>THÔNG TIN KHÁCH HÀNG</b>",
            f"Tên Nhóm: <b>{customer.group_name or 'N/A'}</b>",
            f"Tên Khách Hàng: <b>{customer.customer_name}</b>",
            f"Liên Hệ: <b>{customer.contact_info}</b>",
            f"---------------------------",
            f"<b>HẠN MỨC</b>",
            f"Tổng Hạn Mức Tín Dụng: <b>{fmt_num(customer.total_credit_limit):,} VNĐ</b>",
            f"Hạn Mức Còn Lại: <b>{fmt_num(customer.remaining_credit_limit):,} VNĐ</b>",
            f"Tổng Nợ Gốc Hiện Tại: <b>{fmt_num(customer.total_principal_outstanding):,} VNĐ</b>",
            f"---------------------------",
            f"<b>DANH SÁCH HỢP ĐỒNG</b>"
        ]

        from app.models.credit import CreditStatus
        credits = db.query(Credit).filter(Credit.customer_id == customer.id).all()
        if not credits:
            reply_lines.append("<i>Khách hàng chưa có hợp đồng nào.</i>")
        else:
            for idx, c in enumerate(credits, 1):
                if c.credit_status == CreditStatus.ACTIVE.value:
                    status_emoji = "Đang vay"
                elif c.credit_status == CreditStatus.PAID.value:
                    status_emoji = "Đã tất toán khoản vay"
                elif c.credit_status == CreditStatus.BAD_DEBT.value:
                    status_emoji = "Nợ xấu (Blacklist)"
                else:
                    status_emoji = "Đã huỷ hợp đồng"
                
                loan_label = "Thế chấp" if c.loan_type == "secured" else "Tín chấp"
                reply_lines.append(
                    f"{idx}. {status_emoji} <b>{c.contract_id}</b> ({loan_label}) - Gốc: {fmt_num(c.initial_principal):,} - Còn nợ: {fmt_num(c.remaining_principal):,}"
                )

        await message.reply_text("\n".join(reply_lines), parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in check_customer_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình truy xuất khách hàng.")
    finally:
        db.close()

# --- Check Contract ---
@bot.on_message(filters.command(["credit_check_contract", "credit_xem_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_check_contract|credit_xem_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)
@require_project_name("Credit")
async def check_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_check_contract", "credit_xem_hop_dong"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng. Lệnh ví dụ: <pre>/credit_check_contract HD123</pre>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1]
    db = SessionLocal()
    try:
        # Check Project Isolation
        chat_id = str(message.chat.id)
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        if not current_project_member:
            await message.reply_text("⚠️ Nhóm này chưa được đồng bộ vào dự án nào. Vui lòng sử dụng lệnh /syncchat trước.")
            return

        project_id = current_project_member.project_id
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
            
        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        customer = contract.customer
        if not customer or customer.contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không thuộc về khách hàng trong dự án hiện tại.", parse_mode=ParseMode.HTML)
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val
            
        def fmt_dt(dt):
            if not dt: return "N/A"
            return dt.strftime('%d/%m/%Y')

        from app.models.credit import CreditStatus
        if contract.credit_status == CreditStatus.ACTIVE.value:
            status_emoji = "Đang vay"
        elif contract.credit_status == CreditStatus.PAID.value:
            status_emoji = "Đã tất toán khoản vay"
        elif contract.credit_status == CreditStatus.BAD_DEBT.value:
            status_emoji = "Nợ xấu (Blacklist)"
        else:
            status_emoji = "Đã huỷ hợp đồng"
        loan_type_label = "Thế chấp" if contract.loan_type == "secured" else "Tín chấp"

        reply_lines = [
            f"<b>THÔNG TIN HỢP ĐỒNG: {contract.contract_id}</b>",
            f"Trạng thái: <b>{status_emoji}</b>",
            f"Loại hợp đồng: <b>{loan_type_label}</b>",
            f"Tên: <b>{customer.customer_name}</b>",
            f"Liên hệ: <b>{customer.contact_info}</b>",
            f"Nợ Gốc (Ban đầu): <b>{fmt_num(contract.initial_principal):,}</b>",
            f"Đã Trả Gốc: <b>{fmt_num(contract.total_principal_paid):,}</b>",
            f"Còn Nợ Gốc: <b>{fmt_num(contract.remaining_principal):,}</b>",
            f"Lãi Suất: <b>{fmt_num(contract.monthly_interest_rate)}% / tháng</b>",
            f"Lãi Tạm Tính Hàng Tháng: <b>{fmt_num(contract.monthly_interest_amount):,}</b>",
            f"Công Nợ Lãi Hiện Tại: <b>{fmt_num(contract.interest_debt or 0):,}</b>",
            f"Ngày Vay: <b>{fmt_dt(contract.start_date)}</b>",
            f"Ngày Đáo Hạn: <b>{fmt_dt(contract.due_date)}</b>",
            f"Bắt Đầu Tính Lãi Từ: <b>{fmt_dt(contract.interest_start_date)}</b>",
            f"Ghi chú: {contract.notes or '<i>Không có</i>'}",
        ]

        await message.reply_text("\n".join(reply_lines), parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in check_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình truy xuất hợp đồng.")
    finally:
        db.close()

# --- Check Debt (Xem Công Nợ Hiện Tại) ---
@bot.on_message(filters.command(["credit_check_debt", "credit_xem_cong_no"]) | filters.regex(r"^@\w+\s+/(credit_check_debt|credit_xem_cong_no)\b"))
@require_user_type(UserType.MEMBER)
@require_project_name("Credit")
@require_group_role("member")
async def check_debt_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_check_debt", "credit_xem_cong_no"])
    if args is None: return

    db = SessionLocal()
    try:
        # Lấy @username của người gọi lệnh
        username = message.from_user.username
        if not username:
            await message.reply_text("⚠️ Tài khoản của bạn chưa có username Telegram. Vui lòng cài đặt username trước.", parse_mode=ParseMode.HTML)
            return

        contact_info = f"@{username}"

        # Tìm khách hàng theo contact_info
        customer = db.query(CreditCustomer).filter(CreditCustomer.contact_info == contact_info).first()
        if not customer:
            await message.reply_text(f"ℹ️ Không tìm thấy thông tin khách hàng cho <b>{contact_info}</b>.", parse_mode=ParseMode.HTML)
            return

        # Lấy các hợp đồng đang vay / nợ xấu
        active_credits = db.query(Credit).filter(
            Credit.customer_id == customer.id,
            Credit.credit_status.in_([CreditStatus.ACTIVE.value, CreditStatus.BAD_DEBT.value])
        ).all()

        if not active_credits:
            await message.reply_text(f"ℹ️ <b>{customer.customer_name}</b>, bạn hiện không có hợp đồng công nợ nào.", parse_mode=ParseMode.HTML)
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        def fmt_dt(dt):
            if not dt: return "N/A"
            return dt.strftime('%d/%m/%Y')

        total_principal = sum([(c.remaining_principal or 0) for c in active_credits])
        total_interest = sum([(c.interest_debt or 0) for c in active_credits])
        total_debt = total_principal + total_interest

        contract_lines = []
        for idx, c in enumerate(active_credits, 1):
            status_label = "Nợ xấu" if c.credit_status == CreditStatus.BAD_DEBT.value else "Đang vay"
            loan_label = "Thế chấp" if c.loan_type == "secured" else "Tín chấp"
            contract_lines.append(
                f"{idx}. <b>{c.contract_id}</b> ({loan_label}) - {status_label}\n"
                f"   Nợ gốc còn: <b>{fmt_num(c.remaining_principal):,}</b>\n"
                f"   Nợ lãi: <b>{fmt_num(c.interest_debt or 0):,}</b>\n"
            )

        reply_lines = [
            f"<b>CÔNG NỢ HIỆN TẠI</b>",
            f"Khách hàng: <b>{customer.customer_name}</b> ({contact_info})",
            f"---------------------------",
            f"Tổng hợp đồng: <b>{len(active_credits)}</b>",
            f"Tổng nợ gốc: <b>{fmt_num(total_principal):,}</b>",
            f"Tổng nợ lãi: <b>{fmt_num(total_interest):,}</b>",
            f"Tổng nợ: <b>{fmt_num(total_debt):,}</b>",
            f"---------------------------",
        ] + contract_lines

        await message.reply_text("\n".join(reply_lines), parse_mode=ParseMode.HTML)
        LogInfo(f"[CheckDebt] {contact_info} checked their debt: {len(active_credits)} contracts, total: {total_debt}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in check_debt_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra khi truy xuất công nợ.")
    finally:
        db.close()

# --- Update Customer ---
@bot.on_message(filters.command(["credit_update_customer", "credit_cap_nhat_khach_hang"]) | filters.regex(r"^@\w+\s+/(credit_update_customer|credit_cap_nhat_khach_hang)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
async def update_customer_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_update_customer", "credit_cap_nhat_khach_hang"])
    if args is None: return

    db = SessionLocal()
    try:
        lines = message.text.strip().split("\n")
        
        # Generate form
        if len(lines) < 3:
            if len(args) < 2:
                await message.reply_text("⚠️ Vui lòng cung cấp thông tin liên hệ. Lệnh ví dụ: <pre>/credit_update_customer @username</pre> hoặc <pre>/credit_update_customer [Tên nhóm khách hàng]</pre>", parse_mode=ParseMode.HTML)
                return
            
            from sqlalchemy import or_
            contact_info = args[1]
            customer = db.query(CreditCustomer).filter(
                or_(CreditCustomer.contact_info == contact_info, CreditCustomer.group_name == contact_info)
            ).first()
            if not customer:
                await message.reply_text(f"⚠️ Khách hàng <b>{contact_info}</b> chưa tồn tại trong hệ thống.", parse_mode=ParseMode.HTML)
                return
            
            def fmt_num(val):
                if val is None: return 0
                return int(val) if val == int(val) else val

            form_template = f"""<b>FORM CẬP NHẬT KHÁCH HÀNG TÍN DỤNG</b>
Vui lòng sao chép form dưới đây, chỉnh sửa thông tin và gửi lại:

<pre>/credit_update_customer {customer.contact_info}
Tên Nhóm: {customer.group_name or ""}
Tên Khách Hàng: {customer.customer_name or ""}
Liên Hệ Khách Hàng: {customer.contact_info}
Tổng Hạn Mức Tín Dụng: {fmt_num(customer.total_credit_limit)}
Hạn Mức Còn Lại: {fmt_num(customer.remaining_credit_limit)}
Tổng Nợ Gốc Hiện Tại: {fmt_num(customer.total_principal_outstanding)}
</pre>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return

        # Parse Form
        if len(args) < 2:
            await message.reply_text("⚠️ Không tìm thấy khách hàng mục tiêu trong lệnh.", parse_mode=ParseMode.HTML)
            return
            
        from sqlalchemy import or_
        target_contact_info = args[1]
        customer = db.query(CreditCustomer).filter(
            or_(CreditCustomer.contact_info == target_contact_info, CreditCustomer.group_name == target_contact_info)
        ).first()
        if not customer:
            await message.reply_text(f"⚠️ Không tìm thấy khách hàng <b>{target_contact_info}</b> để cập nhật.", parse_mode=ParseMode.HTML)
            return

        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        group_name = data.get("Tên Nhóm", "")
        customer_name = data.get("Tên Khách Hàng", "")
        new_contact_info = data.get("Liên Hệ Khách Hàng", "")
        total_credit_str = data.get("Tổng Hạn Mức Tín Dụng", "0")
        remain_credit_str = data.get("Hạn Mức Còn Lại", "")
        total_principal_str = data.get("Tổng Nợ Gốc Hiện Tại", "0")

        if not customer_name or not new_contact_info:
            await message.reply_text("⚠️ <b>Tên Khách Hàng</b> và <b>Liên Hệ Khách Hàng</b> là bắt buộc.", parse_mode=ParseMode.HTML)
            return

        parse_float = parse_float_vn

        total_credit = parse_float(total_credit_str)
        provided_remain = parse_float(remain_credit_str) if remain_credit_str else total_credit
        total_principal = parse_float(total_principal_str)

        old_total = customer.total_credit_limit or 0.0
        old_remain = customer.remaining_credit_limit or 0.0

        if total_credit != old_total and provided_remain == old_remain:
            remain_credit = old_remain + (total_credit - old_total)
        else:
            remain_credit = provided_remain

        if new_contact_info != customer.contact_info:
            # Check dup mapping
            existing = db.query(CreditCustomer).filter(CreditCustomer.contact_info == new_contact_info).first()
            if existing:
                await message.reply_text(f"⚠️ Thông tin liên hệ mới <b>{new_contact_info}</b> đã bị trùng lặp với một khách hàng khác.", parse_mode=ParseMode.HTML)
                return

            # Check if valid member
            chat_id = str(message.chat.id)
            current_project_member = db.query(TelegramProjectMember).filter(
                TelegramProjectMember.chat_id == chat_id
            ).first()

            if current_project_member:
                project_id = current_project_member.project_id
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
                    
                if new_contact_info not in valid_contacts:
                    await message.reply_text(f"⚠️ Khách hàng mới <b>{new_contact_info}</b> chưa có mặt trong nhóm thành viên (member).", parse_mode=ParseMode.HTML)
                    return

        customer.group_name = group_name
        customer.customer_name = customer_name
        customer.contact_info = new_contact_info
        customer.total_credit_limit = total_credit
        customer.remaining_credit_limit = remain_credit
        customer.total_principal_outstanding = total_principal
        
        db.commit()
        await message.reply_text(f"✅ Đã cập nhật thông tin khách hàng <b>{customer_name}</b> thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[UpdateCustomer] Updated customer {customer_name} ({new_contact_info}) by {message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in update_customer_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình cập nhật khách hàng.")
    finally:
        db.close()

# --- Create Contract ---
@bot.on_message(filters.command(["credit_create_contract", "credit_tao_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_create_contract|credit_tao_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
async def create_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_create_contract", "credit_tao_hop_dong"])
    if args is None: return

    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        # Simple verification if they only typed "/create_contract @username"
        lines = message.text.strip().split("\n")
        if len(lines) < 3:
            if len(args) < 2:
                await message.reply_text("⚠️ Vui lòng cung cấp thông tin liên hệ của khách hàng. Lệnh ví dụ: <pre>/credit_create_contract @username</pre> hoặc <pre>/credit_create_contract [Tên nhóm khách hàng]</pre>", parse_mode=ParseMode.HTML)
                return

            from sqlalchemy import or_
            contact_info = args[1]
            customer = db.query(CreditCustomer).filter(
                or_(CreditCustomer.contact_info == contact_info, CreditCustomer.group_name == contact_info)
            ).first()
            if not customer:
                await message.reply_text(f"⚠️ Khách hàng <b>{contact_info}</b> chưa tồn tại trong hệ thống. Vui lòng tạo tĩnh thông tin khách hàng bằng lệnh /credit_create_customer trước.", parse_mode=ParseMode.HTML)
                return

            def fmt_num(val):
                if val is None:
                    return 0
                return int(val) if val == int(val) else val

            total_limit = fmt_num(customer.total_credit_limit)
            remain_limit = fmt_num(customer.remaining_credit_limit)
            total_principal = fmt_num(customer.total_principal_outstanding)

            form_template = f"""<b>FORM TẠO HỢP ĐỒNG TÍN DỤNG</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/credit_create_contract {customer.contact_info}
Tên Nhóm: {customer.group_name or ""}
Tên Khách Hàng: {customer.customer_name or ""}
Liên Hệ Khách Hàng: {customer.contact_info}
Tổng Hạn Mức Tín Dụng: {total_limit}
Hạn Mức Còn Lại: {remain_limit}
Tổng Nợ Gốc Hiện Tại: {total_principal}
Mã Hợp Đồng: 
Loại Hợp Đồng: 
Tiền Nợ Gốc (Ban đầu): 
Ngày Bắt Đầu Vay (dd/mm/yyyy): 
Ngày Đáo Hạn (dd/mm/yyyy): 
Ngày Bắt Đầu Thu Lãi (dd/mm/yyyy): 
Lãi Suất / Tháng (%): 
Số Tiền Lãi / Tháng: 
Tổng Số Tiền Trả Gốc: 0
Tiền Nợ Gốc Còn Lại: 
Ghi Chú: 
Gửi Tin Nhắn Phát Sinh (Có/Không): Có
Nội Dung Tin Nhắn: 
</pre>

<i>Ví dụ mã hợp đồng: HD220101. Loại hợp đồng gồm (Thế chấp [secured], Tín chấp [unsecured])</i>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return
            
        # If user actually submitted data in the form format
        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        from sqlalchemy import or_
        contact_info = data.get("Liên Hệ Khách Hàng", "")
        if not contact_info and len(args) > 1:
            contact_info = args[1]
            
        customer = db.query(CreditCustomer).filter(
            or_(CreditCustomer.contact_info == contact_info, CreditCustomer.group_name == contact_info)
        ).first()
        if not customer:
            await message.reply_text(f"⚠️ Khách hàng <b>{contact_info}</b> chưa tồn tại trong hệ thống. Vui lòng tạo khách trước.", parse_mode=ParseMode.HTML)
            return

        parse_float = parse_float_vn

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

        existing_contract = db.query(Credit).filter(Credit.contract_id == contract_id).first()
        if existing_contract:
            await message.reply_text(f"⚠️ Hợp đồng mã <b>{contract_id}</b> đã tồn tại.", parse_mode=ParseMode.HTML)
            return

        loan_type = data.get("Loại Hợp Đồng", "unsecured").strip().lower()
        initial_principal = parse_float(data.get("Tiền Nợ Gốc (Ban đầu)", "0"))
        
        start_date = parse_date(data.get("Ngày Bắt Đầu Vay (dd/mm/yyyy)", ""))
        due_date = parse_date(data.get("Ngày Đáo Hạn (dd/mm/yyyy)", ""))
        interest_start_date = parse_date(data.get("Ngày Bắt Đầu Thu Lãi (dd/mm/yyyy)", ""))
        
        monthly_interest_rate = parse_float(data.get("Lãi Suất / Tháng (%)", "0"))
        monthly_interest_amount = parse_float(data.get("Số Tiền Lãi / Tháng", "0"))
        
        if monthly_interest_amount == 0 and monthly_interest_rate > 0:
            monthly_interest_amount = (initial_principal * monthly_interest_rate) / 100
            
        total_principal_paid = parse_float(data.get("Tổng Số Tiền Trả Gốc", "0"))
        provided_remaining = parse_float(data.get("Tiền Nợ Gốc Còn Lại", "0"))
        if provided_remaining == 0 and initial_principal > 0:
            remaining_principal = initial_principal - total_principal_paid
        elif not data.get("Tiền Nợ Gốc Còn Lại", "").strip():
            remaining_principal = initial_principal - total_principal_paid
        else:
            remaining_principal = provided_remaining

        notes = data.get("Ghi Chú", "")
        send_msg_str = data.get("Gửi Tin Nhắn Phát Sinh (Có/Không)", "").lower()
        send_msg = True if "có" in send_msg_str else False
        msg_content = data.get("Nội Dung Tin Nhắn", "")

        amount = initial_principal
        limit_remaining = customer.remaining_credit_limit or 0.0
        
        # Validation for limits
        if loan_type == "secured":
            if limit_remaining < amount:
                await message.reply_text(f"⚠️ <b>Lỗi Hạn Mức:</b> Hợp đồng thế chấp (secured) yêu cầu số tiền vay ({amount:,.0f}) không được vượt quá Hạn mức còn lại ({limit_remaining:,.0f}).", parse_mode=ParseMode.HTML)
                return
                
        # Update limits
        customer.remaining_credit_limit = limit_remaining - amount
        customer.total_principal_outstanding = (customer.total_principal_outstanding or 0.0) + amount
        
        from app.schemas.credit import CreditCreate
        from app.crud.credit import create_credit

        new_contract = CreditCreate(
            customer_id=customer.id,
            contract_id=contract_id,
            loan_type=loan_type,
            initial_principal=initial_principal,
            start_date=start_date,
            due_date=due_date,
            interest_start_date=interest_start_date,
            monthly_interest_rate=monthly_interest_rate,
            monthly_interest_amount=monthly_interest_amount,
            total_principal_paid=total_principal_paid,
            remaining_principal=remaining_principal,
            notes=notes,
            send_message_arise=send_msg,
            message_content=msg_content,
            credit_status=CreditStatus.ACTIVE
        )
        
        create_credit(db, obj_in=new_contract)
        await message.reply_text(f"✅ Đã tạo hợp đồng <b>{contract_id}</b> cho khách hàng <b>{customer.customer_name}</b> thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[CreateContract] Created contract {contract_id} for {customer.customer_name} by {message.from_user.id}", LogType.SYSTEM_STATUS)
        
    except Exception as e:
        LogError(f"Error in create_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()

# --- Update Contract ---
@bot.on_message(filters.command(["credit_update_contract", "credit_cap_nhat_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_update_contract|credit_cap_nhat_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
async def update_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_update_contract", "credit_cap_nhat_hop_dong"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng. Lệnh ví dụ: <code>/credit_update_contract HD123</code>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1]
    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        # Check which project this chat belongs to
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        if not current_project_member:
            await message.reply_text("⚠️ Nhóm này chưa được đồng bộ vào dự án nào. Vui lòng sử dụng lệnh /syncchat trước.")
            return

        project_id = current_project_member.project_id

        # Get all valid contact_info (usernames) from member groups of this project
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

        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        if not contract.customer or contract.customer.contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không thuộc về khách hàng nào trong dự án hiện tại.", parse_mode=ParseMode.HTML)
            return

        if contract.credit_status == CreditStatus.CANCELLED.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã bị hủy, không thể cập nhật.", parse_mode=ParseMode.HTML)
            return

        # Handle form requests (just /update_contract HD123) vs form submissions (multiple lines)
        lines = message.text.strip().split("\n")
        if len(lines) < 3:
            start_date_str = contract.start_date.strftime("%d/%m/%Y") if contract.start_date else ""
            due_date_str = contract.due_date.strftime("%d/%m/%Y") if contract.due_date else ""
            interest_start_date_str = contract.interest_start_date.strftime("%d/%m/%Y") if contract.interest_start_date else ""
            
            # Format numbers properly
            def fmt_num(val):
                if val is None:
                    return 0
                return int(val) if val == int(val) else val

            total_limit = fmt_num(contract.customer.total_credit_limit if contract.customer else 0)
            remain_limit = fmt_num(contract.customer.remaining_credit_limit if contract.customer else 0)
            total_principal = fmt_num(contract.customer.total_principal_outstanding if contract.customer else 0)
            initial_principal = fmt_num(contract.initial_principal)
            interest_rate = fmt_num(contract.monthly_interest_rate)
            monthly_amount = fmt_num(contract.monthly_interest_amount)
            total_paid = fmt_num(contract.total_principal_paid)
            remaining_principal = fmt_num(contract.remaining_principal)
            send_msg = "Có" if contract.send_message_arise else "Không"

            form_template = f"""<b>FORM CẬP NHẬT HỢP ĐỒNG TÍN DỤNG</b>
Vui lòng sao chép toàn bộ form dưới đây, chỉnh sửa thông tin cần thay đổi và gửi lại:

<pre>/credit_update_contract {contract.contract_id}
Tên Nhóm: {contract.customer.group_name if contract.customer else ""}
Tên Khách Hàng: {contract.customer.customer_name if contract.customer else ""}
Liên Hệ Khách Hàng: {contract.customer.contact_info if contract.customer else ""}
Tổng Hạn Mức Tín Dụng: {total_limit}
Hạn Mức Còn Lại: {remain_limit}
Tổng Nợ Gốc Hiện Tại: {total_principal}
Mã Hợp Đồng: {contract.contract_id or ""}
Loại Hợp Đồng: {contract.loan_type or ""}
Tiền Nợ Gốc (Ban đầu): {initial_principal}
Ngày Bắt Đầu Vay (dd/mm/yyyy): {start_date_str}
Ngày Đáo Hạn (dd/mm/yyyy): {due_date_str}
Ngày Bắt Đầu Thu Lãi (dd/mm/yyyy): {interest_start_date_str}
Lãi Suất / Tháng (%): {interest_rate}
Số Tiền Lãi / Tháng: {monthly_amount}
Tổng Số Tiền Trả Gốc: {total_paid}
Tiền Nợ Gốc Còn Lại: {remaining_principal}
Ghi Chú: {contract.notes or ""}
Gửi Tin Nhắn Phát Sinh (Có/Không): {send_msg}
Nội Dung Tin Nhắn: {contract.message_content or ""}
</pre>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
            return

        # If user actually submitted data in the form format
        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        # Parse functions
        parse_float = parse_float_vn

        def parse_date(date_str: str):
            if not date_str: return None
            try:
                import datetime
                return datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
            except:
                return None

        new_contract_id = data.get("Mã Hợp Đồng", "")
        if not new_contract_id:
            await message.reply_text("⚠️ <b>Mã Hợp Đồng</b> không được để trống.", parse_mode=ParseMode.HTML)
            return

        # Check existing contract code
        if new_contract_id != contract.contract_id:
            dup_contract = db.query(Credit).filter(Credit.contract_id == new_contract_id).first()
            if dup_contract:
                await message.reply_text(f"⚠️ Hợp đồng mã <b>{new_contract_id}</b> đã tồn tại trên một hợp đồng khác.", parse_mode=ParseMode.HTML)
                return

        loan_type = data.get("Loại Hợp Đồng", "unsecured").strip().lower()
        new_initial_principal = parse_float(data.get("Tiền Nợ Gốc (Ban đầu)", "0"))
        
        start_date = parse_date(data.get("Ngày Bắt Đầu Vay (dd/mm/yyyy)", ""))
        due_date = parse_date(data.get("Ngày Đáo Hạn (dd/mm/yyyy)", ""))
        interest_start_date = parse_date(data.get("Ngày Bắt Đầu Thu Lãi (dd/mm/yyyy)", ""))
        
        monthly_interest_rate = parse_float(data.get("Lãi Suất / Tháng (%)", "0"))
        provided_amount = parse_float(data.get("Số Tiền Lãi / Tháng", "0"))

        old_principal = contract.initial_principal or 0.0
        old_rate = contract.monthly_interest_rate or 0.0
        old_amount = contract.monthly_interest_amount or 0.0

        if (new_initial_principal != old_principal or monthly_interest_rate != old_rate) and provided_amount == old_amount:
            monthly_interest_amount = (new_initial_principal * monthly_interest_rate) / 100
        elif provided_amount == 0 and monthly_interest_rate > 0:
            monthly_interest_amount = (new_initial_principal * monthly_interest_rate) / 100
        else:
            monthly_interest_amount = provided_amount

        total_principal_paid = parse_float(data.get("Tổng Số Tiền Trả Gốc", "0"))
        provided_remaining = parse_float(data.get("Tiền Nợ Gốc Còn Lại", "0"))

        old_remaining = contract.remaining_principal or 0.0
        old_paid = contract.total_principal_paid or 0.0

        if (new_initial_principal != old_principal or total_principal_paid != old_paid) and provided_remaining == old_remaining:
            remaining_principal = new_initial_principal - total_principal_paid
        elif not data.get("Tiền Nợ Gốc Còn Lại", "").strip():
            remaining_principal = new_initial_principal - total_principal_paid
        else:
            remaining_principal = provided_remaining

        notes = data.get("Ghi Chú", "")
        send_msg_str = data.get("Gửi Tin Nhắn Phát Sinh (Có/Không)", "").lower()
        send_msg = True if "có" in send_msg_str else False
        msg_content = data.get("Nội Dung Tin Nhắn", "")

        # Re-evaluate limits if loan_type or principal changed
        old_initial_principal = contract.initial_principal or 0.0
        customer = contract.customer
        
        if customer:
            limit_remaining = customer.remaining_credit_limit or 0.0
            
            # Temporary refund old loan to available limit
            temp_limit = limit_remaining + old_initial_principal
            if loan_type == "secured":
                if temp_limit < new_initial_principal:
                    await message.reply_text(f"⚠️ <b>Lỗi Hạn Mức:</b> Hợp đồng thế chấp yêu cầu số tiền vay (<b>{new_initial_principal:,.0f}</b>) không được vượt quá Hạn mức còn lại (<b>{temp_limit:,.0f}</b>).", parse_mode=ParseMode.HTML)
                    return

            customer.remaining_credit_limit = temp_limit - new_initial_principal
            customer.total_principal_outstanding = (customer.total_principal_outstanding or 0.0) - old_initial_principal + new_initial_principal

        contract.contract_id = new_contract_id
        contract.loan_type = loan_type
        contract.initial_principal = new_initial_principal
        contract.start_date = start_date
        contract.due_date = due_date
        contract.interest_start_date = interest_start_date
        contract.monthly_interest_rate = monthly_interest_rate
        contract.monthly_interest_amount = monthly_interest_amount
        contract.total_principal_paid = total_principal_paid
        contract.remaining_principal = remaining_principal
        contract.notes = notes
        contract.send_message_arise = send_msg
        contract.message_content = msg_content
        
        db.commit()
        await message.reply_text(f"✅ Đã cập nhật hợp đồng <b>{new_contract_id}</b> thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[UpdateContract] Updated contract {new_contract_id} by {message.from_user.id}", LogType.SYSTEM_STATUS)
        
    except Exception as e:
        LogError(f"Error in update_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()

# --- Cancel Contract ---
@bot.on_message(filters.command(["credit_cancel_contract", "credit_huy_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_cancel_contract|credit_huy_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
async def cancel_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_cancel_contract", "credit_huy_hop_dong"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng. Lệnh ví dụ: <code>/credit_cancel_contract HD123</code>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1]
    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        # Check which project this chat belongs to
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        if not current_project_member:
            await message.reply_text("⚠️ Nhóm này chưa được đồng bộ vào dự án nào. Vui lòng sử dụng lệnh /syncchat trước.")
            return

        project_id = current_project_member.project_id

        # Get all valid contact_info (usernames) from member groups of this project
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

        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        if not contract.customer or contract.customer.contact_info not in valid_contacts:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không thuộc về khách hàng nào trong dự án hiện tại.", parse_mode=ParseMode.HTML)
            return

        if contract.credit_status == CreditStatus.CANCELLED.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã bị hủy từ trước.", parse_mode=ParseMode.HTML)
            return

        # Handle None value for float formatting
        remaining = contract.remaining_principal if contract.remaining_principal is not None else 0

        text = (
            f"<b>THÔNG TIN HỢP ĐỒNG</b>\n\n"
            f"- Tên Khách Hàng: <b>{contract.customer.customer_name if contract.customer else 'N/A'}</b>\n"
            f"- Mã Hợp Đồng: <b>{contract.contract_id}</b>\n"
            f"- Trạng Thái: <b>{contract.credit_status.upper() if contract.credit_status else 'UNKNOWN'}</b>\n"
            f"- Lãi Suất: <b>{contract.monthly_interest_rate}% / Tháng</b>\n"
            f"- Dư Nợ Gốc: <b>{remaining:,.0f} Đ</b>\n\n"
            f"Bạn có chắc chắn muốn hủy hợp đồng này không?"
        )

        buttons = [
            [
                InlineKeyboardButton("Xác nhận hủy", callback_data=f"cc_confirm_{contract.id}"),
                InlineKeyboardButton("Thoát", callback_data="cc_exit")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in cancel_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cc_confirm_(.*)$"))
async def cancel_contract_confirm_callback(client, callback_query: CallbackQuery):
    contract_uuid = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        contract = db.query(Credit).filter(Credit.id == contract_uuid).first()
        if not contract:
            await callback_query.message.edit_text("⚠️ Hợp đồng không tồn tại hoặc đã bị xóa.")
            return

        if contract.credit_status == CreditStatus.CANCELLED.value:
            await callback_query.message.edit_text(f"⚠️ Hợp đồng <b>{contract.contract_id}</b> đã bị hủy từ trước.", parse_mode=ParseMode.HTML)
            return

        contract.credit_status = CreditStatus.CANCELLED.value
        db.commit()

        await callback_query.message.edit_text(f"✅ Đã hủy hợp đồng <b>{contract.contract_id}</b> thành công.", parse_mode=ParseMode.HTML)
        LogInfo(f"[CancelContract] Cancelled contract {contract.contract_id} by user {callback_query.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in cc_confirm callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi hủy hợp đồng.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cc_exit$"))
async def cancel_contract_exit_callback(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("❌ Đã hủy thao tác.")


# --- Credit: List Contracts ---
@bot.on_message(filters.command(["credit_list_contract", "credit_danh_sach_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_list_contract|credit_danh_sach_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
async def credit_list_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_list_contract", "credit_danh_sach_hop_dong"])
    if args is None: return

    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditCustomer, CreditStatus
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

        customers = db.query(CreditCustomer).filter(CreditCustomer.contact_info.in_(valid_contacts)).all()
        if not customers:
            await message.reply_text("ℹ️ Không có khách hàng nào trong dự án này.", parse_mode=ParseMode.HTML)
            return

        customer_ids = [c.id for c in customers]
        customer_map = {c.id: c for c in customers}

        all_contracts = db.query(Credit).filter(Credit.customer_id.in_(customer_ids)).all()
        if not all_contracts:
            await message.reply_text("ℹ️ Không có hợp đồng tín dụng nào trong dự án.", parse_mode=ParseMode.HTML)
            return

        STATUS_MAP = {
            CreditStatus.ACTIVE.value: "Đang vay",
            CreditStatus.PAID.value: "Đã tất toán",
            CreditStatus.CANCELLED.value: "Đã hủy",
            CreditStatus.BAD_DEBT.value: "Nợ xấu",
        }

        grouped = {}
        for c in all_contracts:
            label = STATUS_MAP.get(c.credit_status, "Không rõ")
            grouped.setdefault(label, []).append(c)

        status_order = ["Đang vay", "Nợ xấu", "Đã tất toán", "Đã hủy", "Không rõ"]

        lines = [
            "DANH SÁCH HỢP ĐỒNG TÍN DỤNG",
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
            import datetime as _dt
            txt_content = "\n".join(lines)
            buf = io.BytesIO(txt_content.encode("utf-8"))
            buf.name = f"danh_sach_hop_dong_tin_dung_{_dt.datetime.now().strftime('%d%m%Y')}.txt"
            await message.reply_document(
                document=buf,
                caption=f"<b>DANH SÁCH HỢP ĐỒNG TÍN DỤNG</b>\nTổng: <b>{len(all_contracts)}</b> hợp đồng\n\n<i>File đính kèm bên dưới.</i>",
                parse_mode=ParseMode.HTML
            )
        else:
            html_lines = [
                f"<b>DANH SÁCH HỢP ĐỒNG TÍN DỤNG</b>",
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

        LogInfo(f"[CreditListContract] Listed {len(all_contracts)} contracts by user {message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in credit_list_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra khi truy xuất danh sách hợp đồng.")
    finally:
        db.close()


# --- Confirm Bad Debt / Blacklist ---
@bot.on_message(filters.command(["credit_bad_debt", "credit_xac_nhan_no_xau"]) | filters.regex(r"^@\w+\s+/(credit_bad_debt|credit_xac_nhan_no_xau)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
async def confirm_bad_debt_handler(client, message: Message) -> None:
    if not message.reply_to_message:
        await message.reply_text("⚠️ Vui lòng <b>Reply</b> (trả lời) lại tin nhắn cảnh báo Nợ Xấu của Bot để sử dụng lệnh này.", parse_mode=ParseMode.HTML)
        return
        
    replied_text = message.reply_to_message.text
    if not replied_text or "CẢNH BÁO NỢ XẤU" not in replied_text:
        await message.reply_text("⚠️ Lệnh này chỉ dùng để Reply vào tin nhắn CẢNH BÁO NỢ XẤU hợp lệ của Bot.", parse_mode=ParseMode.HTML)
        return
        
    import re
    match = re.search(r"Mã Hợp Đồng:\s*([A-Za-z0-9_-]+)", replied_text)
    if not match:
        await message.reply_text("❌ Không thể trích xuất Mã Hợp Đồng từ tin nhắn.", parse_mode=ParseMode.HTML)
        return
        
    contract_code = match.group(1).strip()
    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditStatus
        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"❌ Không tìm thấy hợp đồng <b>{contract_code}</b> trong CSDL.", parse_mode=ParseMode.HTML)
            return
            
        if contract.credit_status == CreditStatus.BAD_DEBT.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã nằm trong Blacklist Nợ Xấu từ trước rồi.", parse_mode=ParseMode.HTML)
            return
            
        contract.credit_status = CreditStatus.BAD_DEBT.value
        if contract.notes:
            if "[BLACKLIST]" not in contract.notes:
                contract.notes = f"[BLACKLIST] {contract.notes}"
        else:
            contract.notes = "[BLACKLIST]"
            
        customer = contract.customer
        db.commit()
        await message.reply_text(f"✅ Đã đưa hợp đồng <b>{contract_code}</b> và Khách hàng <b>{customer.customer_name}</b> vào <a href='https://t.me'>BLACKLIST NỢ XẤU</a> thành công!\n\n<i>Thông tin vẫn được lưu giữ nguyên trạng để tiếp tục truy thu hoặc tra soát.</i>", parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        LogError(f"Error in confirm_bad_debt_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình cập nhật Blacklist.")
    finally:
        db.close()

# --- Paid Interest ---
@bot.on_message(filters.command(["credit_paid_interest", "credit_thanh_toan_lai"]) | filters.regex(r"^@\w+\s+/(credit_paid_interest|credit_thanh_toan_lai)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
async def paid_interest_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_paid_interest", "credit_thanh_toan_lai"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng. Lệnh ví dụ: <code>/credit_paid_interest HD123</code>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1]
    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditStatus
        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return
            
        if contract.credit_status in [CreditStatus.PAID.value, CreditStatus.CANCELLED.value]:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đang ở trạng thái <b>{contract.credit_status}</b>, không thể thanh toán lãi.", parse_mode=ParseMode.HTML)
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val
            
        customer = contract.customer
        int_rate = contract.monthly_interest_rate or 0
        int_amt = contract.monthly_interest_amount or 0
        
        if int_amt == 0 and int_rate > 0:
            int_amt = (contract.remaining_principal * int_rate) / 100

        text = (
            f"<b>📌 THÔNG TIN THANH TOÁN LÃI</b>\n\n"
            f"- Tên Khách Hàng: <b>{customer.customer_name if customer else 'N/A'}</b>\n"
            f"- Mã Hợp Đồng: <b>{contract.contract_id}</b>\n"
            f"- Dư Nợ Gốc: <b>{fmt_num(contract.remaining_principal):,} Đ</b>\n"
            f"- Lãi Suất: <b>{fmt_num(int_rate)}% / Tháng</b>\n"
            f"- <b>Số tiền lãi cần thu:</b> <b>{fmt_num(int_amt):,} Đ</b>\n\n"
            f"<i>Bạn có chắc chắn muốn xác nhận thu tiền lãi cho hợp đồng này không?</i>"
        )

        buttons = [
            [
                InlineKeyboardButton("Xác nhận thanh toán", callback_data=f"pi_confirm_{contract.id}"),
                InlineKeyboardButton("Hủy", callback_data="pi_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in paid_interest_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^pi_confirm_(.*)$"))
async def paid_interest_confirm_callback(client, callback_query: CallbackQuery):
    contract_uuid = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditInterest, CreditStatus
        contract = db.query(Credit).filter(Credit.id == contract_uuid).first()
        
        if not contract:
            await callback_query.message.edit_text("⚠️ Hợp đồng không tồn tại hoặc đã bị xóa.")
            return

        if contract.credit_status in [CreditStatus.PAID.value, CreditStatus.CANCELLED.value]:
            await callback_query.message.edit_text(f"⚠️ Hợp đồng <b>{contract.contract_id}</b> không ở trạng thái hợp lệ để đóng lãi.", parse_mode=ParseMode.HTML)
            return

        int_rate = contract.monthly_interest_rate or 0
        int_amt = contract.monthly_interest_amount or 0
        if int_amt == 0 and int_rate > 0:
            int_amt = (contract.remaining_principal * int_rate) / 100

        # Create interest payment record
        now = datetime.datetime.now()
        new_interest = CreditInterest(
            contract_id=contract.contract_id,
            interest_payment_date=now.date(),
            payment_time=now,
            interest_amount=int_amt
        )
        db.add(new_interest)
        
        # Optionally, reset bad debt back to active if they were in bad debt
        if contract.credit_status == CreditStatus.BAD_DEBT.value:
            contract.credit_status = CreditStatus.ACTIVE.value
            # Remove [BLACKLIST] from notes if needed
            if contract.notes and "[BLACKLIST]" in contract.notes:
                contract.notes = contract.notes.replace("[BLACKLIST]", "").strip()
        
        db.commit()

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        customer = contract.customer
        success_text = (
            f"✅ <b>Thanh toán thành công hợp đồng {contract.contract_id}</b>\n\n"
            f"- Khách hàng: <b>{customer.customer_name if customer else 'N/A'}</b>\n"
            f"- Số tiền thu: <b>{fmt_num(int_amt):,} Đ</b>\n"
            f"- Thời gian: <b>{now.strftime('%d/%m/%Y %H:%M:%S')}</b>\n"
        )
        
        await callback_query.message.edit_text(success_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[PaidInterest] User {callback_query.from_user.id} logged interest payment for {contract.contract_id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in pi_confirm callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi xác nhận thanh toán.", show_alert=True)
    finally:
        db.close()



@bot.on_callback_query(filters.regex(r"^pi_cancel$"))
async def paid_interest_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("❌ Đã hủy thao tác thanh toán.")

# --- Extend Contract ---
@bot.on_message(filters.command(["credit_extend_contract", "credit_gia_han_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_extend_contract|credit_gia_han_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
async def extend_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_extend_contract", "credit_gia_han"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng.\nCú pháp: <code>/credit_extend_contract [Mã HĐ] [Số tháng]</code>\nVí dụ: <code>/credit_extend_contract HD123 3</code>", parse_mode=ParseMode.HTML)
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
        

            
        from app.models.credit import Credit, CreditStatus
        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return
            
        if contract.credit_status in [CreditStatus.PAID.value, CreditStatus.CANCELLED.value]:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đang ở trạng thái <b>{contract.credit_status}</b>, không thể gia hạn.", parse_mode=ParseMode.HTML)
            return

        def add_months_to_date(source_date, months):
            import calendar
            month = source_date.month - 1 + months
            year = source_date.year + month // 12
            month = month % 12 + 1
            day = min(source_date.day, calendar.monthrange(year, month)[1])
            return datetime.date(year, month, day)
            
        new_due_date = add_months_to_date(contract.due_date, months_to_add)
        
        customer = contract.customer

        text = (
            f"<b>THÔNG TIN GIA HẠN HỢP ĐỒNG</b>\n\n"
            f"- Tên Khách Hàng: <b>{customer.customer_name if customer else 'N/A'}</b>\n"
            f"- Mã Hợp Đồng: <b>{contract.contract_id}</b>\n"
            f"- Thời gian gia hạn thêm: <b>{months_to_add} Tháng</b>\n\n"
            f"- Ngày đáo hạn gốc: <b>{contract.due_date.strftime('%d/%m/%Y')}</b>\n"
            f"- Ngày đáo hạn mới: <b>{new_due_date.strftime('%d/%m/%Y')}</b>\n\n"
            f"<i>Lưu ý: Nếu hợp đồng đang Nợ Xấu (Blacklist), bot sẽ tự động đưa về Active.</i>"
        )

        buttons = [
            [
                InlineKeyboardButton("Xác nhận gia hạn", callback_data=f"ec_confirm_{contract.id}_{months_to_add}"),
                InlineKeyboardButton("Hủy", callback_data="ec_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in extend_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ec_confirm_([^_]+)_(\d+)$"))
async def extend_contract_confirm_callback(client, callback_query: CallbackQuery):
    contract_uuid = callback_query.matches[0].group(1)
    months_to_add = int(callback_query.matches[0].group(2))
    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditStatus
        from app.models.telegram import TelegramProjectMember
        
        contract = db.query(Credit).filter(Credit.id == contract_uuid).first()
        
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

        new_due_date = add_months_to_date(contract.due_date, months_to_add)
        old_due_date_str = contract.due_date.strftime('%d/%m/%Y')
        new_due_date_str = new_due_date.strftime('%d/%m/%Y')
        
        contract.due_date = new_due_date
        
        # Reset bad debt back to active
        if contract.credit_status == CreditStatus.BAD_DEBT.value:
            contract.credit_status = CreditStatus.ACTIVE.value
            if contract.notes and "[BLACKLIST]" in contract.notes:
                contract.notes = contract.notes.replace("[BLACKLIST]", "").strip()
        
        customer = contract.customer
        
        # Cross group announcement to member group
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
            f"✅ <b>Gia hạn thành công hợp đồng {contract.contract_id}</b>\n\n"
            f"- Khách hàng: <b>{customer.customer_name if customer else 'N/A'}</b>\n"
            f"- Phương thức: <b>Gia hạn {months_to_add} tháng</b>\n"
            f"- Ngày đáo hạn mới: <b>{new_due_date_str}</b> (cũ: {old_due_date_str})\n"
        )
        
        await callback_query.message.edit_text(success_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[ExtendContract] User {callback_query.from_user.id} extended contract {contract.contract_id}", LogType.SYSTEM_STATUS)
        
        # Send Member Notification
        if member_chat_id:
            member_alert = (
                f"🔔 <b>THÔNG BÁO TỪ QUẢN TRỊ VIÊN</b>\n\n"
                f"Hợp đồng tín dụng mã <b>{contract.contract_id}</b> của Quý khách đã được gia hạn thành công thêm <b>{months_to_add} tháng</b>.\n\n"
                f"<b>Ngày đáo hạn cập nhật mới nhất: {new_due_date_str}</b>\n"
                f"Quý khách vui lòng lưu ý thời gian đáo hạn mới để thanh toán khoản vay đúng hạn. Xin cảm ơn!"
            )
            try:
                await client.send_message(
                    chat_id=int(member_chat_id),
                    text=member_alert,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                LogError(f"Failed to send extend contract alert to member group {member_chat_id}: {e}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in ec_confirm callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi xác nhận gia hạn.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ec_cancel$"))
async def extend_contract_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("❌ Đã hủy thao tác gia hạn.")


# --- Payment Confirmed ---
@bot.on_message(filters.command(["credit_payment_confirmed", "credit_xac_nhan_thanh_toan"]) | filters.regex(r"^@\w+\s+/(credit_payment_confirmed|credit_xac_nhan_thanh_toan)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
async def payment_confirmed_handler(client, message: Message) -> None:
    if not message.reply_to_message:
        await message.reply_text("⚠️ Vui lòng <b>Reply</b> (trả lời) lại tin nhắn THÔNG BÁO ĐÓNG TIỀN LÃI của Bot để sử dụng lệnh này.", parse_mode=ParseMode.HTML)
        return
        
    replied_text = message.reply_to_message.text or message.reply_to_message.caption
    if not replied_text or "THÔNG BÁO ĐÓNG TIỀN LÃI" not in replied_text:
        await message.reply_text("⚠️ Lệnh này chỉ dùng để Reply vào tin nhắn THÔNG BÁO ĐÓNG TIỀN LÃI của Bot.", parse_mode=ParseMode.HTML)
        return
        
    import re
    match = re.search(r"Mã Hợp Đồng:\s*([A-Za-z0-9_-]+)", replied_text)
    if not match:
        await message.reply_text("❌ Không thể trích xuất Mã Hợp Đồng từ tin nhắn.", parse_mode=ParseMode.HTML)
        return
        
    contract_code = match.group(1).strip()
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp số tiền. Lệnh ví dụ: <code>/credit_payment_confirmed 5000000</code>", parse_mode=ParseMode.HTML)
        return
        
    amount_str = args[1]
    paid_amount = parse_float_vn(amount_str)
    
    if paid_amount <= 0:
        await message.reply_text("⚠️ Số tiền thanh toán không hợp lệ.", parse_mode=ParseMode.HTML)
        return
        
    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditStatus, CreditInterest
        from app.models.telegram import TelegramProjectMember
        import html
        
        chat_id = str(message.chat.id)
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        if not current_project_member or current_project_member.role != "member":
            await message.reply_text("⚠️ Lệnh này chỉ được dùng trong nhóm thành viên (member).", parse_mode=ParseMode.HTML)
            return

        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"❌ Không tìm thấy hợp đồng <b>{contract_code}</b> trong CSDL.", parse_mode=ParseMode.HTML)
            return
            
        if contract.credit_status in [CreditStatus.PAID.value, CreditStatus.CANCELLED.value]:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đang ở trạng thái <b>{contract.credit_status}</b>, không thể thanh toán.", parse_mode=ParseMode.HTML)
            return

        now = datetime.datetime.now()
        new_interest = CreditInterest(
            contract_id=contract.contract_id,
            interest_payment_date=now.date(),
            payment_time=now,
            interest_amount=paid_amount
        )
        db.add(new_interest)
        
        if contract.credit_status == CreditStatus.BAD_DEBT.value:
            contract.credit_status = CreditStatus.ACTIVE.value
            if contract.notes and "[BLACKLIST]" in contract.notes:
                contract.notes = contract.notes.replace("[BLACKLIST]", "").strip()
        # Thay vì tính toán từ tin nhắn, trừ trực tiếp trên database
        contract.interest_debt = (contract.interest_debt or 0.0) - paid_amount
                
        db.commit()

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val
            
        remaining = fmt_num(contract.interest_debt)
        date_str = now.strftime('%d/%m/%Y')
        amount_fmt = fmt_num(paid_amount)
        safe_reply_text = html.escape(replied_text)
        
        reply_msg = (
            f"<b>{date_str}</b>\n"
            f"Đã cập nhật thanh toán: <b>{amount_fmt:,}</b> vào hợp đồng\n"
            f"Công nợ hiện tại: <b>{remaining:,}</b>"
        )
        
        await message.reply_text(reply_msg, parse_mode=ParseMode.HTML)
        LogInfo(f"[PaymentConfirmed] Contract {contract.contract_id} received {amount_fmt} by user {message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in payment_confirmed_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình cập nhật thanh toán.")
    finally:
        db.close()

# --- Report Cashflow Command ---
@bot.on_message(filters.command(["credit_cashflow_report", "credit_bao_cao_dong_tien"]) | filters.regex(r"^@\w+\s+/(credit_cashflow_report|credit_bao_cao_dong_tien)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
@require_project_name("Credit")
async def report_cashflow_handler(client, message: Message) -> None:
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.credit import CreditCustomer, Credit, CreditStatus
        
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
            
        customers = db.query(CreditCustomer).filter(CreditCustomer.contact_info.in_(valid_contacts)).all()
        
        if not customers:
            await message.reply_text("⚠️ Không có khách hàng nào trong dự án này.", parse_mode=ParseMode.HTML)
            return
            
        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val
            
        total_contracts = 0
        total_principal = 0
        total_interest = 0
        project_monthly_totals = {}
        
        customer_lines = []
        from app.models.credit import CreditInterest
        
        for customer in customers:
            all_cust_credits = db.query(Credit).filter(
                Credit.customer_id == customer.id
            ).all()
            
            active_credits = [c for c in all_cust_credits if c.credit_status in [CreditStatus.ACTIVE.value, CreditStatus.BAD_DEBT.value]]
            
            if not active_credits and not all_cust_credits:
                continue
                
            cust_contracts = len(active_credits)
            cust_principal = sum([(c.remaining_principal or 0) for c in active_credits])
            cust_interest = sum([(c.interest_debt or 0) for c in active_credits])
            
            total_contracts += cust_contracts
            total_principal += cust_principal
            total_interest += cust_interest
            
            cust_paid_str = ""
            if all_cust_credits:
                contract_ids = [c.contract_id for c in all_cust_credits]
                interests = db.query(CreditInterest).filter(CreditInterest.contract_id.in_(contract_ids)).all()
                monthly_totals = {}
                for int_record in interests:
                    if int_record.payment_time:
                        ym = int_record.payment_time.strftime("%m/%Y")
                    elif int_record.interest_payment_date:
                        ym = int_record.interest_payment_date.strftime("%m/%Y")
                    else:
                        continue
                    monthly_totals[ym] = monthly_totals.get(ym, 0) + (int_record.interest_amount or 0)
                    project_monthly_totals[ym] = project_monthly_totals.get(ym, 0) + (int_record.interest_amount or 0)
                    
                if monthly_totals:
                    parts = [f"Tháng {ym}: {fmt_num(amt):,}" for ym, amt in sorted(monthly_totals.items())]
                    cust_paid_str = " | ".join(parts)
            
            if not cust_paid_str:
                cust_paid_str = "Chưa đóng lãi"
                
            if cust_contracts == 0 and cust_paid_str == "Chưa đóng lãi":
                continue
            
            customer_lines.append(
                f"\n<b>{customer.customer_name}</b> ({customer.contact_info})\n"
                f"   Hợp đồng: {cust_contracts} | Nợ Gốc: <b>{fmt_num(cust_principal):,}</b> | Nợ Lãi: <b>{fmt_num(cust_interest):,}</b>\n"
                f"   Đã đóng: {cust_paid_str}"
            )
            
        if total_contracts == 0 and not project_monthly_totals:
            await message.reply_text("ℹ️ Không có dữ liệu hợp đồng/dòng tiền nào trong dự án.", parse_mode=ParseMode.HTML)
            return
            
        header_lines = [
            f"<b>BÁO CÁO DÒNG TIỀN DỰ ÁN</b>",
            f"---------------------------",
            f"<b>Tổng Hợp Đồng Đang Vay:</b> {total_contracts}",
            f"<b>Tổng Nợ Gốc:</b> {fmt_num(total_principal):,}",
            f"<b>Tổng Nợ Lãi:</b> {fmt_num(total_interest):,}"
        ]
        
        if project_monthly_totals:
            header_lines.append(f"---------------------------")
            header_lines.append(f"<b>TỔNG LÃI ĐÃ THU THEO THÁNG:</b>")
            for ym, amt in sorted(project_monthly_totals.items()):
                header_lines.append(f"Tháng {ym}: <b>{fmt_num(amt):,}</b>")
                
        header_lines.append(f"---------------------------")
        
        report_lines = header_lines + customer_lines
            
        # Tách tin nhắn nếu quá dài (hạn chế 4096 ký tự của Telegram)
        msg_text = "\n".join(report_lines)
        if len(msg_text) > 4000:
            for i in range(0, len(msg_text), 4000):
                await message.reply_text(msg_text[i:i+4000], parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(msg_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        LogError(f"Error in report_cashflow_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình truy xuất báo cáo.")
    finally:
        db.close()

# --- Revenue Date Selector ---
async def generate_revenue_report(client, message, project_id, start_date, end_date):
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from app.models.credit import CreditCustomer, Credit, CreditStatus, CreditInterest
        
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member"
        ).all()
        
        valid_contacts = []
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))
            
        customers = db.query(CreditCustomer).filter(CreditCustomer.contact_info.in_(valid_contacts)).all()
        if not customers:
            await message.reply_text("⚠️ Không có khách hàng nào trong dự án.", parse_mode=ParseMode.HTML)
            return

        all_credits = db.query(Credit).filter(Credit.customer_id.in_([c.id for c in customers])).all()
        contract_ids = [c.contract_id for c in all_credits]
        
        interests = db.query(CreditInterest).filter(
            CreditInterest.contract_id.in_(contract_ids)
        ).all()
        
        import datetime
        valid_interests = []
        for interest in interests:
            record_date = interest.payment_time.date() if interest.payment_time else interest.interest_payment_date
            if not record_date:
                continue
            if start_date <= record_date <= end_date:
                valid_interests.append(interest)
                
        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val
            
        total_collected = sum([i.interest_amount or 0 for i in valid_interests])
        
        active_credits = [c for c in all_credits if c.credit_status in [CreditStatus.ACTIVE.value, CreditStatus.BAD_DEBT.value]]
        total_outstanding_principal = sum([c.remaining_principal or 0 for c in active_credits])
        total_outstanding_interest = sum([c.interest_debt or 0 for c in active_credits])
        
        report_lines = [
            f"<b>BÁO CÁO DOANH THU (Lãi đã thu)</b>",
            f"<i>(Thời gian lọc: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})</i>",
            f"---------------------------",
            f"<b>Tổng Lãi Đã Thu:</b> <b>{fmt_num(total_collected):,} VND</b>", 
            f"<b>Tổng Nợ Gốc:</b> {fmt_num(total_outstanding_principal):,} VND",
            f"<b>Tổng Nợ Lãi Chưa Trả:</b> {fmt_num(total_outstanding_interest):,} VND"
        ]
        
        await message.reply_text("\n".join(report_lines), parse_mode=ParseMode.HTML)
        
    except Exception as e:
        LogError(f"Error in generate_revenue_report: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình tính toán.")
    finally:
        db.close()


@bot.on_message(filters.command(["credit_revenue", "credit_doanh_thu"]) | filters.regex(r"^@\w+\s+/(credit_revenue|credit_doanh_thu)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
async def revenue_report_handler(client, message: Message) -> None:
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
                await generate_revenue_report(client, message, current_project_member.project_id, start_date, end_date)
                return
            except ValueError:
                await message.reply_text("⚠️ Định dạng ngày không hợp lệ. Vui lòng dùng dd/mm/yyyy - dd/mm/yyyy", parse_mode=ParseMode.HTML)
                return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("7 ngày qua", callback_data="rev_7d"), InlineKeyboardButton("14 ngày qua", callback_data="rev_14d")],
            [InlineKeyboardButton("21 ngày qua", callback_data="rev_21d"), InlineKeyboardButton("1 tháng qua", callback_data="rev_1m")],
            [InlineKeyboardButton("1 quý qua", callback_data="rev_1q"), InlineKeyboardButton("Năm nay", callback_data="rev_ytd")],
            [InlineKeyboardButton("Năm trước", callback_data="rev_prev")],
            [InlineKeyboardButton("Hủy", callback_data="rev_cancel")]
        ])
        
        await message.reply_text("Vui lòng chọn khoảng thời gian để xem báo cáo doanh thu lãi:", reply_markup=keyboard)
        
    except Exception as e:
        LogError(f"Error in revenue_report_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rev_(.+)$"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def revenue_callback_handler(client, callback_query: CallbackQuery):
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        chat_id = str(callback_query.message.chat.id)
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()



        data = callback_query.data.split("_", 1)[1]
        
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
        await generate_revenue_report(client, callback_query.message, current_project_member.project_id, start_date, end_date)
        
    except Exception as e:
        LogError(f"Error in revenue_callback_handler: {e}", LogType.SYSTEM_STATUS)
        await callback_query.message.reply_text("❌ Có lỗi xảy ra.")
    finally:
        db.close()
