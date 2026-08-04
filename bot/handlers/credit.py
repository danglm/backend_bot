from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from bot.utils.bot import bot
from bot.utils.utils import check_command_target, require_user_type, require_project_name, require_group_role, command_timeout, fmt_num, fmt_vn
from bot.utils.enums import UserType
from bot.utils.logger import LogInfo, LogError, LogType
from app.db.session import SessionLocal
from bot.utils.states import form_tracker
from app.models.business import Projects
from app.models.telegram import TelegramProjectMember
from app.models.credit import Credit, CreditStatus, CreditCustomer
from sqlalchemy import or_
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
@command_timeout(timeout_seconds=600, auto_delete_cmd=True)  # Form nhiều trường -> cần thời gian điền
async def create_customer_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_create_customer", "credit_tao_khach_hang"])
    if args is None: return

    lines = message.text.strip().split("\n")
    if len(lines) < 3:
        form_template = """<b>FORM TẠO KHÁCH HÀNG TÍN DỤNG</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/credit_create_customer
Mã Khách Hàng:
Tên Nhóm:
Tên Khách Hàng:
Liên Hệ Khách Hàng:
Chat ID (Telegram):
Tổng Hạn Mức Tín Dụng:
Hạn Mức Còn Lại:
Tổng Nợ Gốc Hiện Tại: 0
Phân Loại: KCredit
</pre>

<i>Mã Khách Hàng là mã duy nhất để định danh khách hàng (ví dụ: KH001)
Chat ID (Telegram) là Chat ID nhóm member của khách hàng (ví dụ: -1001234567890). Nếu để trống, bot sẽ tự lấy theo Tên Nhóm đã đồng bộ.
Phân loại gồm: KCredit, PQCredit, QCredit, ...</i>"""
        form_msg = await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        form_tracker.track(message.chat.id, "credit_create_customer", "create", form_msg.id)
        return

    # Parse Form
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    customer_id_str = data.get("Mã Khách Hàng", "")
    group_name = data.get("Tên Nhóm", "")
    customer_name = data.get("Tên Khách Hàng", "")
    contact_info = data.get("Liên Hệ Khách Hàng", "")
    input_chat_id = data.get("Chat ID (Telegram)", "").strip()
    total_credit_str = data.get("Tổng Hạn Mức Tín Dụng", "0")
    remain_credit_str = data.get("Hạn Mức Còn Lại", "")
    total_principal_str = data.get("Tổng Nợ Gốc Hiện Tại", "0")
    classification = data.get("Phân Loại", "").strip()

    if not customer_id_str:
        await message.reply_text("⚠️ <b>Mã Khách Hàng</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    if not customer_name:
        await message.reply_text("⚠️ <b>Tên Khách Hàng</b> là bắt buộc.", parse_mode=ParseMode.HTML)
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
            TelegramProjectMember.role == "member"
        ).all()

        valid_contacts = []
        valid_groups = []
        group_chat_ids = {}
        for m in valid_members:
            if m.user_name:
                valid_contacts.append(f"@{m.user_name}")
            valid_contacts.append(str(m.user_id))
            if m.group_name:
                valid_groups.append(m.group_name)
                if m.chat_id and m.group_name not in group_chat_ids:
                    group_chat_ids[m.group_name] = str(m.chat_id)

        if not group_name or group_name not in valid_groups:
            await message.reply_text(f"⚠️ Tên Nhóm <b>{group_name}</b> không hợp lệ hoặc chưa có mặt trong dự án. Vui lòng kiểm tra lại Tên Nhóm và dùng lệnh /syncchat để đồng bộ trước.", parse_mode=ParseMode.HTML)
            return

        # Chat ID nhóm member Telegram của khách hàng: ưu tiên giá trị nhập tay, nếu trống thì lấy theo Tên Nhóm
        if input_chat_id:
            valid_chat_ids = {str(m.chat_id) for m in valid_members if m.chat_id}
            if input_chat_id not in valid_chat_ids:
                await message.reply_text(f"⚠️ Chat ID <b>{input_chat_id}</b> không thuộc nhóm member nào của dự án. Vui lòng kiểm tra lại hoặc để trống để bot tự lấy theo Tên Nhóm.", parse_mode=ParseMode.HTML)
                return
            customer_chat_id = input_chat_id
        else:
            customer_chat_id = group_chat_ids.get(group_name)
            if not customer_chat_id:
                await message.reply_text(f"⚠️ Không xác định được Chat ID của nhóm <b>{group_name}</b>. Vui lòng điền trực tiếp <b>Chat ID (Telegram)</b> trên Form, hoặc dùng lệnh /syncchat trong nhóm đó trước.", parse_mode=ParseMode.HTML)
                return

        # Check duplicate by customer_id
        existing = db.query(CreditCustomer).filter(CreditCustomer.customer_id == customer_id_str).first()
        if existing:
            await message.reply_text(f"⚠️ Mã Khách Hàng <b>{customer_id_str}</b> đã tồn tại trong hệ thống.", parse_mode=ParseMode.HTML)
            return

        from app.schemas.credit import CreditCustomerCreate
        from app.crud.credit import create_credit_customer

        new_customer = CreditCustomerCreate(
            customer_id=customer_id_str,
            group_name=group_name,
            customer_name=customer_name,
            contact_info=contact_info,
            chat_id=customer_chat_id,
            total_credit_limit=total_credit,
            remaining_credit_limit=remain_credit,
            total_principal_outstanding=total_principal,
            classification=classification
        )

        create_credit_customer(db, obj_in=new_customer)
        await message.reply_text(
            f"✅ Đã tạo khách hàng <b>{customer_name}</b> thành công!\n"
            f"Chat ID (Telegram): <code>{customer_chat_id}</code>",
            parse_mode=ParseMode.HTML
        )
        LogInfo(f"[CreateCustomer] Created customer {customer_name} ({contact_info}) chat_id={customer_chat_id} by {message.from_user.id}", LogType.SYSTEM_STATUS)

        # Delete the form template message after successful creation
        form_msg_id = form_tracker.pop(message.chat.id, "credit_create_customer", "create")
        if form_msg_id:
            try:
                await client.delete_messages(chat_id=message.chat.id, message_ids=form_msg_id)
            except Exception as del_err:
                LogError(f"Failed to delete credit create customer form: {del_err}", LogType.SYSTEM_STATUS)
    except Exception as e:
        LogError(f"Error in create_customer_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý lưu khách hàng.")
    finally:
        db.close()

# --- Check Customer (Interactive) ---
def _sid(uuid_val):
    """Shorten UUID to 32-char hex (no hyphens) for callback_data."""
    return str(uuid_val).replace("-", "")


def _uid(short_hex):
    """Restore UUID string from 32-char hex."""
    import uuid as _uuid
    return str(_uuid.UUID(short_hex))


def _build_update_contract_form(contract):
    """Form cập nhật hợp đồng tín dụng đã điền sẵn dữ liệu hiện tại."""
    def fmt_num(val):
        if val is None: return 0
        return int(val) if val == int(val) else val

    def fmt_dt(dt):
        return dt.strftime('%d/%m/%Y') if dt else ""

    customer = contract.customer

    return f"""<b>FORM CẬP NHẬT HỢP ĐỒNG TÍN DỤNG</b>
Vui lòng sao chép toàn bộ form dưới đây, chỉnh sửa thông tin cần thay đổi và gửi lại:

<pre>/credit_update_contract {contract.contract_id}
Mã Khách Hàng: {customer.customer_id if customer else ""}
Tên Nhóm: {customer.group_name if customer else ""}
Tên Khách Hàng: {customer.customer_name if customer else ""}
Liên Hệ Khách Hàng: {customer.contact_info if customer else ""}
Tổng Hạn Mức Tín Dụng: {fmt_num(customer.total_credit_limit) if customer else 0}
Hạn Mức Còn Lại: {fmt_num(customer.remaining_credit_limit) if customer else 0}
Tổng Nợ Gốc Hiện Tại: {fmt_num(customer.total_principal_outstanding) if customer else 0}
Mã Hợp Đồng: {contract.contract_id or ""}
Loại Hợp Đồng: {contract.loan_type or ""}
Tiền Nợ Gốc (Ban đầu): {fmt_num(contract.initial_principal)}
Ngày Bắt Đầu Vay (dd/mm/yyyy): {fmt_dt(contract.start_date)}
Ngày Đáo Hạn (dd/mm/yyyy): {fmt_dt(contract.due_date)}
Ngày Bắt Đầu Thu Lãi (dd/mm/yyyy): {fmt_dt(contract.interest_start_date)}
Lãi Suất / Tháng (%): {fmt_num(contract.monthly_interest_rate)}
Số Tiền Lãi / Tháng: {fmt_num(contract.monthly_interest_amount)}
Tổng Số Tiền Trả Gốc: {fmt_num(contract.total_principal_paid)}
Tiền Nợ Gốc Còn Lại: {fmt_num(contract.remaining_principal)}
Tổng Nợ Lãi: {fmt_num(contract.interest_debt or 0)}
Ghi Chú: {contract.notes or ""}
Gửi Tin Nhắn Phát Sinh (Có/Không): {"Có" if contract.send_message_arise else "Không"}
Nội Dung Tin Nhắn: {contract.message_content or ""}
Phân Loại: {contract.classification or ""}
</pre>"""


def _build_update_customer_form(customer):
    """Form cập nhật khách hàng tín dụng đã điền sẵn dữ liệu hiện tại."""
    def fmt_num(val):
        if val is None: return 0
        return int(val) if val == int(val) else val

    return f"""<b>FORM CẬP NHẬT KHÁCH HÀNG TÍN DỤNG</b>
Vui lòng sao chép form dưới đây, chỉnh sửa thông tin và gửi lại:

<pre>/credit_update_customer {customer.customer_id}
Mã Khách Hàng: {customer.customer_id or ""}
Tên Nhóm: {customer.group_name or ""}
Tên Khách Hàng: {customer.customer_name or ""}
Liên Hệ Khách Hàng: {customer.contact_info or ""}
Chat ID (Telegram): {customer.chat_id or ""}
Tổng Hạn Mức Tín Dụng: {fmt_num(customer.total_credit_limit)}
Hạn Mức Còn Lại: {fmt_num(customer.remaining_credit_limit)}
Tổng Nợ Gốc Hiện Tại: {fmt_num(customer.total_principal_outstanding)}
Phân Loại: {customer.classification or ""}
</pre>"""


def _build_cxkh_customer_list_keyboard(customers, page, selected_customer_id=None):
    """Build inline keyboard for customer list with pagination and radio select."""
    PAGE_SIZE = 10
    total = len(customers)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_customers = customers[start:end]

    sel_hex = _sid(selected_customer_id) if selected_customer_id else None

    buttons = []
    for c in page_customers:
        c_hex = _sid(c.id)
        is_selected = (c_hex == sel_hex) if sel_hex else False
        prefix = "✅" if is_selected else "⬜"
        label = f"{prefix} {c.customer_id} - {c.customer_name}"
        # ck_s|<32hex>|<page> = max ~40 chars
        buttons.append([InlineKeyboardButton(label, callback_data=f"ck_s|{c_hex}|{page}")])

    # Pagination row
    nav_row = []
    if page > 0:
        # ck_p|<page>|<32hex> = max ~41 chars
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"ck_p|{page - 1}|{sel_hex or ''}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"ck_p|{page + 1}|{sel_hex or ''}"))
    buttons.append(nav_row)

    # Action buttons
    action_row = []
    if sel_hex:
        # ck_uc|<32hex> = max ~38 chars, ck_uhd|<32hex> = max ~39 chars
        action_row.append(InlineKeyboardButton("Cập nhật KH", callback_data=f"ck_uc|{sel_hex}"))
        action_row.append(InlineKeyboardButton("Cập nhật HĐ", callback_data=f"ck_uhd|{sel_hex}"))
    buttons.append(action_row if action_row else [])
    buttons.append([InlineKeyboardButton("Hủy", callback_data="ck_x")])

    # Remove empty rows
    buttons = [row for row in buttons if row]

    return InlineKeyboardMarkup(buttons)


def _build_cxkh_contract_list_keyboard(contracts, page, customer_hex):
    """Build inline keyboard for contract list with pagination."""
    PAGE_SIZE = 10
    total = len(contracts)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_contracts = contracts[start:end]

    buttons = []
    for c in page_contracts:
        status_map = {
            CreditStatus.ACTIVE.value: "Đang vay",
            CreditStatus.PAID.value: "Tất toán",
            CreditStatus.BAD_DEBT.value: "Nợ xấu",
            CreditStatus.CANCELLED.value: "Đã hủy",
        }
        status_label = status_map.get(c.credit_status, "N/A")
        label = f"{c.contract_id} ({status_label})"
        c_hex = _sid(c.id)
        # ck_sc|<32hex> = max ~38 chars
        buttons.append([InlineKeyboardButton(label, callback_data=f"ck_sc|{c_hex}")])

    # Pagination row
    nav_row = []
    if page > 0:
        # ck_cp|<page>|<32hex> = max ~42 chars
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"ck_cp|{page - 1}|{customer_hex}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"ck_cp|{page + 1}|{customer_hex}"))
    buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("Hủy", callback_data="ck_x")])

    buttons = [row for row in buttons if row]
    return InlineKeyboardMarkup(buttons)

@bot.on_message(filters.command(["credit_check_customer", "credit_xem_khach_hang"]) | filters.regex(r"^@\w+\s+/(credit_check_customer|credit_xem_khach_hang)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(auto_delete_cmd=True)
async def check_customer_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_check_customer", "credit_xem_khach_hang"])
    if args is None: return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Danh sách khách hàng", callback_data="ck_list|0")],
        [InlineKeyboardButton("Hủy", callback_data="ck_x")]
    ])
    await message.reply_text(
        "<b>XEM KHÁCH HÀNG TÍN DỤNG</b>\n\nVui lòng chọn thao tác:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@bot.on_callback_query(filters.regex(r"^ck_noop$"))
async def ck_noop_callback(client, callback_query: CallbackQuery):
    await callback_query.answer()


@bot.on_callback_query(filters.regex(r"^ck_x$"))
async def ck_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()


@bot.on_callback_query(filters.regex(r"^ck_list\|(\d+)$"))
async def ck_show_list_callback(client, callback_query: CallbackQuery):
    page = int(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_name).all()

        if not customers:
            await callback_query.message.edit_text("ℹ️ Không có khách hàng nào trong dự án này.")
            return

        keyboard = _build_cxkh_customer_list_keyboard(customers, page)
        await callback_query.message.edit_text(
            "<b>DANH SÁCH KHÁCH HÀNG</b>\n\nChọn khách hàng để xem / thao tác:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in ck_show_list_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ck_s\|([a-f0-9]{32})\|(\d+)$"))
async def ck_sel_callback(client, callback_query: CallbackQuery):
    selected_hex = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))
    selected_uuid = _uid(selected_hex)
    db = SessionLocal()
    try:
        customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_name).all()

        if not customers:
            await callback_query.message.edit_text("Không có khách hàng nào.")
            return

        # Find selected customer for header info
        selected_cust = None
        for c in customers:
            if str(c.id) == selected_uuid:
                selected_cust = c
                break

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        header = "<b>DANH SÁCH KHÁCH HÀNG</b>\n\n"
        if selected_cust:
            header += (
                f"<b>Đã chọn:</b> {selected_cust.customer_name} ({selected_cust.customer_id})\n"
                f"Nhóm: {selected_cust.group_name or 'N/A'} | "
                f"Hạn mức: {fmt_num(selected_cust.total_credit_limit):,} VNĐ\n\n"
            )
        header += "Chọn khách hàng để xem / thao tác:"

        keyboard = _build_cxkh_customer_list_keyboard(customers, page, selected_uuid)
        await callback_query.message.edit_text(
            header,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in ck_sel_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ck_p\|(\d+)\|(.*)$"))
async def ck_page_callback(client, callback_query: CallbackQuery):
    page = int(callback_query.matches[0].group(1))
    selected_hex = callback_query.matches[0].group(2) or None
    selected_uuid = _uid(selected_hex) if selected_hex else None
    db = SessionLocal()
    try:
        customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_name).all()

        if not customers:
            await callback_query.message.edit_text("Không có khách hàng nào.")
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        header = "<b>DANH SÁCH KHÁCH HÀNG</b>\n\n"
        if selected_uuid:
            selected_cust = None
            for c in customers:
                if str(c.id) == selected_uuid:
                    selected_cust = c
                    break
            if selected_cust:
                header += (
                    f"<b>Đã chọn:</b> {selected_cust.customer_name} ({selected_cust.customer_id})\n"
                    f"Nhóm: {selected_cust.group_name or 'N/A'} | "
                    f"Hạn mức: {fmt_num(selected_cust.total_credit_limit):,} VNĐ\n\n"
                )
        header += "Chọn khách hàng để xem / thao tác:"

        keyboard = _build_cxkh_customer_list_keyboard(customers, page, selected_uuid)
        await callback_query.message.edit_text(
            header,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in ck_page_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ck_uc\|([a-f0-9]{32})$"))
async def ck_update_customer_callback(client, callback_query: CallbackQuery):
    """Show update customer form for the selected customer."""
    customer_hex = callback_query.matches[0].group(1)
    customer_uuid = _uid(customer_hex)
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
        if not customer:
            await callback_query.answer("⚠️ Không tìm thấy khách hàng.", show_alert=True)
            return

        form_msg = await callback_query.message.reply_text(
            _build_update_customer_form(customer), parse_mode=ParseMode.HTML
        )
        form_tracker.track(callback_query.message.chat.id, "credit_update_customer", customer.customer_id, form_msg.id)
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in ck_update_customer_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ck_uhd\|([a-f0-9]{32})$"))
async def ck_show_contract_list_callback(client, callback_query: CallbackQuery):
    """Show list of contracts for the selected customer."""
    customer_hex = callback_query.matches[0].group(1)
    customer_uuid = _uid(customer_hex)
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
        if not customer:
            await callback_query.answer("⚠️ Không tìm thấy khách hàng.", show_alert=True)
            return

        contracts = db.query(Credit).filter(Credit.customer_id == customer.id).all()
        if not contracts:
            await callback_query.answer("ℹ️ Khách hàng chưa có hợp đồng nào.", show_alert=True)
            return

        keyboard = _build_cxkh_contract_list_keyboard(contracts, 0, customer_hex)
        await callback_query.message.edit_text(
            f"<b>DANH SÁCH HỢP ĐỒNG</b>\n"
            f"Khách hàng: <b>{customer.customer_name}</b> ({customer.customer_id})\n\n"
            f"Chọn hợp đồng để cập nhật:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in ck_show_contract_list_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ck_cp\|(\d+)\|([a-f0-9]{32})$"))
async def ck_contract_page_callback(client, callback_query: CallbackQuery):
    """Paginate contract list."""
    page = int(callback_query.matches[0].group(1))
    customer_hex = callback_query.matches[0].group(2)
    customer_uuid = _uid(customer_hex)
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
        if not customer:
            await callback_query.answer("⚠️ Không tìm thấy khách hàng.", show_alert=True)
            return

        contracts = db.query(Credit).filter(Credit.customer_id == customer.id).all()
        if not contracts:
            await callback_query.answer("ℹ️ Không có hợp đồng.", show_alert=True)
            return

        keyboard = _build_cxkh_contract_list_keyboard(contracts, page, customer_hex)
        await callback_query.message.edit_text(
            f"<b>DANH SÁCH HỢP ĐỒNG</b>\n"
            f"Khách hàng: <b>{customer.customer_name}</b> ({customer.customer_id})\n\n"
            f"Chọn hợp đồng để cập nhật:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in ck_contract_page_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ck_sc\|([a-f0-9]{32})$"))
async def ck_select_contract_callback(client, callback_query: CallbackQuery):
    """Show update form for the selected contract."""
    contract_hex = callback_query.matches[0].group(1)
    contract_uuid = _uid(contract_hex)
    db = SessionLocal()
    try:
        contract = db.query(Credit).filter(Credit.id == contract_uuid).first()
        if not contract:
            await callback_query.answer("⚠️ Không tìm thấy hợp đồng.", show_alert=True)
            return

        form_msg = await callback_query.message.reply_text(
            _build_update_contract_form(contract), parse_mode=ParseMode.HTML
        )
        form_tracker.track(callback_query.message.chat.id, "credit_update_contract", contract.contract_id, form_msg.id)
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in ck_select_contract_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()

# --- Check Contract (Interactive) ---
def _build_chd_contract_list_keyboard(contracts, page, selected_contract_id=None):
    """Build inline keyboard for contract list with radio select and pagination."""
    PAGE_SIZE = 10
    total = len(contracts)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_contracts = contracts[start:end]

    sel_hex = _sid(selected_contract_id) if selected_contract_id else None

    buttons = []
    for c in page_contracts:
        c_hex = _sid(c.id)
        is_selected = (c_hex == sel_hex) if sel_hex else False
        prefix = "✅" if is_selected else "⬜"
        status_map = {
            CreditStatus.ACTIVE.value: "Đang vay",
            CreditStatus.PAID.value: "Tất toán",
            CreditStatus.BAD_DEBT.value: "Nợ xấu",
            CreditStatus.CANCELLED.value: "Đã hủy",
        }
        status_label = status_map.get(c.credit_status, "N/A")
        label = f"{prefix} {c.contract_id} ({status_label})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"chd_s|{c_hex}|{page}")])

    # Pagination row
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"chd_p|{page - 1}|{sel_hex or ''}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"chd_p|{page + 1}|{sel_hex or ''}"))
    buttons.append(nav_row)

    # Action buttons
    action_row = []
    if sel_hex:
        action_row.append(InlineKeyboardButton("Cập nhật hợp đồng", callback_data=f"chd_u|{sel_hex}"))
    buttons.append(action_row if action_row else [])
    buttons.append([InlineKeyboardButton("Hủy", callback_data="ck_x")])

    buttons = [row for row in buttons if row]
    return InlineKeyboardMarkup(buttons)


@bot.on_message(filters.command(["credit_check_contract", "credit_xem_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_check_contract|credit_xem_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(auto_delete_cmd=True)
async def check_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_check_contract", "credit_xem_hop_dong"])
    if args is None: return

    db = SessionLocal()
    try:
        contracts = db.query(Credit).all()
        if not contracts:
            await message.reply_text("Không có hợp đồng nào trong hệ thống.")
            return

        keyboard = _build_chd_contract_list_keyboard(contracts, 0)
        await message.reply_text(
            "<b>DANH SÁCH HỢP ĐỒNG</b>\n\nChọn hợp đồng để xem / thao tác:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LogError(f"Error in check_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("Có lỗi xảy ra.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^chd_s\|([a-f0-9]{32})\|(\d+)$"))
async def chd_sel_callback(client, callback_query: CallbackQuery):
    selected_hex = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))
    selected_uuid = _uid(selected_hex)
    db = SessionLocal()
    try:
        contracts = db.query(Credit).all()
        if not contracts:
            await callback_query.message.edit_text("Không có hợp đồng nào.")
            return

        # Find selected contract for header info
        selected_ct = None
        for c in contracts:
            if str(c.id) == selected_uuid:
                selected_ct = c
                break

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        header = "<b>DANH SÁCH HỢP ĐỒNG</b>\n\n"
        if selected_ct:
            cust = selected_ct.customer
            cust_name = cust.customer_name if cust else "N/A"
            header += (
                f"<b>Đã chọn:</b> {selected_ct.contract_id}\n"
                f"Khách hàng: {cust_name}\n"
                f"Còn nợ: {fmt_num(selected_ct.remaining_principal):,} VNĐ\n\n"
            )
        header += "Chọn hợp đồng để xem / thao tác:"

        keyboard = _build_chd_contract_list_keyboard(contracts, page, selected_uuid)
        await callback_query.message.edit_text(
            header,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in chd_sel_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^chd_p\|(\d+)\|(.*)$"))
async def chd_page_callback(client, callback_query: CallbackQuery):
    page = int(callback_query.matches[0].group(1))
    selected_hex = callback_query.matches[0].group(2) or None
    selected_uuid = _uid(selected_hex) if selected_hex else None
    db = SessionLocal()
    try:
        contracts = db.query(Credit).all()
        if not contracts:
            await callback_query.message.edit_text("Không có hợp đồng nào.")
            return

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        header = "<b>DANH SÁCH HỢP ĐỒNG</b>\n\n"
        if selected_uuid:
            selected_ct = None
            for c in contracts:
                if str(c.id) == selected_uuid:
                    selected_ct = c
                    break
            if selected_ct:
                cust = selected_ct.customer
                cust_name = cust.customer_name if cust else "N/A"
                header += (
                    f"<b>Đã chọn:</b> {selected_ct.contract_id}\n"
                    f"Khách hàng: {cust_name}\n"
                    f"Còn nợ: {fmt_num(selected_ct.remaining_principal):,} VNĐ\n\n"
                )
        header += "Chọn hợp đồng để xem / thao tác:"

        keyboard = _build_chd_contract_list_keyboard(contracts, page, selected_uuid)
        await callback_query.message.edit_text(
            header,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in chd_page_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^chd_u\|([a-f0-9]{32})$"))
async def chd_update_contract_callback(client, callback_query: CallbackQuery):
    """Show update form for the selected contract."""
    contract_hex = callback_query.matches[0].group(1)
    contract_uuid = _uid(contract_hex)
    db = SessionLocal()
    try:
        contract = db.query(Credit).filter(Credit.id == contract_uuid).first()
        if not contract:
            await callback_query.answer("Không tìm thấy hợp đồng.", show_alert=True)
            return

        form_msg = await callback_query.message.reply_text(
            _build_update_contract_form(contract), parse_mode=ParseMode.HTML
        )
        form_tracker.track(callback_query.message.chat.id, "credit_update_contract", contract.contract_id, form_msg.id)
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in chd_update_contract_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()

# --- Check Debt (Xem Công Nợ Hiện Tại) ---
@bot.on_message(filters.command(["credit_check_debt", "credit_xem_cong_no"]) | filters.regex(r"^@\w+\s+/(credit_check_debt|credit_xem_cong_no)\b"))
@require_user_type(UserType.MEMBER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("member")
@command_timeout(auto_delete_cmd=True)
async def check_debt_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_check_debt", "credit_xem_cong_no"])
    if args is None: return

    db = SessionLocal()
    try:
        # Xác định khách hàng theo chat_id của chính nhóm gửi lệnh
        customers = _cmv_customers(db, message.chat.id)
        if not customers:
            await message.reply_text("ℹ️ Nhóm này chưa được gắn với khách hàng tín dụng nào.")
            return

        if len(customers) > 1:
            await message.reply_text(
                "<b>CÔNG NỢ HIỆN TẠI</b>\n\nChọn khách hàng để xem công nợ:",
                reply_markup=_cmv_customer_pick_keyboard(customers, "cmv_cn"),
                parse_mode=ParseMode.HTML
            )
            return

        customer = customers[0]

        # Lấy các hợp đồng đang vay / nợ xấu
        active_credits = db.query(Credit).filter(
            Credit.customer_id == customer.id,
            Credit.credit_status.in_([CreditStatus.ACTIVE.value, CreditStatus.BAD_DEBT.value])
        ).all()

        if not active_credits:
            await message.reply_text(f"ℹ️ <b>{customer.customer_name}</b>, bạn hiện không có hợp đồng công nợ nào.", parse_mode=ParseMode.HTML)
            return

        await message.reply_text(
            _cmv_debt_text(customer, active_credits),
            reply_markup=_cmv_debt_keyboard(),
            parse_mode=ParseMode.HTML
        )
        LogInfo(f"[CheckDebt] {customer.customer_id} checked their debt from chat {message.chat.id}: {len(active_credits)} contracts", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in check_debt_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra khi truy xuất công nợ.")
    finally:
        db.close()

# --- Update Customer ---
def _cuk_customer_list_keyboard(customers, page):
    """Bàn phím chọn khách hàng để cập nhật: tối đa 10 nút/trang, có Trước/Sau và Hủy."""
    PAGE_SIZE = 10
    total = len(customers)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_customers = customers[start:min(start + PAGE_SIZE, total)]

    buttons = [
        [InlineKeyboardButton(
            f"{c.customer_id} - {c.customer_name}",
            callback_data=f"cuk_s|{_sid(c.id)}"
        )]
        for c in page_customers
    ]

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"cuk_p|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"cuk_p|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("Hủy", callback_data="cuk_x")])
    return InlineKeyboardMarkup(buttons)


@bot.on_callback_query(filters.regex(r"^cuk_x$"))
@require_group_role("main")
async def cuk_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()


@bot.on_callback_query(filters.regex(r"^cuk_p\|(\d+)$"))
@require_group_role("main")
async def cuk_page_callback(client, callback_query: CallbackQuery):
    """Phân trang danh sách khách hàng khi cập nhật."""
    page = int(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
        if not customers:
            await callback_query.message.edit_text("ℹ️ Chưa có khách hàng nào trong hệ thống.")
            return

        await callback_query.message.edit_text(
            "<b>CẬP NHẬT KHÁCH HÀNG TÍN DỤNG</b>\n\nChọn khách hàng cần cập nhật:",
            reply_markup=_cuk_customer_list_keyboard(customers, page),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cuk_page_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cuk_s\|([a-f0-9]{32})$"))
@require_group_role("main")
async def cuk_select_customer_callback(client, callback_query: CallbackQuery):
    """Chọn khách hàng -> hiển thị form cập nhật cho khách hàng đó."""
    customer_uuid = _uid(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
        if not customer:
            await callback_query.answer("⚠️ Không tìm thấy khách hàng.", show_alert=True)
            return

        form_msg = await callback_query.message.reply_text(
            _build_update_customer_form(customer), parse_mode=ParseMode.HTML
        )
        form_tracker.track(callback_query.message.chat.id, "credit_update_customer", customer.customer_id, form_msg.id)
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cuk_select_customer_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_message(filters.command(["credit_update_customer", "credit_cap_nhat_khach_hang"]) | filters.regex(r"^@\w+\s+/(credit_update_customer|credit_cap_nhat_khach_hang)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(timeout_seconds=600, auto_delete_cmd=True)  # Form nhiều trường -> cần thời gian điền
async def update_customer_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_update_customer", "credit_cap_nhat_khach_hang"])
    if args is None: return

    db = SessionLocal()
    try:
        lines = message.text.strip().split("\n")
        
        # Generate form
        if len(lines) < 3:
            # Không kèm Mã Khách Hàng -> hiển thị danh sách khách hàng để chọn
            if len(args) < 2:
                customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
                if not customers:
                    await message.reply_text("ℹ️ Chưa có khách hàng nào trong hệ thống.")
                    return

                await message.reply_text(
                    "<b>CẬP NHẬT KHÁCH HÀNG TÍN DỤNG</b>\n\nChọn khách hàng cần cập nhật:",
                    reply_markup=_cuk_customer_list_keyboard(customers, 0),
                    parse_mode=ParseMode.HTML
                )
                return

            from sqlalchemy import or_
            lookup_key = args[1]
            customer = db.query(CreditCustomer).filter(
                or_(CreditCustomer.customer_id == lookup_key, CreditCustomer.group_name == lookup_key)
            ).first()
            if not customer:
                await message.reply_text(f"⚠️ Khách hàng <b>{lookup_key}</b> chưa tồn tại trong hệ thống.", parse_mode=ParseMode.HTML)
                return

            form_msg = await message.reply_text(_build_update_customer_form(customer), parse_mode=ParseMode.HTML)
            form_tracker.track(message.chat.id, "credit_update_customer", customer.customer_id, form_msg.id)
            return

        # Parse Form
        if len(args) < 2:
            await message.reply_text("⚠️ Không tìm thấy khách hàng mục tiêu trong lệnh.", parse_mode=ParseMode.HTML)
            return
            
        from sqlalchemy import or_
        target_customer_id = args[1]
        customer = db.query(CreditCustomer).filter(
            or_(CreditCustomer.customer_id == target_customer_id, CreditCustomer.group_name == target_customer_id)
        ).first()
        if not customer:
            await message.reply_text(f"⚠️ Không tìm thấy khách hàng <b>{target_customer_id}</b> để cập nhật.", parse_mode=ParseMode.HTML)
            return

        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        new_customer_id = data.get("Mã Khách Hàng", customer.customer_id or "")
        group_name = data.get("Tên Nhóm", "")
        customer_name = data.get("Tên Khách Hàng", "")
        new_contact_info = data.get("Liên Hệ Khách Hàng", "")
        input_chat_id = data.get("Chat ID (Telegram)", "").strip()
        total_credit_str = data.get("Tổng Hạn Mức Tín Dụng", "0")
        remain_credit_str = data.get("Hạn Mức Còn Lại", "")
        total_principal_str = data.get("Tổng Nợ Gốc Hiện Tại", "0")
        classification = data.get("Phân Loại", customer.classification or "").strip()

        if not customer_name:
            await message.reply_text("⚠️ <b>Tên Khách Hàng</b> là bắt buộc.", parse_mode=ParseMode.HTML)
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

        # Check customer_id uniqueness if changed
        if new_customer_id and new_customer_id != customer.customer_id:
            existing = db.query(CreditCustomer).filter(CreditCustomer.customer_id == new_customer_id).first()
            if existing:
                await message.reply_text(f"⚠️ Mã Khách Hàng mới <b>{new_customer_id}</b> đã bị trùng lặp với một khách hàng khác.", parse_mode=ParseMode.HTML)
                return

        # Validate group_name
        chat_id = str(message.chat.id)
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        new_chat_id = customer.chat_id
        valid_members = []
        if current_project_member:
            valid_members = db.query(TelegramProjectMember).filter(
                TelegramProjectMember.project_id == current_project_member.project_id,
                TelegramProjectMember.role == "member"
            ).all()

        if valid_members and group_name:
            valid_groups = [m.group_name for m in valid_members if m.group_name]

            if group_name not in valid_groups:
                await message.reply_text(f"⚠️ Nhóm <b>{group_name}</b> không hợp lệ hoặc chưa được đồng bộ trong dự án.", parse_mode=ParseMode.HTML)
                return

            # Đồng bộ lại Chat ID nhóm member theo Tên Nhóm mới
            for m in valid_members:
                if m.group_name == group_name and m.chat_id:
                    new_chat_id = str(m.chat_id)
                    break

        # Chat ID nhập tay trên Form được ưu tiên hơn giá trị suy ra từ Tên Nhóm
        if input_chat_id:
            valid_chat_ids = {str(m.chat_id) for m in valid_members if m.chat_id}
            if valid_chat_ids and input_chat_id not in valid_chat_ids:
                await message.reply_text(f"⚠️ Chat ID <b>{input_chat_id}</b> không thuộc nhóm member nào của dự án. Vui lòng kiểm tra lại hoặc để trống để bot tự lấy theo Tên Nhóm.", parse_mode=ParseMode.HTML)
                return
            new_chat_id = input_chat_id

        customer.customer_id = new_customer_id
        customer.group_name = group_name
        customer.customer_name = customer_name
        customer.contact_info = new_contact_info
        customer.chat_id = new_chat_id
        customer.total_credit_limit = total_credit
        customer.remaining_credit_limit = remain_credit
        customer.total_principal_outstanding = total_principal
        customer.classification = classification
        
        db.commit()
        await message.reply_text(
            f"✅ Đã cập nhật thông tin khách hàng <b>{customer_name}</b> (Mã: {new_customer_id}) thành công!\n"
            f"Chat ID (Telegram): <code>{new_chat_id or 'Chưa có'}</code>",
            parse_mode=ParseMode.HTML
        )
        LogInfo(f"[UpdateCustomer] Updated customer {customer_name} (ID: {new_customer_id}) by {message.from_user.id}", LogType.SYSTEM_STATUS)

        # Delete the form template message after successful update
        form_msg_id = form_tracker.pop(message.chat.id, "credit_update_customer", target_customer_id)
        if form_msg_id:
            try:
                await client.delete_messages(chat_id=message.chat.id, message_ids=form_msg_id)
            except Exception as del_err:
                LogError(f"Failed to delete credit update customer form: {del_err}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in update_customer_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình cập nhật khách hàng.")
    finally:
        db.close()

# --- Create Contract ---
def _build_create_contract_form(customer):
    """Form tạo hợp đồng tín dụng đã điền sẵn thông tin khách hàng."""
    def fmt_num(val):
        if val is None:
            return 0
        return int(val) if val == int(val) else val

    return f"""<b>FORM TẠO HỢP ĐỒNG TÍN DỤNG</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/credit_create_contract {customer.customer_id}
Mã Khách Hàng: {customer.customer_id or ""}
Tên Nhóm: {customer.group_name or ""}
Tên Khách Hàng: {customer.customer_name or ""}
Liên Hệ Khách Hàng: {customer.contact_info or ""}
Tổng Hạn Mức Tín Dụng: {fmt_num(customer.total_credit_limit)}
Hạn Mức Còn Lại: {fmt_num(customer.remaining_credit_limit)}
Tổng Nợ Gốc Hiện Tại: {fmt_num(customer.total_principal_outstanding)}
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
Phân Loại: {customer.classification or "KCredit"}
</pre>

<i>Ví dụ mã hợp đồng: HD220101. Loại hợp đồng gồm (Thế chấp [secured], Tín chấp [unsecured]). Phân loại gồm: KCredit, PQCredit, QCredit, ...</i>"""


def _cch_customer_list_keyboard(customers, page):
    """Bàn phím chọn khách hàng để tạo hợp đồng: tối đa 10 nút/trang, có Trước/Sau và Hủy."""
    PAGE_SIZE = 10
    total = len(customers)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_customers = customers[start:min(start + PAGE_SIZE, total)]

    buttons = [
        [InlineKeyboardButton(
            f"{c.customer_id} - {c.customer_name}",
            callback_data=f"cch_s|{_sid(c.id)}"
        )]
        for c in page_customers
    ]

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"cch_p|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"cch_p|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("Hủy", callback_data="cch_x")])
    return InlineKeyboardMarkup(buttons)


@bot.on_callback_query(filters.regex(r"^cch_x$"))
@require_group_role("main")
async def cch_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()


@bot.on_callback_query(filters.regex(r"^cch_p\|(\d+)$"))
@require_group_role("main")
async def cch_page_callback(client, callback_query: CallbackQuery):
    """Phân trang danh sách khách hàng khi tạo hợp đồng."""
    page = int(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
        if not customers:
            await callback_query.message.edit_text("ℹ️ Chưa có khách hàng nào trong hệ thống.")
            return

        await callback_query.message.edit_text(
            "<b>TẠO HỢP ĐỒNG TÍN DỤNG</b>\n\nChọn khách hàng cần tạo hợp đồng:",
            reply_markup=_cch_customer_list_keyboard(customers, page),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cch_page_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cch_s\|([a-f0-9]{32})$"))
@require_group_role("main")
async def cch_select_customer_callback(client, callback_query: CallbackQuery):
    """Chọn khách hàng -> hiển thị form tạo hợp đồng cho khách hàng đó."""
    customer_uuid = _uid(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
        if not customer:
            await callback_query.answer("⚠️ Không tìm thấy khách hàng.", show_alert=True)
            return

        form_msg = await callback_query.message.reply_text(
            _build_create_contract_form(customer), parse_mode=ParseMode.HTML
        )
        form_tracker.track(callback_query.message.chat.id, "credit_create_contract", customer.customer_id, form_msg.id)
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cch_select_customer_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_message(filters.command(["credit_create_contract", "credit_tao_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_create_contract|credit_tao_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(timeout_seconds=600, auto_delete_cmd=True)  # Form nhiều trường -> cần thời gian điền
async def create_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_create_contract", "credit_tao_hop_dong"])
    if args is None: return

    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        # Simple verification if they only typed "/create_contract KH001"
        lines = message.text.strip().split("\n")
        if len(lines) < 3:
            # Không kèm Mã Khách Hàng -> hiển thị danh sách khách hàng để chọn
            if len(args) < 2:
                customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
                if not customers:
                    await message.reply_text("ℹ️ Chưa có khách hàng nào trong hệ thống. Vui lòng tạo khách hàng bằng lệnh /credit_tao_khach_hang trước.")
                    return

                await message.reply_text(
                    "<b>TẠO HỢP ĐỒNG TÍN DỤNG</b>\n\nChọn khách hàng cần tạo hợp đồng:",
                    reply_markup=_cch_customer_list_keyboard(customers, 0),
                    parse_mode=ParseMode.HTML
                )
                return

            from sqlalchemy import or_
            lookup_key = args[1]
            customer = db.query(CreditCustomer).filter(
                or_(CreditCustomer.customer_id == lookup_key, CreditCustomer.group_name == lookup_key)
            ).first()
            if not customer:
                await message.reply_text(f"⚠️ Khách hàng <b>{lookup_key}</b> chưa tồn tại trong hệ thống. Vui lòng tạo thông tin khách hàng bằng lệnh /credit_create_customer trước.", parse_mode=ParseMode.HTML)
                return

            form_msg = await message.reply_text(_build_create_contract_form(customer), parse_mode=ParseMode.HTML)
            form_tracker.track(message.chat.id, "credit_create_contract", customer.customer_id, form_msg.id)
            return


        # If user actually submitted data in the form format
        data = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        customer_id_input = data.get("Mã Khách Hàng", "")
        group_name = data.get("Tên Nhóm", "")
        
        if customer_id_input:
            customer = db.query(CreditCustomer).filter(CreditCustomer.customer_id == customer_id_input).first()
        elif group_name:
            customer = db.query(CreditCustomer).filter(CreditCustomer.group_name == group_name).first()
        elif len(args) > 1:
            target = args[1]
            customer = db.query(CreditCustomer).filter(
                or_(CreditCustomer.customer_id == target, CreditCustomer.group_name == target)
            ).first()
        else:
            customer = None
            
        if not customer:
            await message.reply_text(f"⚠️ Khách hàng chưa tồn tại trong hệ thống. Vui lòng tạo khách trước.", parse_mode=ParseMode.HTML)
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
        classification = data.get("Phân Loại", customer.classification or "").strip()
        
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
        is_sec = False
        if loan_type:
            is_sec = loan_type.lower().strip() in ["secured", "thế chấp", "the chap", "collateral"]
        if is_sec:
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
            interest_debt=0.0,
            credit_status=CreditStatus.ACTIVE,
            classification=classification
        )
        
        create_credit(db, obj_in=new_contract)
        await message.reply_text(f"✅ Đã tạo hợp đồng <b>{contract_id}</b> cho khách hàng <b>{customer.customer_name}</b> thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[CreateContract] Created contract {contract_id} for {customer.customer_name} by {message.from_user.id}", LogType.SYSTEM_STATUS)

        # Delete the form template message after successful creation
        form_msg_id = form_tracker.pop(message.chat.id, "credit_create_contract", customer.customer_id)
        if form_msg_id:
            try:
                await client.delete_messages(chat_id=message.chat.id, message_ids=form_msg_id)
            except Exception as del_err:
                LogError(f"Failed to delete credit create contract form: {del_err}", LogType.SYSTEM_STATUS)
        
    except Exception as e:
        LogError(f"Error in create_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()

# --- Update Contract ---
def _cuh_customer_list_keyboard(customers, page):
    """Bàn phím chọn khách hàng để cập nhật hợp đồng: tối đa 10 nút/trang, có Trước/Sau và Hủy."""
    PAGE_SIZE = 10
    total = len(customers)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_customers = customers[start:min(start + PAGE_SIZE, total)]

    buttons = [
        [InlineKeyboardButton(
            f"{c.customer_id} - {c.customer_name}",
            callback_data=f"cuh_c|{_sid(c.id)}|0"
        )]
        for c in page_customers
    ]

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"cuh_cp|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"cuh_cp|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("Hủy", callback_data="cuh_x")])
    return InlineKeyboardMarkup(buttons)


def _cuh_contract_list_keyboard(contracts, page, customer_hex):
    """Bàn phím chọn hợp đồng của một khách hàng: tối đa 10 nút/trang, có Trước/Sau, Quay lại và Hủy."""
    PAGE_SIZE = 10
    total = len(contracts)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_contracts = contracts[start:min(start + PAGE_SIZE, total)]

    buttons = []
    for c in page_contracts:
        status_label = _CMV_STATUS_LABELS.get(c.credit_status, "N/A")
        buttons.append([InlineKeyboardButton(
            f"{c.contract_id} ({status_label})",
            callback_data=f"cuh_s|{_sid(c.id)}"
        )])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"cuh_c|{customer_hex}|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"cuh_c|{customer_hex}|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton("Quay lại", callback_data="cuh_cp|0"),
        InlineKeyboardButton("Hủy", callback_data="cuh_x")
    ])
    return InlineKeyboardMarkup(buttons)


@bot.on_callback_query(filters.regex(r"^cuh_x$"))
@require_group_role("main")
async def cuh_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()


@bot.on_callback_query(filters.regex(r"^cuh_cp\|(\d+)$"))
@require_group_role("main")
async def cuh_customer_page_callback(client, callback_query: CallbackQuery):
    """Phân trang / quay lại danh sách khách hàng khi cập nhật hợp đồng."""
    page = int(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
        if not customers:
            await callback_query.message.edit_text("ℹ️ Chưa có khách hàng nào trong hệ thống.")
            return

        await callback_query.message.edit_text(
            "<b>CẬP NHẬT HỢP ĐỒNG TÍN DỤNG</b>\n\nChọn khách hàng:",
            reply_markup=_cuh_customer_list_keyboard(customers, page),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cuh_customer_page_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cuh_c\|([a-f0-9]{32})\|(\d+)$"))
@require_group_role("main")
async def cuh_contract_list_callback(client, callback_query: CallbackQuery):
    """Chọn khách hàng -> danh sách hợp đồng của khách hàng đó."""
    customer_hex = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == _uid(customer_hex)).first()
        if not customer:
            await callback_query.answer("⚠️ Không tìm thấy khách hàng.", show_alert=True)
            return

        contracts = db.query(Credit).filter(
            Credit.customer_id == customer.id,
            Credit.credit_status != CreditStatus.CANCELLED.value
        ).order_by(Credit.contract_id).all()
        if not contracts:
            await callback_query.answer("ℹ️ Khách hàng chưa có hợp đồng nào.", show_alert=True)
            return

        await callback_query.message.edit_text(
            f"<b>DANH SÁCH HỢP ĐỒNG</b>\n"
            f"Khách hàng: <b>{customer.customer_name}</b> ({customer.customer_id})\n\n"
            f"Chọn hợp đồng cần cập nhật:",
            reply_markup=_cuh_contract_list_keyboard(contracts, page, customer_hex),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cuh_contract_list_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cuh_s\|([a-f0-9]{32})$"))
@require_group_role("main")
async def cuh_select_contract_callback(client, callback_query: CallbackQuery):
    """Chọn hợp đồng -> hiển thị form cập nhật hợp đồng đó."""
    db = SessionLocal()
    try:
        contract = db.query(Credit).filter(Credit.id == _uid(callback_query.matches[0].group(1))).first()
        if not contract:
            await callback_query.answer("⚠️ Không tìm thấy hợp đồng.", show_alert=True)
            return

        form_msg = await callback_query.message.reply_text(
            _build_update_contract_form(contract), parse_mode=ParseMode.HTML
        )
        form_tracker.track(callback_query.message.chat.id, "credit_update_contract", contract.contract_id, form_msg.id)
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cuh_select_contract_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_message(filters.command(["credit_update_contract", "credit_cap_nhat_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_update_contract|credit_cap_nhat_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(timeout_seconds=600, auto_delete_cmd=True)  # Form nhiều trường -> cần thời gian điền
async def update_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_update_contract", "credit_cap_nhat_hop_dong"])
    if args is None: return

    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        # Không kèm Mã Hợp Đồng -> hiển thị danh sách khách hàng để chọn
        if len(args) < 2:
            customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
            if not customers:
                await message.reply_text("ℹ️ Chưa có khách hàng nào trong hệ thống.")
                return

            await message.reply_text(
                "<b>CẬP NHẬT HỢP ĐỒNG TÍN DỤNG</b>\n\nChọn khách hàng:",
                reply_markup=_cuh_customer_list_keyboard(customers, 0),
                parse_mode=ParseMode.HTML
            )
            return

        contract_code = args[1]
        # Check which project this chat belongs to
        current_project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id
        ).first()

        if not current_project_member:
            await message.reply_text("⚠️ Nhóm này chưa được đồng bộ vào dự án nào. Vui lòng sử dụng lệnh /syncchat trước.")
            return

        project_id = current_project_member.project_id

        # Get all valid group names from member groups of this project
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.role == "member"
        ).all()

        valid_groups = []
        for m in valid_members:
            if m.group_name:
                valid_groups.append(m.group_name)

        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        if not contract.customer or not contract.customer.group_name or contract.customer.group_name not in valid_groups:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không thuộc về nhóm hợp lệ nào trong dự án hiện tại.", parse_mode=ParseMode.HTML)
            return

        if contract.credit_status == CreditStatus.CANCELLED.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã bị hủy.", parse_mode=ParseMode.HTML)
            return

        lines = message.text.strip().split("\n")
        if len(lines) < 3:
            form_msg = await message.reply_text(_build_update_contract_form(contract), parse_mode=ParseMode.HTML)
            form_tracker.track(message.chat.id, "credit_update_contract", contract_code, form_msg.id)
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

        interest_debt_val = parse_float(data.get("Tổng Nợ Lãi", ""))
        notes = data.get("Ghi Chú", "")
        send_msg_str = data.get("Gửi Tin Nhắn Phát Sinh (Có/Không)", "").lower()
        send_msg = True if "có" in send_msg_str else False
        msg_content = data.get("Nội Dung Tin Nhắn", "")
        classification = data.get("Phân Loại", contract.classification or "").strip()

        # Re-evaluate limits if loan_type or principal changed
        old_initial_principal = contract.initial_principal or 0.0
        customer = contract.customer
        
        if customer:
            limit_remaining = customer.remaining_credit_limit or 0.0
            
            # Temporary refund old loan to available limit
            temp_limit = limit_remaining + old_initial_principal
            is_sec = False
            if loan_type:
                is_sec = loan_type.lower().strip() in ["secured", "thế chấp", "the chap", "collateral"]
            if is_sec:
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
        contract.interest_debt = interest_debt_val
        contract.classification = classification
        
        db.commit()
        await message.reply_text(f"✅ Đã cập nhật hợp đồng <b>{new_contract_id}</b> thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[UpdateContract] Updated contract {new_contract_id} by {message.from_user.id}", LogType.SYSTEM_STATUS)

        # Delete the form template message after successful update
        form_msg_id = form_tracker.pop(message.chat.id, "credit_update_contract", contract_code)
        if form_msg_id:
            try:
                await client.delete_messages(chat_id=message.chat.id, message_ids=form_msg_id)
            except Exception as del_err:
                LogError(f"Failed to delete credit update contract form: {del_err}", LogType.SYSTEM_STATUS)
        
    except Exception as e:
        LogError(f"Error in update_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()

# --- Cancel Contract ---
def _cancel_contract_confirm(contract):
    """Nội dung + bàn phím xác nhận hủy một hợp đồng."""
    customer = contract.customer
    remaining = contract.remaining_principal if contract.remaining_principal is not None else 0

    text = (
        f"<b>XÁC NHẬN HỦY HỢP ĐỒNG</b>\n\n"
        f"- Tên Khách Hàng: <b>{customer.customer_name if customer else 'N/A'}</b>\n"
        f"- Mã Hợp Đồng: <b>{contract.contract_id}</b>\n"
        f"- Trạng Thái: <b>{contract.credit_status.upper() if contract.credit_status else 'UNKNOWN'}</b>\n"
        f"- Lãi Suất: <b>{contract.monthly_interest_rate}% / Tháng</b>\n"
        f"- Dư Nợ Gốc: <b>{remaining:,.0f} Đ</b>\n\n"
        f"Bạn có chắc chắn muốn hủy hợp đồng <b>{contract.contract_id}</b> không?"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Xác nhận", callback_data=f"cc_confirm_{contract.id}"),
        InlineKeyboardButton("Hủy", callback_data="cc_exit")
    ]])
    return text, keyboard


def _chh_customer_list_keyboard(customers, page):
    """Bàn phím chọn khách hàng để hủy hợp đồng: tối đa 10 nút/trang, có Trước/Sau và Hủy."""
    PAGE_SIZE = 10
    total = len(customers)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_customers = customers[start:min(start + PAGE_SIZE, total)]

    buttons = [
        [InlineKeyboardButton(
            f"{c.customer_id} - {c.customer_name}",
            callback_data=f"chh_c|{_sid(c.id)}|0"
        )]
        for c in page_customers
    ]

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"chh_cp|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"chh_cp|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("Hủy", callback_data="cc_exit")])
    return InlineKeyboardMarkup(buttons)


def _chh_contract_list_keyboard(contracts, page, customer_hex):
    """Bàn phím chọn hợp đồng cần hủy: tối đa 10 nút/trang, có Trước/Sau, Quay lại và Hủy."""
    PAGE_SIZE = 10
    total = len(contracts)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_contracts = contracts[start:min(start + PAGE_SIZE, total)]

    buttons = []
    for c in page_contracts:
        status_label = _CMV_STATUS_LABELS.get(c.credit_status, "N/A")
        buttons.append([InlineKeyboardButton(
            f"{c.contract_id} ({status_label})",
            callback_data=f"chh_s|{_sid(c.id)}"
        )])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"chh_c|{customer_hex}|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"chh_c|{customer_hex}|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton("Quay lại", callback_data="chh_cp|0"),
        InlineKeyboardButton("Hủy", callback_data="cc_exit")
    ])
    return InlineKeyboardMarkup(buttons)


@bot.on_callback_query(filters.regex(r"^chh_cp\|(\d+)$"))
@require_group_role("main")
async def chh_customer_page_callback(client, callback_query: CallbackQuery):
    """Phân trang / quay lại danh sách khách hàng khi hủy hợp đồng."""
    page = int(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
        if not customers:
            await callback_query.message.edit_text("ℹ️ Chưa có khách hàng nào trong hệ thống.")
            return

        await callback_query.message.edit_text(
            "<b>HỦY HỢP ĐỒNG TÍN DỤNG</b>\n\nChọn khách hàng:",
            reply_markup=_chh_customer_list_keyboard(customers, page),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in chh_customer_page_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^chh_c\|([a-f0-9]{32})\|(\d+)$"))
@require_group_role("main")
async def chh_contract_list_callback(client, callback_query: CallbackQuery):
    """Chọn khách hàng -> danh sách hợp đồng có thể hủy."""
    customer_hex = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == _uid(customer_hex)).first()
        if not customer:
            await callback_query.answer("⚠️ Không tìm thấy khách hàng.", show_alert=True)
            return

        contracts = db.query(Credit).filter(
            Credit.customer_id == customer.id,
            Credit.credit_status != CreditStatus.CANCELLED.value
        ).order_by(Credit.contract_id).all()
        if not contracts:
            await callback_query.answer("ℹ️ Khách hàng không có hợp đồng nào có thể hủy.", show_alert=True)
            return

        await callback_query.message.edit_text(
            f"<b>DANH SÁCH HỢP ĐỒNG</b>\n"
            f"Khách hàng: <b>{customer.customer_name}</b> ({customer.customer_id})\n\n"
            f"Chọn hợp đồng cần hủy:",
            reply_markup=_chh_contract_list_keyboard(contracts, page, customer_hex),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in chh_contract_list_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^chh_s\|([a-f0-9]{32})$"))
@require_group_role("main")
async def chh_select_contract_callback(client, callback_query: CallbackQuery):
    """Chọn hợp đồng -> thông báo xác nhận hủy kèm 2 nút Xác nhận / Hủy."""
    db = SessionLocal()
    try:
        contract = db.query(Credit).filter(Credit.id == _uid(callback_query.matches[0].group(1))).first()
        if not contract:
            await callback_query.answer("⚠️ Không tìm thấy hợp đồng.", show_alert=True)
            return

        if contract.credit_status == CreditStatus.CANCELLED.value:
            await callback_query.answer(f"Hợp đồng {contract.contract_id} đã bị hủy từ trước.", show_alert=True)
            return

        text, keyboard = _cancel_contract_confirm(contract)
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in chh_select_contract_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_message(filters.command(["credit_cancel_contract", "credit_huy_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_cancel_contract|credit_huy_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(auto_delete_cmd=True)
async def cancel_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_cancel_contract", "credit_huy_hop_dong"])
    if args is None: return

    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        # Không kèm Mã Hợp Đồng -> hiển thị danh sách khách hàng để chọn
        if len(args) < 2:
            customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
            if not customers:
                await message.reply_text("ℹ️ Chưa có khách hàng nào trong hệ thống.")
                return

            await message.reply_text(
                "<b>HỦY HỢP ĐỒNG TÍN DỤNG</b>\n\nChọn khách hàng:",
                reply_markup=_chh_customer_list_keyboard(customers, 0),
                parse_mode=ParseMode.HTML
            )
            return

        contract_code = args[1]

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
            TelegramProjectMember.role == "member"
        ).all()

        valid_groups = []
        for m in valid_members:
            if m.group_name:
                valid_groups.append(m.group_name)

        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        if not contract.customer or not contract.customer.group_name or contract.customer.group_name not in valid_groups:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không thuộc về khách hàng nào trong dự án hiện tại.", parse_mode=ParseMode.HTML)
            return

        if contract.credit_status == CreditStatus.CANCELLED.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã bị hủy từ trước.", parse_mode=ParseMode.HTML)
            return

        text, reply_markup = _cancel_contract_confirm(contract)
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in cancel_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cc_confirm_(.*)$"))
@require_group_role("main")
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
@require_group_role("main")
async def cancel_contract_exit_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()


# --- Credit: List Contracts ---
@bot.on_message(filters.command(["credit_list_contract", "credit_danh_sach_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_list_contract|credit_danh_sach_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(auto_delete_cmd=True)
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

        # Tìm các nhóm member có parent_id trỏ về nhóm main hiện tại
        main_chat_id = current_group.chat_id
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.parent_id == main_chat_id,
            TelegramProjectMember.role == "member"
        ).all()

        # Nhóm main chưa được gán parent_id cho các nhóm member -> lấy theo dự án
        if not valid_members:
            valid_members = db.query(TelegramProjectMember).filter(
                TelegramProjectMember.project_id == current_group.project_id,
                TelegramProjectMember.role == "member"
            ).all()

        # Đối chiếu khách hàng theo chat_id nhóm member (tên nhóm hay bị lệch hoa/thường, sai chính tả)
        member_chat_ids = {str(m.chat_id) for m in valid_members if m.chat_id}
        customers = []
        if member_chat_ids:
            customers = db.query(CreditCustomer).filter(
                CreditCustomer.chat_id.in_(member_chat_ids)
            ).all()

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
            f"{'━' * 15}",
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
                f"{'━' * 15}",
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
@command_timeout(auto_delete_cmd=True)
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
@command_timeout(auto_delete_cmd=True)
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
    await callback_query.message.delete()

# --- Extend Contract ---
def _build_extend_contract_form(contract):
    """Form gia hạn hợp đồng tín dụng."""
    customer = contract.customer
    status_label = _CMV_STATUS_LABELS.get(contract.credit_status, "N/A")
    due_date_str = contract.due_date.strftime('%d/%m/%Y') if contract.due_date else ""

    return f"""<b>FORM GIA HẠN HỢP ĐỒNG TÍN DỤNG</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/credit_extend_contract {contract.contract_id}
Mã Hợp Đồng: {contract.contract_id or ""}
Tên Khách Hàng: {customer.customer_name if customer else ""}
Trạng Thái: {status_label}
Ngày Đáo Hạn Hiện Tại: {due_date_str}
Số Tháng Gia Hạn: 1
</pre>

<i>Số Tháng Gia Hạn là số nguyên từ 1 đến 60.
Nếu hợp đồng đang Nợ Xấu (Blacklist), bot sẽ tự động đưa về Đang vay sau khi gia hạn.</i>"""


def _cgh_customer_list_keyboard(customers, page):
    """Bàn phím chọn khách hàng để gia hạn hợp đồng: tối đa 10 nút/trang, có Trước/Sau và Hủy."""
    PAGE_SIZE = 10
    total = len(customers)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_customers = customers[start:min(start + PAGE_SIZE, total)]

    buttons = [
        [InlineKeyboardButton(
            f"{c.customer_id} - {c.customer_name}",
            callback_data=f"cgh_c|{_sid(c.id)}|0"
        )]
        for c in page_customers
    ]

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"cgh_cp|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"cgh_cp|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("Hủy", callback_data="ec_cancel")])
    return InlineKeyboardMarkup(buttons)


def _cgh_contract_list_keyboard(contracts, page, customer_hex):
    """Bàn phím chọn hợp đồng để gia hạn (liệt kê mọi trạng thái)."""
    PAGE_SIZE = 10
    total = len(contracts)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_contracts = contracts[start:min(start + PAGE_SIZE, total)]

    buttons = []
    for c in page_contracts:
        status_label = _CMV_STATUS_LABELS.get(c.credit_status, "N/A")
        buttons.append([InlineKeyboardButton(
            f"{c.contract_id} ({status_label})",
            callback_data=f"cgh_s|{_sid(c.id)}"
        )])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"cgh_c|{customer_hex}|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"cgh_c|{customer_hex}|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton("Quay lại", callback_data="cgh_cp|0"),
        InlineKeyboardButton("Hủy", callback_data="ec_cancel")
    ])
    return InlineKeyboardMarkup(buttons)


@bot.on_callback_query(filters.regex(r"^cgh_cp\|(\d+)$"))
@require_group_role("main")
async def cgh_customer_page_callback(client, callback_query: CallbackQuery):
    """Phân trang / quay lại danh sách khách hàng khi gia hạn hợp đồng."""
    page = int(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
        if not customers:
            await callback_query.message.edit_text("ℹ️ Chưa có khách hàng nào trong hệ thống.")
            return

        await callback_query.message.edit_text(
            "<b>GIA HẠN HỢP ĐỒNG TÍN DỤNG</b>\n\nChọn khách hàng:",
            reply_markup=_cgh_customer_list_keyboard(customers, page),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cgh_customer_page_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cgh_c\|([a-f0-9]{32})\|(\d+)$"))
@require_group_role("main")
async def cgh_contract_list_callback(client, callback_query: CallbackQuery):
    """Chọn khách hàng -> danh sách toàn bộ hợp đồng (mọi trạng thái)."""
    customer_hex = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == _uid(customer_hex)).first()
        if not customer:
            await callback_query.answer("⚠️ Không tìm thấy khách hàng.", show_alert=True)
            return

        contracts = db.query(Credit).filter(
            Credit.customer_id == customer.id
        ).order_by(Credit.contract_id).all()
        if not contracts:
            await callback_query.answer("ℹ️ Khách hàng chưa có hợp đồng nào.", show_alert=True)
            return

        await callback_query.message.edit_text(
            f"<b>DANH SÁCH HỢP ĐỒNG</b>\n"
            f"Khách hàng: <b>{customer.customer_name}</b> ({customer.customer_id})\n\n"
            f"Chọn hợp đồng cần gia hạn:",
            reply_markup=_cgh_contract_list_keyboard(contracts, page, customer_hex),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cgh_contract_list_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cgh_s\|([a-f0-9]{32})$"))
@require_group_role("main")
async def cgh_select_contract_callback(client, callback_query: CallbackQuery):
    """Chọn hợp đồng -> hiển thị form điền thông tin gia hạn."""
    db = SessionLocal()
    try:
        contract = db.query(Credit).filter(Credit.id == _uid(callback_query.matches[0].group(1))).first()
        if not contract:
            await callback_query.answer("⚠️ Không tìm thấy hợp đồng.", show_alert=True)
            return

        if contract.credit_status in [CreditStatus.PAID.value, CreditStatus.CANCELLED.value]:
            status_label = _CMV_STATUS_LABELS.get(contract.credit_status, contract.credit_status)
            await callback_query.answer(
                f"Hợp đồng {contract.contract_id} đang ở trạng thái {status_label}, không thể gia hạn.",
                show_alert=True
            )
            return

        if not contract.due_date:
            await callback_query.answer(
                f"Hợp đồng {contract.contract_id} chưa có Ngày Đáo Hạn nên không thể gia hạn.",
                show_alert=True
            )
            return

        form_msg = await callback_query.message.reply_text(
            _build_extend_contract_form(contract), parse_mode=ParseMode.HTML
        )
        form_tracker.track(callback_query.message.chat.id, "credit_extend_contract", contract.contract_id, form_msg.id)
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cgh_select_contract_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_message(filters.command(["credit_extend_contract", "credit_gia_han_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_extend_contract|credit_gia_han_hop_dong)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(auto_delete_cmd=True)
async def extend_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_extend_contract", "credit_gia_han_hop_dong"])
    if args is None: return

    lines = message.text.strip().split("\n")
    is_form = len(lines) > 1

    db = SessionLocal()
    try:
        # Không kèm Mã Hợp Đồng -> hiển thị danh sách khách hàng để chọn
        if not is_form and len(args) < 2:
            customers = db.query(CreditCustomer).order_by(CreditCustomer.customer_id).all()
            if not customers:
                await message.reply_text("ℹ️ Chưa có khách hàng nào trong hệ thống.")
                return

            await message.reply_text(
                "<b>GIA HẠN HỢP ĐỒNG TÍN DỤNG</b>\n\nChọn khách hàng:",
                reply_markup=_cgh_customer_list_keyboard(customers, 0),
                parse_mode=ParseMode.HTML
            )
            return

        months_to_add = 1
        if is_form:
            # Người dùng gửi lại Form gia hạn
            data = {}
            for line in lines[1:]:
                if ":" in line:
                    key, val = line.split(":", 1)
                    data[key.strip()] = val.strip()

            contract_code = (args[1].strip() if len(args) >= 2 else data.get("Mã Hợp Đồng", "")).strip()
            months_str = data.get("Số Tháng Gia Hạn", "1").strip()
        else:
            contract_code = args[1].strip()
            months_str = args[2].strip() if len(args) >= 3 else "1"

        if not contract_code:
            await message.reply_text("⚠️ Vui lòng cung cấp <b>Mã Hợp Đồng</b>.", parse_mode=ParseMode.HTML)
            return

        try:
            months_to_add = int(months_str)
            if months_to_add <= 0 or months_to_add > 60:
                raise ValueError()
        except ValueError:
            await message.reply_text("⚠️ Số tháng gia hạn không hợp lệ (phải là số nguyên từ 1 đến 60).", parse_mode=ParseMode.HTML)
            return

        from app.models.credit import Credit, CreditStatus
        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()

        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng nào có mã <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return
            
        if contract.credit_status in [CreditStatus.PAID.value, CreditStatus.CANCELLED.value]:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đang ở trạng thái <b>{contract.credit_status}</b>, không thể gia hạn.", parse_mode=ParseMode.HTML)
            return

        if not contract.due_date:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> chưa có Ngày Đáo Hạn nên không thể gia hạn.", parse_mode=ParseMode.HTML)
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

        # Xóa Form mẫu sau khi người dùng đã gửi lại thông tin
        form_msg_id = form_tracker.pop(message.chat.id, "credit_extend_contract", contract.contract_id)
        if form_msg_id:
            try:
                await client.delete_messages(chat_id=message.chat.id, message_ids=form_msg_id)
            except Exception as del_err:
                LogError(f"Failed to delete credit extend contract form: {del_err}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in extend_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình xử lý.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ec_confirm_([^_]+)_(\d+)$"))
@require_group_role("main")
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

        if contract.credit_status in [CreditStatus.PAID.value, CreditStatus.CANCELLED.value]:
            await callback_query.answer(
                f"Hợp đồng {contract.contract_id} đang ở trạng thái {contract.credit_status}, không thể gia hạn.",
                show_alert=True
            )
            return

        if not contract.due_date:
            await callback_query.answer(
                f"Hợp đồng {contract.contract_id} chưa có Ngày Đáo Hạn nên không thể gia hạn.",
                show_alert=True
            )
            return

        def add_months_to_date(source_date, months):
            import calendar
            month = source_date.month - 1 + months
            year = source_date.year + month // 12
            month = month % 12 + 1
            day = min(source_date.day, calendar.monthrange(year, month)[1])
            return datetime.date(year, month, day)

        old_due_date = contract.due_date
        new_due_date = add_months_to_date(old_due_date, months_to_add)
        old_due_date_str = old_due_date.strftime('%d/%m/%Y')
        new_due_date_str = new_due_date.strftime('%d/%m/%Y')

        new_values = {"due_date": new_due_date}

        # Reset bad debt back to active
        if contract.credit_status == CreditStatus.BAD_DEBT.value:
            new_values["credit_status"] = CreditStatus.ACTIVE.value
            if contract.notes and "[BLACKLIST]" in contract.notes:
                new_values["notes"] = contract.notes.replace("[BLACKLIST]", "").strip()

        # Chỉ ghi khi due_date vẫn đúng giá trị vừa đọc -> bấm 2 lần / 2 admin
        # bấm cùng lúc chỉ gia hạn được 1 lần, không cộng dồn.
        updated = db.query(Credit).filter(
            Credit.id == contract_uuid,
            Credit.due_date == old_due_date
        ).update(new_values, synchronize_session=False)

        if not updated:
            db.rollback()
            await callback_query.answer(
                f"Hợp đồng {contract.contract_id} vừa được gia hạn bởi thao tác khác. Vui lòng kiểm tra lại.",
                show_alert=True
            )
            return


        customer = contract.customer
        
        # Cross group announcement to member group
        member_chat_id = None
        if customer:
            member_chat_id = str(customer.chat_id or "").strip() or None
            if not member_chat_id and customer.group_name:
                from app.crud.credit import match_member_link
                customer_links = db.query(TelegramProjectMember).filter(
                    TelegramProjectMember.role == "member"
                ).all()
                matched_link = match_member_link(customer, customer_links)
                if matched_link:
                    member_chat_id = matched_link.chat_id


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
@require_group_role("main")
async def extend_contract_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()


# --- Payment Confirmed ---
@bot.on_message(filters.command(["credit_payment_confirmed", "credit_xac_nhan_thanh_toan"]) | filters.regex(r"^@\w+\s+/(credit_payment_confirmed|credit_xac_nhan_thanh_toan)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@command_timeout(auto_delete_cmd=True)
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

        # Trừ nợ lãi bằng phép tính ngay trên DB (không đọc-sửa-ghi trong Python)
        # để 2 lần thanh toán đồng thời không ghi đè lẫn nhau. Chặn sàn ở 0 khi trả dư.
        from sqlalchemy import func as _sa_func
        db.query(Credit).filter(Credit.id == contract.id).update(
            {"interest_debt": _sa_func.greatest(
                _sa_func.coalesce(Credit.interest_debt, 0.0) - paid_amount, 0.0
            )},
            synchronize_session=False
        )

        db.commit()
        db.refresh(contract)

        def fmt_num(val):
            if val is None: return 0
            return int(val) if val == int(val) else val

        remaining = fmt_num(contract.interest_debt)
        date_str = now.strftime('%d/%m/%Y')
        amount_fmt = fmt_num(paid_amount)
        safe_reply_text = html.escape(replied_text)
        
        reply_msg = (
            f"<b>{date_str}</b>\n"
            f"Đã cập nhật thanh toán nợ lãi: <b>{amount_fmt:,}</b> vào hợp đồng\n"
            f"Tổng nợ lãi còn lại: <b>{remaining:,}</b>"
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
_CASHFLOW_PAGE_SIZE = 10


def _cashflow_data(db, chat_id):
    """Số liệu dòng tiền của dự án, dùng chung cho báo cáo tổng và chi tiết."""
    from app.models.telegram import TelegramProjectMember
    from app.models.credit import CreditCustomer, Credit, CreditStatus, CreditInterest

    current_project_member = db.query(TelegramProjectMember).filter(
        TelegramProjectMember.chat_id == chat_id
    ).first()
    if not current_project_member:
        return None

    valid_members = db.query(TelegramProjectMember).filter(
        TelegramProjectMember.project_id == current_project_member.project_id,
        TelegramProjectMember.role == "member",
        TelegramProjectMember.parent_id == chat_id
    ).all()

    # Nhóm main chưa được gán parent_id cho các nhóm member -> lấy theo dự án
    if not valid_members:
        valid_members = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == current_project_member.project_id,
            TelegramProjectMember.role == "member"
        ).all()

    # Đối chiếu theo chat_id nhóm member (tên nhóm hay bị lệch hoa/thường, sai chính tả)
    member_chat_ids = {str(m.chat_id) for m in valid_members if m.chat_id}
    customers = []
    if member_chat_ids:
        customers = db.query(CreditCustomer).filter(
            CreditCustomer.chat_id.in_(member_chat_ids)
        ).order_by(CreditCustomer.customer_id).all()
    if not customers:
        return None

    total_contracts = 0
    total_principal = 0
    total_interest = 0
    total_paid = 0
    rows = []

    for customer in customers:
        all_cust_credits = db.query(Credit).filter(Credit.customer_id == customer.id).all()
        if not all_cust_credits:
            continue

        active_credits = [c for c in all_cust_credits
                          if c.credit_status in [CreditStatus.ACTIVE.value, CreditStatus.BAD_DEBT.value]]

        cust_contracts = len(active_credits)
        cust_principal = sum([(c.remaining_principal or 0) for c in active_credits])
        cust_interest = sum([(c.interest_debt or 0) for c in active_credits])

        interests = db.query(CreditInterest).filter(
            CreditInterest.contract_id.in_([c.contract_id for c in all_cust_credits])
        ).all()
        cust_paid = sum([(i.interest_amount or 0) for i in interests
                         if i.payment_time or i.interest_payment_date])

        if cust_contracts == 0 and not cust_paid:
            continue

        total_contracts += cust_contracts
        total_principal += cust_principal
        total_interest += cust_interest
        total_paid += cust_paid

        rows.append({
            "customer_id": customer.customer_id,
            "customer_name": customer.customer_name,
            "contracts": cust_contracts,
            "principal": cust_principal,
            "interest": cust_interest,
            "paid": cust_paid,
        })

    rows.sort(key=lambda r: (-r["principal"], -r["paid"], r["customer_id"] or ""))

    return {
        "total_contracts": total_contracts,
        "total_principal": total_principal,
        "total_interest": total_interest,
        "total_paid": total_paid,
        "rows": rows,
    }


def _cashflow_summary_text(data):
    return "\n".join([
        f"<b>BÁO CÁO DÒNG TIỀN DỰ ÁN</b>",
        f"{'━' * 15}",
        f"<b>Tổng Hợp Đồng Đang Vay:</b> {data['total_contracts']}",
        f"<b>Tổng Nợ Gốc:</b> {fmt_vn(data['total_principal'])}",
        f"<b>Tổng Nợ Lãi:</b> {fmt_vn(data['total_interest'])}",
        f"<b>Tổng Lãi Đã Thu:</b> {fmt_vn(data['total_paid'])}",
        f"{'━' * 15}",
    ])


def _cashflow_keyboard():
    """Nút Chi tiết / Hủy cho báo cáo dòng tiền."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Chi tiết", callback_data="cfd|0"),
        InlineKeyboardButton("Hủy", callback_data="cf_x")
    ]])


def _cashflow_detail_keyboard(page, total_pages):
    """Bàn phím chi tiết dòng tiền: phân trang tối đa 10 khách hàng, kèm Ẩn chi tiết và Hủy."""
    total_pages = max(1, total_pages)
    page = max(0, min(page, total_pages - 1))
    buttons = []

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"cfd|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"cfd|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton("Ẩn chi tiết", callback_data="cfs"),
        InlineKeyboardButton("Hủy", callback_data="cf_x")
    ])
    return InlineKeyboardMarkup(buttons)


@bot.on_message(filters.command(["credit_cashflow_report", "credit_bao_cao_dong_tien"]) | filters.regex(r"^@\w+\s+/(credit_cashflow_report|credit_bao_cao_dong_tien)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
@require_project_name("Credit")
@command_timeout(auto_delete_cmd=True)
async def report_cashflow_handler(client, message: Message) -> None:
    db = SessionLocal()
    try:
        data = _cashflow_data(db, str(message.chat.id))
        if data is None:
            await message.reply_text("⚠️ Không có khách hàng nào trong dự án này.", parse_mode=ParseMode.HTML)
            return
        if not data["rows"] and data["total_contracts"] == 0 and not data["total_paid"]:
            await message.reply_text("ℹ️ Không có dữ liệu hợp đồng/dòng tiền nào trong dự án.", parse_mode=ParseMode.HTML)
            return

        await message.reply_text(
            _cashflow_summary_text(data),
            reply_markup=_cashflow_keyboard(),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        LogError(f"Error in report_cashflow_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình truy xuất báo cáo.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cfd\|(\d+)$"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def cashflow_detail_callback(client, callback_query: CallbackQuery):
    """Nút 'Chi tiết': dòng tiền của từng khách hàng, phân trang tối đa 10 khách hàng/trang."""
    page = int(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        data = _cashflow_data(db, str(callback_query.message.chat.id))
        if data is None or not data["rows"]:
            await callback_query.answer("Không có khách hàng nào để hiển thị chi tiết.", show_alert=True)
            return

        rows = data["rows"]
        total = len(rows)
        total_pages = max(1, (total + _CASHFLOW_PAGE_SIZE - 1) // _CASHFLOW_PAGE_SIZE)
        page = max(0, min(page, total_pages - 1))
        start = page * _CASHFLOW_PAGE_SIZE

        lines = [
            f"<b>CHI TIẾT DÒNG TIỀN THEO KHÁCH HÀNG</b>",
            f"{'━' * 15}",
            f"Tổng: <b>{total}</b> khách hàng | Trang <b>{page + 1}/{total_pages}</b>",
            f"Tổng Lãi Đã Thu: <b>{fmt_vn(data['total_paid'])}</b>",
            f"{'━' * 15}",
        ]
        for idx, r in enumerate(rows[start:start + _CASHFLOW_PAGE_SIZE], start + 1):
            paid_str = f"<b>{fmt_vn(r['paid'])}</b>" if r["paid"] else "Chưa đóng lãi"
            lines.append(
                f"\n{idx}. <b>{r['customer_name']}</b> (Mã: {r['customer_id']})\n"
                f"   Hợp đồng: {r['contracts']} | Nợ Gốc: <b>{fmt_vn(r['principal'])}</b> | Nợ Lãi: <b>{fmt_vn(r['interest'])}</b>\n"
                f"   Tổng thanh toán: {paid_str}"
            )

        await callback_query.message.edit_text(
            "\n".join(lines),
            reply_markup=_cashflow_detail_keyboard(page, total_pages),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()

    except Exception as e:
        LogError(f"Error in cashflow_detail_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cfs$"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def cashflow_summary_callback(client, callback_query: CallbackQuery):
    """Nút 'Ẩn chi tiết': quay về báo cáo dòng tiền tổng."""
    db = SessionLocal()
    try:
        data = _cashflow_data(db, str(callback_query.message.chat.id))
        if data is None:
            await callback_query.answer("Không có khách hàng nào trong dự án này.", show_alert=True)
            return

        await callback_query.message.edit_text(
            _cashflow_summary_text(data),
            reply_markup=_cashflow_keyboard(),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()

    except Exception as e:
        LogError(f"Error in cashflow_summary_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cf_x$"))
@require_group_role("main")
async def cashflow_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()

# --- Revenue Date Selector ---
def _revenue_data(db, project_id, start_date, end_date):
    """Số liệu doanh thu lãi của dự án trong khoảng thời gian, dùng chung cho báo cáo tổng và chi tiết."""
    from app.models.telegram import TelegramProjectMember
    from app.models.credit import CreditCustomer, Credit, CreditStatus, CreditInterest

    valid_members = db.query(TelegramProjectMember).filter(
        TelegramProjectMember.project_id == project_id,
        TelegramProjectMember.role == "member"
    ).all()

    # Đối chiếu theo chat_id nhóm member (tên nhóm hay bị lệch hoa/thường, sai chính tả)
    member_chat_ids = {str(m.chat_id) for m in valid_members if m.chat_id}
    customers = []
    if member_chat_ids:
        customers = db.query(CreditCustomer).filter(
            CreditCustomer.chat_id.in_(member_chat_ids)
        ).all()
    if not customers:
        return None

    customer_map = {c.id: c for c in customers}
    all_credits = db.query(Credit).filter(Credit.customer_id.in_(list(customer_map))).all()
    contract_ids = [c.contract_id for c in all_credits]

    interests = db.query(CreditInterest).filter(
        CreditInterest.contract_id.in_(contract_ids)
    ).all() if contract_ids else []

    # Lãi đã thu trong kỳ, gom theo từng hợp đồng
    collected_by_contract = {}
    total_collected = 0
    for interest in interests:
        record_date = interest.payment_time.date() if interest.payment_time else interest.interest_payment_date
        if not record_date or not (start_date <= record_date <= end_date):
            continue
        amount = interest.interest_amount or 0
        collected_by_contract[interest.contract_id] = collected_by_contract.get(interest.contract_id, 0) + amount
        total_collected += amount

    active_credits = [c for c in all_credits if c.credit_status in [CreditStatus.ACTIVE.value, CreditStatus.BAD_DEBT.value]]
    active_ids = {c.id for c in active_credits}

    rows = []
    for c in all_credits:
        collected = collected_by_contract.get(c.contract_id, 0)
        principal = (c.remaining_principal or 0) if c.id in active_ids else 0
        interest_debt = (c.interest_debt or 0) if c.id in active_ids else 0
        if not collected and not principal and not interest_debt:
            continue
        cust = customer_map.get(c.customer_id)
        rows.append({
            "contract_id": c.contract_id,
            "customer_name": cust.customer_name if cust else "N/A",
            "collected": collected,
            "principal": principal,
            "interest_debt": interest_debt,
        })
    rows.sort(key=lambda r: (-r["collected"], -r["principal"], r["contract_id"] or ""))

    return {
        "total_collected": total_collected,
        "total_principal": sum([c.remaining_principal or 0 for c in active_credits]),
        "total_interest": sum([c.interest_debt or 0 for c in active_credits]),
        "rows": rows,
    }


_REVENUE_PAGE_SIZE = 10


def _rev_dates(start_date, end_date):
    return start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')


def _revenue_keyboard(start_date, end_date):
    """Nút Chi tiết / Hủy cho báo cáo doanh thu (mang theo khoảng thời gian đã lọc)."""
    s, e = _rev_dates(start_date, end_date)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Chi tiết", callback_data=f"revd|{s}|{e}|0"),
        InlineKeyboardButton("Hủy", callback_data="rev_cancel")
    ]])


def _revenue_detail_keyboard(start_date, end_date, page, total_pages):
    """Bàn phím chi tiết doanh thu: phân trang tối đa 10 hợp đồng, kèm Ẩn chi tiết và Hủy."""
    s, e = _rev_dates(start_date, end_date)
    total_pages = max(1, total_pages)
    page = max(0, min(page, total_pages - 1))
    buttons = []

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"revd|{s}|{e}|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="ck_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"revd|{s}|{e}|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton("Ẩn chi tiết", callback_data=f"revs|{s}|{e}"),
        InlineKeyboardButton("Hủy", callback_data="rev_cancel")
    ])
    return InlineKeyboardMarkup(buttons)


def _revenue_summary_text(data, start_date, end_date):
    return "\n".join([
        f"<b>BÁO CÁO DOANH THU (Lãi đã thu)</b>",
        f"<i>(Thời gian lọc: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})</i>",
        f"{'━' * 15}",
        f"<b>Tổng Lãi Đã Thu:</b> <b>{fmt_vn(data['total_collected'])}</b>",
        f"<b>Tổng Nợ Gốc:</b> {fmt_vn(data['total_principal'])}",
        f"<b>Tổng Nợ Lãi Chưa Trả:</b> {fmt_vn(data['total_interest'])}",
    ])


async def generate_revenue_report(client, message, project_id, start_date, end_date):
    db = SessionLocal()
    try:
        data = _revenue_data(db, project_id, start_date, end_date)
        if data is None:
            await message.reply_text("⚠️ Không có khách hàng nào trong dự án.", parse_mode=ParseMode.HTML)
            return

        await message.reply_text(
            _revenue_summary_text(data, start_date, end_date),
            reply_markup=_revenue_keyboard(start_date, end_date),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        LogError(f"Error in generate_revenue_report: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình tính toán.")
    finally:
        db.close()


async def _revenue_project_id(callback_query, db):
    """Dự án của nhóm đang thao tác, None nếu nhóm chưa đồng bộ."""
    from app.models.telegram import TelegramProjectMember
    member = db.query(TelegramProjectMember).filter(
        TelegramProjectMember.chat_id == str(callback_query.message.chat.id)
    ).first()
    if not member:
        await callback_query.answer("⚠️ Nhóm này chưa được đồng bộ vào dự án nào.", show_alert=True)
        return None
    return member.project_id


@bot.on_callback_query(filters.regex(r"^revd\|(\d{8})\|(\d{8})\|(\d+)$"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def revenue_detail_callback(client, callback_query: CallbackQuery):
    """Nút 'Chi tiết': số tiền của từng hợp đồng, phân trang tối đa 10 hợp đồng/trang."""
    import datetime
    start_date = datetime.datetime.strptime(callback_query.matches[0].group(1), "%Y%m%d").date()
    end_date = datetime.datetime.strptime(callback_query.matches[0].group(2), "%Y%m%d").date()
    page = int(callback_query.matches[0].group(3))

    db = SessionLocal()
    try:
        project_id = await _revenue_project_id(callback_query, db)
        if project_id is None:
            return

        data = _revenue_data(db, project_id, start_date, end_date)
        if data is None or not data["rows"]:
            await callback_query.answer("Không có hợp đồng nào để hiển thị chi tiết.", show_alert=True)
            return

        rows = data["rows"]
        total = len(rows)
        total_pages = max(1, (total + _REVENUE_PAGE_SIZE - 1) // _REVENUE_PAGE_SIZE)
        page = max(0, min(page, total_pages - 1))
        start = page * _REVENUE_PAGE_SIZE

        lines = [
            f"<b>CHI TIẾT DOANH THU THEO HỢP ĐỒNG</b>",
            f"<i>(Thời gian lọc: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})</i>",
            f"{'━' * 15}",
            f"Tổng: <b>{total}</b> hợp đồng | Trang <b>{page + 1}/{total_pages}</b>",
            f"Tổng Lãi Đã Thu: <b>{fmt_vn(data['total_collected'])}</b>",
            f"{'━' * 15}",
        ]
        for idx, r in enumerate(rows[start:start + _REVENUE_PAGE_SIZE], start + 1):
            lines.append(
                f"{idx}. <code>{r['contract_id']}</code> - {r['customer_name']}\n"
                f"   Lãi đã thu: <b>{fmt_vn(r['collected'])}</b>\n"
                f"   Nợ gốc: {fmt_vn(r['principal'])}\n"
                f"   Nợ lãi chưa trả: {fmt_vn(r['interest_debt'])}"
            )

        await callback_query.message.edit_text(
            "\n".join(lines),
            reply_markup=_revenue_detail_keyboard(start_date, end_date, page, total_pages),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()

    except Exception as e:
        LogError(f"Error in revenue_detail_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^revs\|(\d{8})\|(\d{8})$"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def revenue_summary_callback(client, callback_query: CallbackQuery):
    """Nút 'Ẩn chi tiết': quay về báo cáo doanh thu tổng."""
    import datetime
    start_date = datetime.datetime.strptime(callback_query.matches[0].group(1), "%Y%m%d").date()
    end_date = datetime.datetime.strptime(callback_query.matches[0].group(2), "%Y%m%d").date()

    db = SessionLocal()
    try:
        project_id = await _revenue_project_id(callback_query, db)
        if project_id is None:
            return

        data = _revenue_data(db, project_id, start_date, end_date)
        if data is None:
            await callback_query.answer("Không có khách hàng nào trong dự án.", show_alert=True)
            return

        await callback_query.message.edit_text(
            _revenue_summary_text(data, start_date, end_date),
            reply_markup=_revenue_keyboard(start_date, end_date),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()

    except Exception as e:
        LogError(f"Error in revenue_summary_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_message(filters.command(["credit_revenue", "credit_doanh_thu"]) | filters.regex(r"^@\w+\s+/(credit_revenue|credit_doanh_thu)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(auto_delete_cmd=True)
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

# --- Remind Next Period ---
@bot.on_message(filters.command(["remind_next_period"]) | filters.regex(r"^@\w+\s+/remind_next_period\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("main")
@command_timeout(auto_delete_cmd=True)
async def remind_next_period_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["remind_next_period"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp mã hợp đồng. Lệnh ví dụ: <pre>/remind_next_period HD123</pre>", parse_mode=ParseMode.HTML)
        return

    contract_code = args[1]
    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditStatus
        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await message.reply_text(f"⚠️ Không tìm thấy hợp đồng <b>{contract_code}</b>.", parse_mode=ParseMode.HTML)
            return

        if contract.credit_status != CreditStatus.ACTIVE.value:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không ở trạng thái ACTIVE (Đang vay).", parse_mode=ParseMode.HTML)
            return
            
        if not contract.interest_start_date:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> không có ngày bắt đầu tính lãi.", parse_mode=ParseMode.HTML)
            return

        import datetime
        now = datetime.datetime.now()
        current_date = now.date()
        interest_day = contract.interest_start_date.day
        
        if current_date.day >= interest_day:
            due_year, due_month = current_date.year, current_date.month
        else:
            due_year, due_month = (current_date.year, current_date.month - 1) if current_date.month > 1 else (current_date.year - 1, 12)
            
        skip_tag = f"[SKIP_INTEREST: {due_month:02d}/{due_year}]"
        
        if contract.notes and skip_tag in contract.notes:
            await message.reply_text(f"⚠️ Hợp đồng <b>{contract_code}</b> đã được dời thông báo cho chu kỳ này trước đó rồi.", parse_mode=ParseMode.HTML)
            return
            
        # Append skip tag
        if contract.notes:
            contract.notes = f"{contract.notes}\n{skip_tag}"
        else:
            contract.notes = skip_tag
            
        db.commit()
        
        await message.reply_text(f"✅ Đã dời thông báo đóng lãi của hợp đồng <b>{contract_code}</b> sang chu kỳ sau.\n\n<i>Lãi của chu kỳ này đã được cộng vào tổng nợ lãi. Bot sẽ ngưng nhắc nhở và không đưa khách hàng vào Nợ Xấu (Blacklist) trong chu kỳ này.</i>", parse_mode=ParseMode.HTML)
        LogInfo(f"Remind next period applied to {contract_code} by {message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in remind_next_period_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình dời thông báo.")
    finally:
        db.close()


# ===================== CREDIT INTEREST NOTIFICATION CALLBACKS =====================

async def _check_admin_or_owner_credit(callback_query: CallbackQuery) -> bool:
    """Kiểm tra người dùng click callback có phải là OWNER hoặc ADMINISTRATOR không."""
    user_id = str(callback_query.from_user.id)
    username = callback_query.from_user.username
    chat_id = str(callback_query.message.chat.id)
    
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        member = None
        if username:
            member = db.query(TelegramProjectMember).filter(
                TelegramProjectMember.chat_id == chat_id,
                TelegramProjectMember.user_name == username
            ).first()
        if not member:
            member = db.query(TelegramProjectMember).filter(
                TelegramProjectMember.chat_id == chat_id,
                TelegramProjectMember.user_id == user_id
            ).first()
            
        if member and member.member_status in ["OWNER", "ADMINISTRATOR"]:
            return True
            
        # Fallback check across project members
        if not member:
            member = db.query(TelegramProjectMember).filter(
                TelegramProjectMember.user_id == user_id,
                TelegramProjectMember.member_status.in_(["OWNER", "ADMINISTRATOR"])
            ).first()
            if member:
                return True
                
        return False
    except Exception as e:
        LogError(f"Error checking admin/owner in credit: {e}", LogType.SYSTEM_STATUS)
        return False
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cnt_full_pay\|([^|]+)$"))
async def cnt_full_pay_callback(client, callback_query: CallbackQuery):
    """Nút 1: 'Đã nhận TT đủ' -> Ghi nhận thanh toán 100% nợ lãi hiện tại."""
    if not await _check_admin_or_owner_credit(callback_query):
        await callback_query.answer("⚠️ Thao tác này chỉ dành cho Admin và Owner!", show_alert=True)
        return
        
    contract_code = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditStatus, CreditInterest
        
        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await callback_query.answer(f"❌ Không tìm thấy hợp đồng {contract_code}.", show_alert=True)
            return
            
        paid_amount = contract.interest_debt or 0.0
        if paid_amount <= 0:
            await callback_query.answer("⚠️ Hợp đồng này hiện không có nợ lãi cần thanh toán.", show_alert=True)
            return

        # Chỉ về 0 khi nợ lãi vẫn đúng bằng số vừa đọc -> bấm 2 lần / 2 admin bấm
        # cùng lúc chỉ ghi nhận được 1 lần, không tạo 2 bản ghi thu lãi trùng.
        cleared = db.query(Credit).filter(
            Credit.id == contract.id,
            Credit.interest_debt == paid_amount
        ).update({"interest_debt": 0.0}, synchronize_session=False)

        if not cleared:
            db.rollback()
            await callback_query.answer(
                "Nợ lãi của hợp đồng vừa được cập nhật bởi thao tác khác. Vui lòng kiểm tra lại.",
                show_alert=True
            )
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
            db.query(Credit).filter(Credit.id == contract.id).update(
                {
                    "credit_status": CreditStatus.ACTIVE.value,
                    "notes": (contract.notes or "").replace("[BLACKLIST]", "").strip() or None,
                },
                synchronize_session=False
            )

        db.commit()

        amount_fmt = fmt_num(paid_amount)
        date_str = now.strftime('%d/%m/%Y %H:%M')
        
        reply_msg = (
            f"✅ <b>XÁC NHẬN ĐÃ NHẬN THANH TOÁN ĐỦ TIỀN LÃI</b>\n\n"
            f"- Mã hợp đồng: <code>{contract_code}</code>\n"
            f"- Số tiền đã thu: <b>{amount_fmt} VNĐ</b>\n"
            f"- Nợ lãi còn lại: <b>0 VNĐ</b>\n"
            f"- Thời gian: <b>{date_str}</b>"
        )
        await callback_query.message.edit_text(reply_msg, parse_mode=ParseMode.HTML)
        LogInfo(f"[CntFullPay] Contract {contract_code} paid full interest {amount_fmt} by {callback_query.from_user.id}", LogType.SYSTEM_STATUS)
    except Exception as e:
        db.rollback()
        LogError(f"Error in cnt_full_pay_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi cập nhật thanh toán.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cnt_pay\|([^|]+)$"))
async def cnt_pay_callback(client, callback_query: CallbackQuery):
    """Nút 2: 'Đã nhận TT' -> Hướng dẫn & mẫu lệnh /credit_payment_confirmed."""
    if not await _check_admin_or_owner_credit(callback_query):
        await callback_query.answer("⚠️ Thao tác này chỉ dành cho Admin và Owner!", show_alert=True)
        return
        
    contract_code = callback_query.matches[0].group(1)
    
    text = (
        f"💡 <b>XÁC NHẬN THANH TOÁN TIỀN LÃI</b>\n\n"
        f"Mã hợp đồng: <code>{contract_code}</code>\n\n"
        f"Vui lòng sao chép và nhập số tiền thanh toán:\n"
        f"<pre>/credit_payment_confirmed [Số_Tiền_Thanh_Toán]</pre>\n"
        f"<i>(Ví dụ: <code>/credit_payment_confirmed 5000000</code>)</i>"
    )
    await callback_query.message.reply_text(text, parse_mode=ParseMode.HTML)
    await callback_query.answer()


@bot.on_callback_query(filters.regex(r"^cnt_remind\|([^|]+)$"))
async def cnt_remind_callback(client, callback_query: CallbackQuery):
    """Nút 3: 'Lưu sổ' -> Thực hiện dời thông báo lãi sang chu kỳ sau (/remind_next_period)."""
    if not await _check_admin_or_owner_credit(callback_query):
        await callback_query.answer("⚠️ Thao tác này chỉ dành cho Admin và Owner!", show_alert=True)
        return
        
    contract_code = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditStatus
        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await callback_query.answer(f"❌ Không tìm thấy hợp đồng {contract_code}.", show_alert=True)
            return
            
        if contract.credit_status != CreditStatus.ACTIVE.value:
            await callback_query.answer(f"⚠️ Hợp đồng {contract_code} không ở trạng thái ACTIVE.", show_alert=True)
            return
            
        if not contract.interest_start_date:
            await callback_query.answer(f"⚠️ Hợp đồng {contract_code} không có ngày bắt đầu tính lãi.", show_alert=True)
            return
            
        now = datetime.datetime.now()
        current_date = now.date()
        interest_day = contract.interest_start_date.day
        
        if current_date.day >= interest_day:
            due_year, due_month = current_date.year, current_date.month
        else:
            due_year, due_month = (current_date.year, current_date.month - 1) if current_date.month > 1 else (current_date.year - 1, 12)
            
        skip_tag = f"[SKIP_INTEREST: {due_month:02d}/{due_year}]"
        
        if contract.notes and skip_tag in contract.notes:
            await callback_query.answer(f"⚠️ Hợp đồng {contract_code} đã được dời thông báo cho chu kỳ này trước đó rồi.", show_alert=True)
            return
            
        if contract.notes:
            contract.notes = f"{contract.notes}\n{skip_tag}"
        else:
            contract.notes = skip_tag
            
        db.commit()
        
        msg_text = (
            f"✅ <b>ĐÃ LƯU SỔ / DỜI THÔNG BÁO TIỀN LÃI</b>\n\n"
            f"- Mã hợp đồng: <code>{contract_code}</code>\n\n"
            f"<i>Lãi của chu kỳ này đã được cộng vào tổng nợ lãi. Bot sẽ tạm ngưng nhắc nhở và không đưa khách hàng vào Nợ Xấu trong chu kỳ này.</i>"
        )
        await callback_query.message.edit_text(msg_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[CntRemind] Remind next period applied to {contract_code} by {callback_query.from_user.id}", LogType.SYSTEM_STATUS)
    except Exception as e:
        db.rollback()
        LogError(f"Error in cnt_remind_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi dời thông báo.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cnt_bad\|([^|]+)$"))
async def cnt_bad_callback(client, callback_query: CallbackQuery):
    """Nút 4: 'Nợ Xấu' -> Chuyển hợp đồng sang Nợ Xấu (BAD_DEBT)."""
    if not await _check_admin_or_owner_credit(callback_query):
        await callback_query.answer("⚠️ Thao tác này chỉ dành cho Admin và Owner!", show_alert=True)
        return
        
    contract_code = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        from app.models.credit import Credit, CreditStatus
        contract = db.query(Credit).filter(Credit.contract_id == contract_code).first()
        if not contract:
            await callback_query.answer(f"❌ Không tìm thấy hợp đồng {contract_code}.", show_alert=True)
            return
            
        contract.credit_status = CreditStatus.BAD_DEBT.value
        if not contract.notes:
            contract.notes = "[BLACKLIST]"
        elif "[BLACKLIST]" not in contract.notes:
            contract.notes = f"{contract.notes}\n[BLACKLIST]"
            
        db.commit()
        
        msg_text = (
            f"⚠️ <b>ĐÃ CHUYỂN HỢP ĐỒNG SANG NỢ XẤU</b>\n\n"
            f"- Mã hợp đồng: <code>{contract_code}</code>\n"
            f"- Trạng thái mới: <b>BAD_DEBT (Nợ Xấu)</b>\n"
            f"- Ghi chú: <b>[BLACKLIST]</b>"
        )
        await callback_query.message.edit_text(msg_text, parse_mode=ParseMode.HTML)
        LogInfo(f"[CntBad] Contract {contract_code} set to BAD_DEBT by {callback_query.from_user.id}", LogType.SYSTEM_STATUS)
    except Exception as e:
        db.rollback()
        LogError(f"Error in cnt_bad_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi chuyển Nợ Xấu.", show_alert=True)
    finally:
        db.close()

# --- Member: Xem Thông Tin Khách Hàng / Hợp Đồng (không dùng icon) ---
_CMV_PAGE_SIZE = 10

_CMV_STATUS_LABELS = {
    CreditStatus.ACTIVE.value: "Đang vay",
    CreditStatus.PAID.value: "Tất toán",
    CreditStatus.BAD_DEBT.value: "Nợ xấu",
    CreditStatus.CANCELLED.value: "Đã hủy",
}


def _cmv_num(val):
    if val is None: return 0
    return int(val) if val == int(val) else val


def _cmv_date(dt):
    return dt.strftime('%d/%m/%Y') if dt else "N/A"


def _cmv_loan_label(loan_type):
    if loan_type and loan_type.lower().strip() in ["secured", "thế chấp", "the chap", "collateral"]:
        return "Thế chấp"
    return "Tín chấp"


def _cmv_customers(db, chat_id):
    """Danh sách khách hàng tín dụng gắn với nhóm member theo chat_id."""
    chat_id = str(chat_id)
    customers = db.query(CreditCustomer).filter(
        CreditCustomer.chat_id == chat_id
    ).order_by(CreditCustomer.customer_name).all()
    if customers:
        return customers

    # Bản ghi cũ chưa có chat_id: đối chiếu tạm theo Tên Nhóm đã đồng bộ
    member = db.query(TelegramProjectMember).filter(
        TelegramProjectMember.chat_id == chat_id
    ).first()
    if member and member.group_name:
        return db.query(CreditCustomer).filter(
            CreditCustomer.group_name == member.group_name
        ).order_by(CreditCustomer.customer_name).all()
    return []


def _cmv_owns(db, chat_id, customer):
    """Kiểm tra khách hàng có thuộc nhóm member đang thao tác hay không."""
    if not customer:
        return False
    return any(str(c.id) == str(customer.id) for c in _cmv_customers(db, chat_id))


def _cmv_customer_text(customer, contracts):
    active = [c for c in contracts if c.credit_status == CreditStatus.ACTIVE.value]
    total_remaining = sum([(c.remaining_principal or 0) for c in contracts])
    total_interest_debt = sum([(c.interest_debt or 0) for c in contracts])
    return "\n".join([
        "<b>THÔNG TIN KHÁCH HÀNG</b>",
        f"{'━' * 15}",
        f"Mã khách hàng: <b>{customer.customer_id or 'N/A'}</b>",
        f"Tên khách hàng: <b>{customer.customer_name or 'N/A'}</b>",
        f"Tên nhóm: {customer.group_name or 'N/A'}",
        f"Liên hệ: {customer.contact_info or 'N/A'}",
        f"Phân loại: {customer.classification or 'N/A'}",
        f"{'━' * 15}",
        f"Tổng hạn mức tín dụng: <b>{_cmv_num(customer.total_credit_limit):,}</b>",
        f"Hạn mức còn lại: <b>{_cmv_num(customer.remaining_credit_limit):,}</b>",
        f"Tổng nợ gốc hiện tại: <b>{_cmv_num(customer.total_principal_outstanding):,}</b>",
        f"{'━' * 15}",
        f"Tổng số hợp đồng: <b>{len(contracts)}</b> (Đang vay: <b>{len(active)}</b>)",
        f"Tổng nợ gốc còn lại: <b>{_cmv_num(total_remaining):,}</b>",
        f"Tổng nợ lãi: <b>{_cmv_num(total_interest_debt):,}</b>",
    ])


def _cmv_contract_text(contract, customer):
    status_label = _CMV_STATUS_LABELS.get(contract.credit_status, "N/A")
    return "\n".join([
        "<b>THÔNG TIN HỢP ĐỒNG</b>",
        f"{'━' * 15}",
        f"Mã hợp đồng: <code>{contract.contract_id or 'N/A'}</code>",
        f"Khách hàng: <b>{customer.customer_name if customer else 'N/A'}</b>"
        f" ({customer.customer_id if customer else 'N/A'})",
        f"Loại hợp đồng: {_cmv_loan_label(contract.loan_type)}",
        f"Trạng thái: <b>{status_label}</b>",
        f"{'━' * 15}",
        f"Nợ gốc ban đầu: <b>{_cmv_num(contract.initial_principal):,}</b>",
        f"Đã trả gốc: <b>{_cmv_num(contract.total_principal_paid):,}</b>",
        f"Nợ gốc còn lại: <b>{_cmv_num(contract.remaining_principal):,}</b>",
        f"Nợ lãi hiện tại: <b>{_cmv_num(contract.interest_debt or 0):,}</b>",
        f"{'━' * 15}",
        f"Ngày bắt đầu vay: {_cmv_date(contract.start_date)}",
        f"Ngày đáo hạn: {_cmv_date(contract.due_date)}",
        f"Ngày bắt đầu thu lãi: {_cmv_date(contract.interest_start_date)}",
        f"Lãi suất / tháng: <b>{_cmv_num(contract.monthly_interest_rate)}%</b>",
        f"Số tiền lãi / tháng: <b>{_cmv_num(contract.monthly_interest_amount):,}</b>",
        f"Ghi chú: {contract.notes or 'Không có'}",
    ])


def _cmv_debt_text(customer, active_credits):
    """Nội dung công nợ hiện tại của một khách hàng."""
    total_principal = sum([(c.remaining_principal or 0) for c in active_credits])
    total_interest = sum([(c.interest_debt or 0) for c in active_credits])
    total_debt = total_principal + total_interest

    contract_lines = []
    for idx, c in enumerate(active_credits, 1):
        status_label = "Nợ xấu" if c.credit_status == CreditStatus.BAD_DEBT.value else "Đang vay"
        contract_lines.append(
            f"{idx}. <b>{c.contract_id}</b> ({_cmv_loan_label(c.loan_type)}) - {status_label}\n"
            f"   Nợ gốc còn: <b>{_cmv_num(c.remaining_principal):,}</b>\n"
            f"   Nợ lãi: <b>{_cmv_num(c.interest_debt or 0):,}</b>\n"
        )

    return "\n".join([
        "<b>CÔNG NỢ HIỆN TẠI</b>",
        f"Khách hàng: <b>{customer.customer_name}</b> (Mã: {customer.customer_id})",
        f"{'━' * 15}",
        f"Tổng hợp đồng: <b>{len(active_credits)}</b>",
        f"Tổng nợ gốc: <b>{_cmv_num(total_principal):,}</b>",
        f"Tổng nợ lãi: <b>{_cmv_num(total_interest):,}</b>",
        f"Tổng nợ: <b>{_cmv_num(total_debt):,}</b>",
        f"{'━' * 15}",
    ] + contract_lines)


def _cmv_debt_keyboard():
    """Bàn phím màn hình công nợ: Quay lại (danh sách khách hàng) và Hủy."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Quay lại", callback_data="cmv_cnl"),
        InlineKeyboardButton("Hủy", callback_data="cmv_x")
    ]])


def _cmv_contract_list_keyboard(contracts, page, customer_hex, page_prefix, item_prefix):
    """Bàn phím danh sách hợp đồng dạng nút, có phân trang và nút Hủy."""
    total = len(contracts)
    total_pages = max(1, (total + _CMV_PAGE_SIZE - 1) // _CMV_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * _CMV_PAGE_SIZE
    page_contracts = contracts[start:min(start + _CMV_PAGE_SIZE, total)]

    buttons = []
    for c in page_contracts:
        status_label = _CMV_STATUS_LABELS.get(c.credit_status, "N/A")
        buttons.append([InlineKeyboardButton(
            f"{c.contract_id} ({status_label})",
            callback_data=f"{item_prefix}|{_sid(c.id)}"
        )])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Trước", callback_data=f"{page_prefix}|{customer_hex}|{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="cmv_n"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau >>", callback_data=f"{page_prefix}|{customer_hex}|{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("Hủy", callback_data="cmv_x")])
    return InlineKeyboardMarkup(buttons)


def _cmv_customer_pick_keyboard(customers, action_prefix):
    """Bàn phím chọn khách hàng khi một nhóm gắn với nhiều khách hàng."""
    buttons = [
        [InlineKeyboardButton(
            f"{c.customer_id} - {c.customer_name}",
            callback_data=f"{action_prefix}|{_sid(c.id)}|0"
        )]
        for c in customers
    ]
    buttons.append([InlineKeyboardButton("Hủy", callback_data="cmv_x")])
    return InlineKeyboardMarkup(buttons)


@bot.on_callback_query(filters.regex(r"^cmv_n$"))
async def cmv_noop_callback(client, callback_query: CallbackQuery):
    await callback_query.answer()


@bot.on_callback_query(filters.regex(r"^cmv_x$"))
async def cmv_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()


async def _cmv_send_customer_info(db, customer, send):
    """Hiển thị thông tin khách hàng kèm 2 nút: Xem hợp đồng, Hủy."""
    contracts = db.query(Credit).filter(Credit.customer_id == customer.id).all()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Xem hợp đồng", callback_data=f"cmv_hd|{_sid(customer.id)}|0")],
        [InlineKeyboardButton("Hủy", callback_data="cmv_x")]
    ])
    await send(_cmv_customer_text(customer, contracts), reply_markup=keyboard, parse_mode=ParseMode.HTML)


@bot.on_message(filters.command(["credit_member_check_customer", "credit_xem_tt_khach_hang"]) | filters.regex(r"^@\w+\s+/(credit_member_check_customer|credit_xem_tt_khach_hang)\b"))
@require_user_type(UserType.MEMBER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("member")
@command_timeout(auto_delete_cmd=True)
async def member_check_customer_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_member_check_customer", "credit_xem_tt_khach_hang"])
    if args is None: return

    db = SessionLocal()
    try:
        customers = _cmv_customers(db, message.chat.id)
        if not customers:
            await message.reply_text("Nhóm này chưa được gắn với khách hàng tín dụng nào.")
            return

        if len(customers) > 1:
            await message.reply_text(
                "<b>THÔNG TIN KHÁCH HÀNG</b>\n\nChọn khách hàng để xem thông tin:",
                reply_markup=_cmv_customer_pick_keyboard(customers, "cmv_kh"),
                parse_mode=ParseMode.HTML
            )
            return

        await _cmv_send_customer_info(db, customers[0], message.reply_text)
    except Exception as e:
        LogError(f"Error in member_check_customer_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("Có lỗi xảy ra khi truy xuất thông tin khách hàng.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cmv_kh\|([a-f0-9]{32})\|(\d+)$"))
@require_group_role("member")
async def cmv_customer_info_callback(client, callback_query: CallbackQuery):
    """Hiển thị thông tin khách hàng đã chọn."""
    customer_uuid = _uid(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
        if not _cmv_owns(db, callback_query.message.chat.id, customer):
            await callback_query.answer("Không tìm thấy khách hàng của nhóm này.", show_alert=True)
            return

        await _cmv_send_customer_info(db, customer, callback_query.message.edit_text)
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cmv_customer_info_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cmv_cn\|([a-f0-9]{32})\|(\d+)$"))
@require_group_role("member")
async def cmv_debt_callback(client, callback_query: CallbackQuery):
    """Hiển thị công nợ hiện tại của khách hàng đã chọn."""
    customer_uuid = _uid(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
        if not _cmv_owns(db, callback_query.message.chat.id, customer):
            await callback_query.answer("Không tìm thấy khách hàng của nhóm này.", show_alert=True)
            return

        active_credits = db.query(Credit).filter(
            Credit.customer_id == customer.id,
            Credit.credit_status.in_([CreditStatus.ACTIVE.value, CreditStatus.BAD_DEBT.value])
        ).all()
        if not active_credits:
            await callback_query.answer(f"{customer.customer_name} hiện không có hợp đồng công nợ nào.", show_alert=True)
            return

        await callback_query.message.edit_text(
            _cmv_debt_text(customer, active_credits),
            reply_markup=_cmv_debt_keyboard(),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cmv_debt_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cmv_cnl$"))
@require_group_role("member")
async def cmv_debt_list_callback(client, callback_query: CallbackQuery):
    """Nút 'Quay lại' ở màn hình công nợ: về danh sách khách hàng của nhóm."""
    db = SessionLocal()
    try:
        customers = _cmv_customers(db, callback_query.message.chat.id)
        if not customers:
            await callback_query.answer("Nhóm này chưa được gắn với khách hàng tín dụng nào.", show_alert=True)
            return

        await callback_query.message.edit_text(
            "<b>CÔNG NỢ HIỆN TẠI</b>\n\nChọn khách hàng để xem công nợ:",
            reply_markup=_cmv_customer_pick_keyboard(customers, "cmv_cn"),
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cmv_debt_list_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cmv_hd\|([a-f0-9]{32})\|(\d+)$"))
@require_group_role("member")
async def cmv_contract_list_callback(client, callback_query: CallbackQuery):
    """Nút 'Xem hợp đồng': danh sách hợp đồng của khách hàng."""
    customer_uuid = _uid(callback_query.matches[0].group(1))
    page = int(callback_query.matches[0].group(2))
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
        if not _cmv_owns(db, callback_query.message.chat.id, customer):
            await callback_query.answer("Không tìm thấy khách hàng của nhóm này.", show_alert=True)
            return

        contracts = db.query(Credit).filter(Credit.customer_id == customer.id).order_by(Credit.contract_id).all()
        if not contracts:
            await callback_query.answer("Khách hàng chưa có hợp đồng nào.", show_alert=True)
            return

        keyboard = _cmv_contract_list_keyboard(contracts, page, _sid(customer.id), "cmv_hd", "cmv_hdc")
        await callback_query.message.edit_text(
            f"<b>DANH SÁCH HỢP ĐỒNG</b>\n"
            f"Khách hàng: <b>{customer.customer_name}</b> ({customer.customer_id})\n\n"
            f"Chọn hợp đồng để xem thông tin:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cmv_contract_list_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cmv_hdc\|([a-f0-9]{32})$"))
@require_group_role("member")
async def cmv_contract_detail_callback(client, callback_query: CallbackQuery):
    """Thông tin hợp đồng (luồng xem thông tin khách hàng) kèm nút Hủy."""
    contract_uuid = _uid(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        contract = db.query(Credit).filter(Credit.id == contract_uuid).first()
        customer = contract.customer if contract else None
        if not _cmv_owns(db, callback_query.message.chat.id, customer):
            await callback_query.answer("Không tìm thấy hợp đồng của nhóm này.", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Hủy", callback_data="cmv_x")]])
        await callback_query.message.edit_text(
            _cmv_contract_text(contract, customer),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cmv_contract_detail_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_message(filters.command(["credit_member_check_contract", "credit_xem_tt_hop_dong"]) | filters.regex(r"^@\w+\s+/(credit_member_check_contract|credit_xem_tt_hop_dong)\b"))
@require_user_type(UserType.MEMBER, UserType.ADMIN)
@require_project_name("Credit")
@require_group_role("member")
@command_timeout(auto_delete_cmd=True)
async def member_check_contract_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["credit_member_check_contract", "credit_xem_tt_hop_dong"])
    if args is None: return

    db = SessionLocal()
    try:
        customers = _cmv_customers(db, message.chat.id)
        if not customers:
            await message.reply_text("Nhóm này chưa được gắn với khách hàng tín dụng nào.")
            return

        if len(customers) > 1:
            await message.reply_text(
                "<b>DANH SÁCH HỢP ĐỒNG</b>\n\nChọn khách hàng để xem danh sách hợp đồng:",
                reply_markup=_cmv_customer_pick_keyboard(customers, "cmv_ds"),
                parse_mode=ParseMode.HTML
            )
            return

        customer = customers[0]
        contracts = db.query(Credit).filter(Credit.customer_id == customer.id).order_by(Credit.contract_id).all()
        if not contracts:
            await message.reply_text("Khách hàng chưa có hợp đồng nào.")
            return

        keyboard = _cmv_contract_list_keyboard(contracts, 0, _sid(customer.id), "cmv_ds", "cmv_dsc")
        await message.reply_text(
            f"<b>DANH SÁCH HỢP ĐỒNG</b>\n"
            f"Khách hàng: <b>{customer.customer_name}</b> ({customer.customer_id})\n\n"
            f"Chọn hợp đồng để xem thông tin:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LogError(f"Error in member_check_contract_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("Có lỗi xảy ra khi truy xuất danh sách hợp đồng.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cmv_ds\|([a-f0-9]{32})\|(\d+)$"))
@require_group_role("member")
async def cmv_member_contract_list_callback(client, callback_query: CallbackQuery):
    """Danh sách hợp đồng (luồng xem thông tin hợp đồng)."""
    customer_uuid = _uid(callback_query.matches[0].group(1))
    page = int(callback_query.matches[0].group(2))
    db = SessionLocal()
    try:
        customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_uuid).first()
        if not _cmv_owns(db, callback_query.message.chat.id, customer):
            await callback_query.answer("Không tìm thấy khách hàng của nhóm này.", show_alert=True)
            return

        contracts = db.query(Credit).filter(Credit.customer_id == customer.id).order_by(Credit.contract_id).all()
        if not contracts:
            await callback_query.answer("Khách hàng chưa có hợp đồng nào.", show_alert=True)
            return

        keyboard = _cmv_contract_list_keyboard(contracts, page, _sid(customer.id), "cmv_ds", "cmv_dsc")
        await callback_query.message.edit_text(
            f"<b>DANH SÁCH HỢP ĐỒNG</b>\n"
            f"Khách hàng: <b>{customer.customer_name}</b> ({customer.customer_id})\n\n"
            f"Chọn hợp đồng để xem thông tin:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cmv_member_contract_list_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cmv_dsc\|([a-f0-9]{32})$"))
@require_group_role("member")
async def cmv_member_contract_detail_callback(client, callback_query: CallbackQuery):
    """Thông tin hợp đồng (luồng xem thông tin hợp đồng) kèm nút Quay lại, Hủy."""
    contract_uuid = _uid(callback_query.matches[0].group(1))
    db = SessionLocal()
    try:
        contract = db.query(Credit).filter(Credit.id == contract_uuid).first()
        customer = contract.customer if contract else None
        if not _cmv_owns(db, callback_query.message.chat.id, customer):
            await callback_query.answer("Không tìm thấy hợp đồng của nhóm này.", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Quay lại", callback_data=f"cmv_ds|{_sid(customer.id)}|0"),
            InlineKeyboardButton("Hủy", callback_data="cmv_x")
        ]])
        await callback_query.message.edit_text(
            _cmv_contract_text(contract, customer),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in cmv_member_contract_detail_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()

