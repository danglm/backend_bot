from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from bot.utils.bot import bot
from bot.utils.utils import check_command_target, require_user_type, require_project_name, require_custom_title, require_group_role
from bot.utils.enums import UserType
from bot.utils.logger import LogInfo, LogError, LogType
from app.db.session import SessionLocal
import re
from datetime import datetime, timedelta
import traceback

# TienNga project handlers


# --- Thêm nhân viên ---
@bot.on_message(filters.command(["tien_nga_create_employee", "tien_nga_tao_nhan_vien"]) | filters.regex(r"^@\w+\s+/(tien_nga_create_employee|tien_nga_tao_nhan_vien)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ns")
async def tien_nga_create_employee_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_create_employee", "tien_nga_tao_nhan_vien"])
    if args is None: return

    from bot.utils.human_resource import handle_create_employee
    await handle_create_employee(client, message, "/tien_nga_create_employee")


# --- Cập nhật nhân viên ---
@bot.on_message(filters.command(["tien_nga_update_employee", "tien_nga_cap_nhat_nhan_vien"]) | filters.regex(r"^@\w+\s+/(tien_nga_update_employee|tien_nga_cap_nhat_nhan_vien)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ns")
async def tien_nga_update_employee_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_update_employee", "tien_nga_cap_nhat_nhan_vien"])
    if args is None: return

    from bot.utils.human_resource import handle_update_employee
    await handle_update_employee(client, message, "/tien_nga_update_employee")


# --- Xóa nhân viên (soft delete) ---
@bot.on_message(filters.command(["tien_nga_delete_employee", "tien_nga_xoa_nhan_vien"]) | filters.regex(r"^@\w+\s+/(tien_nga_delete_employee|tien_nga_xoa_nhan_vien)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ns")
async def tien_nga_delete_employee_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_delete_employee", "tien_nga_xoa_nhan_vien"])
    if args is None: return

    from bot.utils.human_resource import handle_delete_employee
    await handle_delete_employee(client, message, "/tien_nga_delete_employee")


@bot.on_callback_query(filters.regex(r"^del_emp_(confirm|cancel)\|(.+)$"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def tien_nga_delete_employee_cb_handler(client, callback_query):
    from bot.utils.human_resource import handle_delete_employee_callback
    await handle_delete_employee_callback(client, callback_query)




# --- Chấm công (Check-in) ---
@bot.on_message(filters.command(["tien_nga_check_in", "tien_nga_cham_cong"]) | filters.regex(r"^@\w+\s+/(tien_nga_check_in|tien_nga_cham_cong)\b"))
@require_project_name("Tiến Nga")
@require_group_role("member")
@require_custom_title("member_ns")
async def tien_nga_check_in_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_check_in", "tien_nga_cham_cong"])
    if args is None: return

    from bot.utils.human_resource import handle_check_in
    await handle_check_in(client, message, "/tien_nga_check_in")


# --- Tan ca (Check-out) ---
@bot.on_message(filters.command(["tien_nga_check_out", "tien_nga_tan_ca"]) | filters.regex(r"^@\w+\s+/(tien_nga_check_out|tien_nga_tan_ca)\b"))
@require_project_name("Tiến Nga")
@require_group_role("member")
@require_custom_title("member_ns")
async def tien_nga_check_out_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_check_out", "tien_nga_tan_ca"])
    if args is None: return

    from bot.utils.human_resource import handle_check_out
    await handle_check_out(client, message, "/tien_nga_check_out")


# --- Xin nghỉ phép (Request Leave) ---
@bot.on_message(filters.command(["tien_nga_request_leave", "tien_nga_xin_nghi_phep"]) | filters.regex(r"^@\w+\s+/(tien_nga_request_leave|tien_nga_xin_nghi_phep)\b"))
@require_project_name("Tiến Nga")
@require_group_role("member")
@require_custom_title("member_ns")
async def tien_nga_request_leave_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_request_leave", "tien_nga_xin_nghi_phep"])
    if args is None: return

    from bot.utils.human_resource import handle_request_leave
    await handle_request_leave(client, message, "/tien_nga_request_leave")


# --- Đăng ký tăng ca (Request Overtime) ---
@bot.on_message(filters.command(["tien_nga_request_overtime", "tien_nga_dang_ky_tang_ca"]) | filters.regex(r"^@\w+\s+/(tien_nga_request_overtime|tien_nga_dang_ky_tang_ca)\b"))
@require_project_name("Tiến Nga")
@require_group_role("member")
@require_custom_title("member_ns")
async def tien_nga_request_overtime_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_request_overtime", "tien_nga_dang_ky_tang_ca"])
    if args is None: return

    from bot.utils.human_resource import handle_request_overtime
    await handle_request_overtime(client, message, "/tien_nga_request_overtime")


# --- Xem chấm công (List Check-in) ---
@bot.on_message(filters.command(["tien_nga_list_check_in", "tien_nga_xem_cham_cong"]) | filters.regex(r"^@\w+\s+/(tien_nga_list_check_in|tien_nga_xem_cham_cong)\b"))
@require_project_name("Tiến Nga")
@require_group_role("member")
@require_custom_title("member_ns")
async def tien_nga_list_check_in_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_list_check_in", "tien_nga_xem_cham_cong"])
    if args is None: return

    from bot.utils.human_resource import handle_list_check_in
    await handle_list_check_in(client, message, "/tien_nga_list_check_in")


# --- Xem danh sách nghỉ phép (List Request Leave) ---
@bot.on_message(filters.command(["tien_nga_list_request_leave", "tien_nga_xem_nghi_phep"]) | filters.regex(r"^@\w+\s+/(tien_nga_list_request_leave|tien_nga_xem_nghi_phep)\b"))
@require_project_name("Tiến Nga")
@require_group_role("member")
@require_custom_title("member_ns")
async def tien_nga_list_request_leave_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_list_request_leave", "tien_nga_xem_nghi_phep"])
    if args is None: return

    from bot.utils.human_resource import handle_list_request_leave
    await handle_list_request_leave(client, message, "/tien_nga_list_request_leave")


# --- Giao việc (Create Task) ---
@bot.on_message(filters.command(["tien_nga_create_task", "tien_nga_giao_viec"]) | filters.regex(r"^@\w+\s+/(tien_nga_create_task|tien_nga_giao_viec)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main", "member")
@require_custom_title("super_main", "main_ns")
async def tien_nga_create_task_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_create_task", "tien_nga_giao_viec"])
    if args is None: return

    from bot.utils.human_resource import handle_create_task
    await handle_create_task(client, message, "/tien_nga_create_task")


# --- Xem danh sách task (List Tasks) ---
@bot.on_message(filters.command(["tien_nga_list_tasks", "tien_nga_xem_cong_viec"]) | filters.regex(r"^@\w+\s+/(tien_nga_list_tasks|tien_nga_xem_cong_viec)\b"))
@require_project_name("Tiến Nga")
@require_group_role("member")
@require_custom_title("member_ns")
async def tien_nga_list_tasks_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_list_tasks", "tien_nga_xem_cong_viec"])
    if args is None: return

    from bot.utils.human_resource import handle_list_tasks
    await handle_list_tasks(client, message, "/tien_nga_list_tasks")


# --- Task callback handlers ---
@bot.on_callback_query(filters.regex(r"^tsk_sel_(.+)$"))
async def _tsk_sel(client, callback_query):
    from bot.utils.human_resource import task_select_callback
    await task_select_callback(client, callback_query)

@bot.on_callback_query(filters.regex(r"^tsk_detail_(.+)$"))
async def _tsk_detail(client, callback_query):
    from bot.utils.human_resource import task_detail_callback
    await task_detail_callback(client, callback_query)

@bot.on_callback_query(filters.regex(r"^tsk_status_(.+)$"))
async def _tsk_status(client, callback_query):
    from bot.utils.human_resource import task_status_callback
    await task_status_callback(client, callback_query)

@bot.on_callback_query(filters.regex(r"^tsk_set_(PENDING|IN_PROGRESS|COMPLETED|CANCELLED)_(.+)$"))
async def _tsk_set(client, callback_query):
    from bot.utils.human_resource import task_set_status_callback
    await task_set_status_callback(client, callback_query)

@bot.on_callback_query(filters.regex(r"^tsk_back_list$"))
async def _tsk_back(client, callback_query):
    from bot.utils.human_resource import task_back_list_callback
    await task_back_list_callback(client, callback_query)

@bot.on_callback_query(filters.regex(r"^tsk_cancel$"))
async def _tsk_cancel(client, callback_query):
    from bot.utils.human_resource import task_cancel_callback
    await task_cancel_callback(client, callback_query)


# --- Hủy task (Reply /cancel vào tin nhắn task) ---
@bot.on_message(filters.command(["cancel", "huy_task"]) & filters.reply)
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ns")
async def tien_nga_cancel_task_handler(client, message: Message) -> None:
    from bot.utils.human_resource import handle_cancel_task_reply
    await handle_cancel_task_reply(client, message)


# --- Xem công việc của nhân viên (Admin) ---
@bot.on_message(filters.command(["tien_nga_check_tasks"]) | filters.regex(r"^@\w+\s+/tien_nga_check_tasks\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ns")
async def tien_nga_check_tasks_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_check_tasks"])
    if args is None: return

    from bot.utils.human_resource import handle_check_tasks
    await handle_check_tasks(client, message, "/tien_nga_check_tasks")


# --- Xuất bảng lương (Export Payroll) ---
@bot.on_message(filters.command(["export_payroll", "tien_nga_xuat_luong", "tien_nga_export_payroll"]) | filters.regex(r"^@\w+\s+/(export_payroll|tien_nga_xuat_luong|tien_nga_export_payroll)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ns")
async def tien_nga_export_payroll_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["export_payroll", "tien_nga_xuat_luong", "tien_nga_export_payroll"])
    if args is None: return

    from bot.utils.human_resource import handle_export_payroll
    # Re-construct message.text for the actual handler to parse args
    import re
    cmd = args[0] if args else "export_payroll"
    message.text = f"/{cmd} " + " ".join(args[1:]) if len(args) > 1 else f"/{cmd}"
    await handle_export_payroll(client, message, f"/{cmd}")


# --- Tạo lại bảng chấm công (Recreate Attendance Report) ---
@bot.on_message(filters.command(["tien_nga_recreate_attendance_report"]) | filters.regex(r"^@\w+\s+/tien_nga_recreate_attendance_report\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ns")
async def tien_nga_recreate_attendance_report_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["tien_nga_recreate_attendance_report"])
    if args is None: return

    from bot.utils.human_resource import handle_recreate_attendance_report
    import re
    cmd = args[0] if args else "tien_nga_recreate_attendance_report"
    message.text = f"/{cmd} " + " ".join(args[1:]) if len(args) > 1 else f"/{cmd}"
    await handle_recreate_attendance_report(client, message, f"/{cmd}")


#############  Nhà cung cấp #############
# --- Tạo điểm thu mua (Create Collection Point) ---
@bot.on_message(filters.command(["tien_nga_create_collection_point"]) | filters.regex(r"^@\w+\s+/tien_nga_create_collection_point\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ncc")
async def tien_nga_create_collection_point_handler(client, message: Message) -> None:
    lines = message.text.strip().split("\n")
    
    # Nếu chỉ gõ lệnh không -> hiển thị form
    if len(lines) < 2:
        form_template = """<b>FORM TẠO ĐIỂM THU MUA MỚI</b>
Vui lòng sao chép form dưới đây, điền đầy đủ thông tin và gửi lại:

<pre>/tien_nga_create_collection_point
Tên Điểm Thu Mua: 
Địa Chỉ: </pre>"""
        await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        return

    # Parse form data
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    collection_name = data.get("Tên Điểm Thu Mua", "").strip()
    address = data.get("Địa Chỉ", "").strip()

    if not collection_name or not address:
        await message.reply_text(
            "⚠️ <b>Tên Điểm Thu Mua</b> và <b>Địa Chỉ</b> là bắt buộc.",
            parse_mode=ParseMode.HTML
        )
        return

    from app.db.session import SessionLocal
    from app.models.business import CollectionPoint
    
    db = SessionLocal()
    try:
        # Check if already exists
        existing = db.query(CollectionPoint).filter(CollectionPoint.collection_name == collection_name).first()
        if existing:
            await message.reply_text(
                f"⚠️ Điểm thu mua <b>{collection_name}</b> đã tồn tại trong hệ thống.",
                parse_mode=ParseMode.HTML
            )
            return
            
        new_point = CollectionPoint(
            collection_name=collection_name,
            address=address
        )
        db.add(new_point)
        db.commit()
        
        LogInfo(f"[TienNga] Created collection point '{collection_name}' by user {message.from_user.id}", LogType.SYSTEM_STATUS)
        
        await message.reply_text(
            f"✅ <b>TẠO ĐIỂM THU MUA THÀNH CÔNG</b>\n\n"
            f"<b>Tên:</b> {collection_name}\n"
            f"<b>Địa Chỉ:</b> {address}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LogError(f"Error creating collection point: {e}", LogType.SYSTEM_STATUS)
        db.rollback()
        await message.reply_text("❌ Có lỗi xảy ra khi lưu vào database.", parse_mode=ParseMode.HTML)
    finally:
        db.close()



# --- Tạo Khách Hàng Mới (Create Customer) ---
@bot.on_message(filters.command(["tien_nga_create_customer"]) | filters.regex(r"^@\w+\s+/tien_nga_create_customer\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", 'main_ncc')
async def tien_nga_create_customer_handler(client, message: Message) -> None:
    lines = message.text.strip().split("\n")
    
    # Nếu chỉ gõ lệnh không -> hiển thị button chọn xưởng thu mua
    if len(lines) < 2:
        from app.db.session import SessionLocal
        from app.models.business import CollectionPoint
        
        db = SessionLocal()
        try:
            points = db.query(CollectionPoint).all()
            if not points:
                await message.reply_text("⚠️ Chưa có Điểm Thu Mua nào. Vui lòng tạo trước bằng lệnh /tien_nga_create_collection_point.")
                return
                
            buttons = []
            for p in points:
                buttons.append([InlineKeyboardButton(p.collection_name, callback_data=f"tn_selcp_{p.id}")])
                
            markup = InlineKeyboardMarkup(buttons)
            await message.reply_text("<b>Vui lòng chọn Điểm Thu Mua (Xưởng) cho Khách Hàng:</b>", reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            LogError(f"Error listing collection points: {e}", LogType.SYSTEM_STATUS)
            await message.reply_text("❌ Có lỗi xảy ra.")
        finally:
            db.close()
        return

    # Parse form data
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    cp_id = data.get("Mã Điểm Thu", "").strip()
    fullname = data.get("Tên Khách Hàng", "").strip()
    hoursehold_id = data.get("Mã Hộ", "").strip()
    phone = data.get("SĐT Khách", "").strip()
    address = data.get("Địa Chỉ", "").strip()
    ingredient = data.get("Nguyên Liệu", "").strip()
    username = data.get("Username TG", "").strip()
    
    amount_of_debt = parse_float_vn(data.get("Số Tiền Nợ", "0"))
    cash_advance = parse_float_vn(data.get("Ứng Tiền Cuối Mùa", "0"))
    total_debt = parse_float_vn(data.get("Tổng Công Nợ", "0"))

    if not cp_id or not fullname or not hoursehold_id:
        await message.reply_text("⚠️ <b>Mã Điểm Thu</b>, <b>Tên Khách Hàng</b> và <b>Mã Hộ</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    from app.db.session import SessionLocal
    from app.models.business import Customers
    import uuid
    
    db = SessionLocal()
    try:
        existing = db.query(Customers).filter(Customers.hoursehold_id == hoursehold_id).first()
        if existing:
            await message.reply_text(f"⚠️ Khách hàng mã hộ <b>{hoursehold_id}</b> đã tồn tại.", parse_mode=ParseMode.HTML)
            return
            
        new_customer = Customers(
            id=str(uuid.uuid4()),
            fullname=fullname,
            hoursehold_id=hoursehold_id,
            collection_point_id=cp_id,
            number_phone=phone,
            address=address,
            ingredient=ingredient,
            amount_of_debt=int(amount_of_debt),
            cash_advance=int(cash_advance),
            total_debt=int(total_debt),
            username=username if username else None
        )
        db.add(new_customer)
        db.commit()
        
        LogInfo(f"[TienNga] Created customer '{hoursehold_id}' by user {message.from_user.id}", LogType.SYSTEM_STATUS)
        
        await message.reply_text(f"✅ <b>TẠO KHÁCH HÀNG THÀNH CÔNG</b>\n\n<b>Mã Hộ:</b> {hoursehold_id}\n<b>Tên KH:</b> {fullname}", parse_mode=ParseMode.HTML)
    except Exception as e:
        LogError(f"Error creating customer: {e}", LogType.SYSTEM_STATUS)
        db.rollback()
        await message.reply_text("❌ Có lỗi xảy ra khi lưu vào database.", parse_mode=ParseMode.HTML)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^tn_selcp_(.+)$"))
async def tien_nga_select_collection_point_callback(client, callback_query):
    cp_id = callback_query.matches[0].group(1)
    from app.db.session import SessionLocal
    from app.models.business import CollectionPoint
    
    db = SessionLocal()
    try:
        cp = db.query(CollectionPoint).filter(CollectionPoint.id == cp_id).first()
        if not cp:
            await callback_query.answer("⚠️ Không tìm thấy Điểm Thu Mua", show_alert=True)
            return
            
        cp_name = cp.collection_name
        form_template = f"""<b>FORM TẠO KHÁCH HÀNG MỚI</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/tien_nga_create_customer
Mã Điểm Thu: {cp_id}
Tên Khách Hàng: 
Mã Hộ: 
SĐT Khách: 
Địa Chỉ: 
Nguyên Liệu: 
Số Tiền Nợ: 
Ứng Tiền Cuối Mùa: 
Tổng Công Nợ: 
Username TG: </pre>

<i>(*Ghi chú: Đang thêm khách hàng cho Xưởng: <b>{cp_name}</b>)</i>"""
        await callback_query.message.reply_text(form_template, parse_mode=ParseMode.HTML)
        await callback_query.answer()
    except Exception as e:
        LogError(f"Error in select collection point: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Lỗi hệ thống", show_alert=True)
    finally:
        db.close()

# --- Cập Nhật Khách Hàng (Update Customer) ---
@bot.on_message(filters.command(["tien_nga_update_customer"]) | filters.regex(r"^@\w+\s+/tien_nga_update_customer\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_custom_title("super_main", 'main_ncc')
async def tien_nga_update_customer_handler(client, message: Message) -> None:
    lines = message.text.strip().split("\n")
    
    # Nếu chỉ có 1 dòng (chứa lệnh và có thể là ID)
    if len(lines) < 2:
        args = lines[0].split()
        if len(args) != 2:
            await message.reply_text("⚠️ Cú pháp: <code>/tien_nga_update_customer [Mã Hộ]</code>\n\n<i>Ví dụ: <code>/tien_nga_update_customer KH001</code></i>", parse_mode=ParseMode.HTML)
            return
            
        hoursehold_id = args[1]
        
        from app.db.session import SessionLocal
        from app.models.business import Customers
        
        db = SessionLocal()
        try:
            customer = db.query(Customers).filter(Customers.hoursehold_id == hoursehold_id).first()
            if not customer:
                await message.reply_text(f"⚠️ Không tìm thấy Khách hàng với mã hộ <b>{hoursehold_id}</b>.", parse_mode=ParseMode.HTML)
                return
                
            def fmt_num(val):
                if val is None: return 0
                return int(val) if val == int(val) else val
            
            # Format number output to Vietnam string but keeping the numeric in form to be copy pasted easily
            form_template = f"""<b>FORM CẬP NHẬT KHÁCH HÀNG</b>
Vui lòng sao chép form dưới đây, sửa thông tin và gửi lại:

<pre>/tien_nga_update_customer
Mã Hộ: {customer.hoursehold_id}
Tên Khách Hàng: {customer.fullname or ""}
SĐT Khách: {customer.number_phone or ""}
Địa Chỉ: {customer.address or ""}
Nguyên Liệu: {customer.ingredient or ""}
Số Tiền Nợ: {fmt_num(customer.amount_of_debt)}
Ứng Tiền Cuối Mùa: {fmt_num(customer.cash_advance)}
Tổng Công Nợ: {fmt_num(customer.total_debt)}
Username: {customer.username or ''}</pre>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        except Exception as e:
            LogError(f"Error fetching customer for update: {e}", LogType.SYSTEM_STATUS)
            await message.reply_text("❌ Lỗi hệ thống.", parse_mode=ParseMode.HTML)
        finally:
            db.close()
        return

    # Parse form data (nhiều dòng)
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    hoursehold_id = data.get("Mã Hộ", "").strip()
    if not hoursehold_id:
        await message.reply_text("⚠️ <b>Mã Hộ</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return
        
    fullname = data.get("Tên Khách Hàng", "").strip()
    phone = data.get("SĐT Khách", "").strip()
    address = data.get("Địa Chỉ", "").strip()
    ingredient = data.get("Nguyên Liệu", "").strip()
    username = data.get("Username", "").strip()
    
    amount_of_debt = parse_float_vn(data.get("Số Tiền Nợ", "0"))
    cash_advance = parse_float_vn(data.get("Ứng Tiền Cuối Mùa", "0"))
    total_debt = parse_float_vn(data.get("Tổng Công Nợ", "0"))

    from app.db.session import SessionLocal
    from app.models.business import Customers
    
    db = SessionLocal()
    try:
        customer = db.query(Customers).filter(Customers.hoursehold_id == hoursehold_id).first()
        if not customer:
            await message.reply_text(f"⚠️ Khách hàng mã hộ <b>{hoursehold_id}</b> không tồn tại.", parse_mode=ParseMode.HTML)
            return
            
        if fullname: customer.fullname = fullname
        customer.number_phone = phone
        customer.address = address
        customer.ingredient = ingredient
        customer.amount_of_debt = int(amount_of_debt)
        customer.cash_advance = int(cash_advance)
        customer.total_debt = int(total_debt)
        customer.username = username
        
        db.commit()
        
        LogInfo(f"[TienNga] Updated customer '{hoursehold_id}' by user {message.from_user.id}", LogType.SYSTEM_STATUS)
        
        def fmt_vn(val):
            if val is None: return "0"
            return f"{int(val):,}".replace(",", ".")
            
        await message.reply_text(
            f"✅ <b>CẬP NHẬT KHÁCH HÀNG THÀNH CÔNG</b>\n\n"
            f"<b>Mã Hộ:</b> {hoursehold_id}\n"
            f"<b>Tên KH:</b> {customer.fullname}\n"
            f"<b>SĐT:</b> {customer.number_phone or '—'}\n"
            f"<b>Địa Chỉ:</b> {customer.address or '—'}\n"
            f"<b>Nguyên Liệu:</b> {customer.ingredient or '—'}\n"
            f"<b>Số Tiền Nợ:</b> <code>{fmt_vn(customer.amount_of_debt)}</code>\n"
            f"<b>Ứng Cuối Mùa:</b> <code>{fmt_vn(customer.cash_advance)}</code>\n"
            f"<b>Tổng Nợ:</b> <code>{fmt_vn(customer.total_debt)}</code>\n"
            f"<b>Username:</b> {customer.username or '—'}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LogError(f"Error updating customer: {e}", LogType.SYSTEM_STATUS)
        db.rollback()
        await message.reply_text("❌ Có lỗi xảy ra khi lưu vào database.", parse_mode=ParseMode.HTML)
    finally:
        db.close()


# --- Xóa Khách Hàng (Soft Delete Customer) ---
@bot.on_message(filters.command(["tien_nga_delete_customer"]) | filters.regex(r"^@\w+\s+/tien_nga_delete_customer\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ncc")
async def tien_nga_delete_customer_handler(client, message: Message) -> None:
    args = message.text.split()
    if len(args) != 2:
        await message.reply_text(
            "⚠️ Cú pháp: <code>/tien_nga_delete_customer [Mã Hộ]</code>\n\n"
            "<i>Ví dụ: <code>/tien_nga_delete_customer KH001</code></i>",
            parse_mode=ParseMode.HTML
        )
        return
        
    hoursehold_id = args[1]
    
    from app.db.session import SessionLocal
    from app.models.business import Customers
    
    db = SessionLocal()
    try:
        customer = db.query(Customers).filter(Customers.hoursehold_id == hoursehold_id).first()
        if not customer:
            await message.reply_text(f"⚠️ Không tìm thấy Khách hàng mã hộ <b>{hoursehold_id}</b>.", parse_mode=ParseMode.HTML)
            return
            
        if customer.status == "INACTIVE" or customer.status == "DELETED":
            await message.reply_text(f"ℹ️ Khách hàng mã hộ <b>{hoursehold_id}</b> đã ở trạng thái khóa / xóa từ trước.", parse_mode=ParseMode.HTML)
            return

        customer.status = "DELETED"
        db.commit()
        
        LogInfo(f"[TienNga] Soft deleted customer '{hoursehold_id}' by user {message.from_user.id}", LogType.SYSTEM_STATUS)
        
        await message.reply_text(
            f"✅ <b>XÓA KHÁCH HÀNG THÀNH CÔNG</b>\n\n"
            f"Mã Hộ: <b>{hoursehold_id}</b>\n"
            f"Tên KH: {customer.fullname}\n"
            f"<i>Khách hàng này đã được ẩn (chuyển sang trạng thái DELETED).</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LogError(f"Error soft deleting customer: {e}", LogType.SYSTEM_STATUS)
        db.rollback()
        await message.reply_text("❌ Có lỗi xảy ra khi cập nhật database.", parse_mode=ParseMode.HTML)
    finally:
        db.close()


# --- Xuất danh sách khách hàng (List Customers) ---
@bot.on_message(filters.command(["tien_nga_list_customers", "tien_nga_ds_khach_hang"]) | filters.regex(r"^@\w+\s+/(tien_nga_list_customers|tien_nga_ds_khach_hang)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ncc")
async def tien_nga_list_customers_handler(client, message: Message) -> None:
    args = message.text.strip().split()

    db = SessionLocal()
    try:
        from app.models.business import Customers, CollectionPoint
        import tempfile
        import os
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        # Query all active customers with their collection point info
        customers = (
            db.query(Customers, CollectionPoint.collection_name)
            .outerjoin(CollectionPoint, Customers.collection_point_id == CollectionPoint.id)
            .filter(Customers.status == "ACTIVE")
            .order_by(CollectionPoint.collection_name, Customers.id)
            .all()
        )

        if not customers:
            await message.reply_text(
                "⚠️ Không có khách hàng nào trong hệ thống.",
                parse_mode=ParseMode.HTML,
            )
            return

        # Group customers by collection point
        grouped = {}
        for cust, cp_name in customers:
            group_key = cp_name or "Chưa phân loại"
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(cust)

        # Build Excel workbook
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # remove default sheet

        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill("solid", fgColor="2F5496")
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
        money_align = Alignment(horizontal="right", vertical="center")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        alt_fill = PatternFill("solid", fgColor="D9E2F3")

        headers = [
            "STT",
            "Mã Hộ",
            "Tên Khách Hàng",
            "Số Điện Thoại",
            "Địa Chỉ",
            "Nguyên Liệu",
            "Số Tiền Nợ",
            "Ứng Tiền Cuối Mùa",
            "Tổng Công Nợ",
            "Username TG",
            "Trạng Thái",
        ]

        col_widths = [6, 10, 22, 16, 25, 15, 18, 20, 18, 18, 12]

        total_customers = 0

        for group_name, custs in grouped.items():
            # Excel sheet name max 31 chars
            sheet_name = group_name[:31]
            ws = wb.create_sheet(title=sheet_name)

            # Write headers
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align
                cell.border = thin_border

            # Write data rows
            def fmt_money(val):
                if val is None or val == 0:
                    return "0"
                return f"{int(val):,}".replace(",", ".")

            for idx, cust in enumerate(custs, 1):
                row = idx + 1
                row_fill = alt_fill if idx % 2 == 0 else None

                values = [
                    idx,
                    cust.hoursehold_id or cust.id,
                    cust.fullname,
                    cust.number_phone,
                    cust.address,
                    cust.ingredient,
                    fmt_money(cust.amount_of_debt),
                    fmt_money(cust.cash_advance),
                    fmt_money(cust.total_debt),
                    cust.username,
                    cust.status,
                ]

                for col_idx, val in enumerate(values, 1):
                    cell = ws.cell(row=row, column=col_idx, value=val)
                    cell.border = thin_border
                    if col_idx in (7, 8, 9):  # Money columns
                        cell.alignment = money_align
                    elif col_idx == 1:
                        cell.alignment = center_align
                    else:
                        cell.alignment = left_align
                    if row_fill:
                        cell.fill = row_fill

            total_customers += len(custs)

            # Set column widths
            for col_idx, width in enumerate(col_widths, 1):
                col_letter = openpyxl.utils.get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = width

            # Freeze header row
            ws.freeze_panes = "A2"

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp_path = tmp.name
        wb.save(tmp_path)

        now_str = datetime.now().strftime("%Y%m%d_%H%M")
        summary_lines = "\n".join(
            f"  • <b>{name}</b>: {len(custs)} KH" for name, custs in grouped.items()
        )

        await message.reply_document(
            document=tmp_path,
            file_name=f"danh_sach_khach_hang_{now_str}.xlsx",
            caption=(
                f"<b>DANH SÁCH KHÁCH HÀNG</b>\n\n"
                f"Tổng: <b>{total_customers}</b> khách hàng\n"
                f"Số Xưởng: <b>{len(grouped)}</b>\n\n"
                f"{summary_lines}\n\n"
                f"<i>Xuất lúc: {datetime.now().strftime('%H:%M %d/%m/%Y')}</i>"
            ),
            parse_mode=ParseMode.HTML,
        )

        os.remove(tmp_path)
        LogInfo(
            f"[TienNga] Exported {total_customers} customers by @{message.from_user.username or message.from_user.id}",
            LogType.SYSTEM_STATUS,
        )

    except Exception as e:
        LogError(f"Error in tien_nga_list_customers_handler: {e}", LogType.SYSTEM_STATUS)
        import traceback
        traceback.print_exc()
        await message.reply_text(
            f"❌ Có lỗi xảy ra khi xuất danh sách: {e}",
            parse_mode=ParseMode.HTML,
        )
    finally:
        db.close()


def parse_float_vn(val_str: str) -> float:
    """Parse số tiền kiểu Việt Nam (1.000.000,5 hoặc -3.000.000)"""
    if not val_str:
        return 0.0
    v = val_str.strip()
    
    negative = v.startswith("-")
    v = v.lstrip("-").strip()
    
    # Remove currency symbols
    v = re.sub(r'[^0-9.,-]', '', v)
    if not v:
        return 0.0
    
    # Vietnamese format: 1.000.000,5 -> dots are thousand separators, comma is decimal
    if "," in v and "." in v:
        # 5.898.728,5 -> remove dots, replace comma with dot
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:
        # Could be 1,5 (decimal) or 1,000 (thousands)
        parts = v.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            v = v.replace(",", ".")
        else:
            v = v.replace(",", "")
    elif "." in v:
        # Could be 1.000.000 (VN thousands) or 1.5 (decimal)
        parts = v.split(".")
        if all(len(p) == 3 for p in parts[1:]):
            v = v.replace(".", "")
        # else keep as is (decimal dot)
    
    try:
        result = float(v)
        return -result if negative else result
    except ValueError:
        return 0.0

# --- Nhập mua mủ hàng ngày (Daily Purchase) ---
@bot.on_message(filters.command(["tien_nga_daily_purchase"]) | filters.regex(r"^@\w+\s+/tien_nga_daily_purchase\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ncc")
async def tien_nga_daily_purchase_handler(client, message: Message) -> None:
    lines = message.text.strip().split("\n")
    
    # Nếu chỉ có 1 dòng (lệnh + có thể mã hộ)
    if len(lines) < 2:
        args = lines[0].split()
        if len(args) < 2:
            await message.reply_text(
                "⚠️ Cú pháp: <code>/tien_nga_daily_purchase [Mã Hộ]</code>\n\n"
                "<i>Ví dụ: <code>/tien_nga_daily_purchase X051</code></i>",
                parse_mode=ParseMode.HTML
            )
            return
            
        hoursehold_id = args[1].upper()
        
        from app.db.session import SessionLocal
        from app.models.business import Customers, CollectionPoint
        
        db = SessionLocal()
        try:
            customer = db.query(Customers).filter(Customers.hoursehold_id == hoursehold_id).first()
            if not customer:
                await message.reply_text(
                    f"⚠️ Không tìm thấy Khách hàng với mã hộ <b>{hoursehold_id}</b>.",
                    parse_mode=ParseMode.HTML
                )
                return
            
            cp_name = ""
            cp_id_str = ""
            if customer.collection_point_id:
                cp = db.query(CollectionPoint).filter(CollectionPoint.id == customer.collection_point_id).first()
                if cp:
                    cp_name = cp.collection_name
                    cp_id_str = str(cp.id)
            
            today_str = datetime.now().strftime("%d/%m/%Y")
            
            form_template = f"""<b>📋 FORM NHẬP MUA MỦ NGÀY</b>
Khách hàng: <b>{customer.fullname}</b> (<code>{hoursehold_id}</code>)
Xưởng: <b>{cp_name or 'Chưa có'}</b>

Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/tien_nga_daily_purchase
Mã Hộ: {hoursehold_id}
Mã Điểm Thu: {cp_id_str}
Ngày: {today_str}
Tuần: 
Trợ Giá: 0
Khối Lượng: 
Trừ Bì: 0
KL Thực Tế: 
Số Độ: 
Mủ Khô: 
Đơn Giá: 
Giá Hỗ Trợ: 0
Thành Tiền: 
Đã Thanh Toán: 0
Lưu Sổ: 0
Tạm Ứng: 0</pre>

<i>Ghi chú: Số tiền ví dụ 424.080 hoặc 5.898.728,5</i>"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        except Exception as e:
            LogError(f"Error fetching customer for daily purchase: {e}", LogType.SYSTEM_STATUS)
            await message.reply_text("❌ Lỗi hệ thống.", parse_mode=ParseMode.HTML)
        finally:
            db.close()
        return

    # Parse form data (nhiều dòng)
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    hoursehold_id = data.get("Mã Hộ", "").strip().upper()
    if not hoursehold_id:
        await message.reply_text("⚠️ <b>Mã Hộ</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    cp_id = data.get("Mã Điểm Thu", "").strip()
    ngay_str = data.get("Ngày", "").strip()
    
    if not ngay_str:
        await message.reply_text("⚠️ <b>Ngày</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return
    
    try:
        ngay = datetime.strptime(ngay_str, "%d/%m/%Y").date()
    except:
        await message.reply_text(
            "⚠️ Định dạng <b>Ngày</b> không hợp lệ. Vui lòng nhập DD/MM/YYYY.",
            parse_mode=ParseMode.HTML
        )
        return
    
    week = data.get("Tuần", "").strip()
    week_val = int(week) if week.isdigit() else ngay.isocalendar()[1]
    
    is_subsidized = int(parse_float_vn(data.get("Trợ Giá", "0")))
    weight = parse_float_vn(data.get("Khối Lượng", "0"))
    tare_weight = parse_float_vn(data.get("Trừ Bì", "0"))
    actual_weight = parse_float_vn(data.get("KL Thực Tế", "0"))
    degree = parse_float_vn(data.get("Số Độ", "0"))
    dry_rubber = parse_float_vn(data.get("Mủ Khô", "0"))
    unit_price = parse_float_vn(data.get("Đơn Giá", "0"))
    subsidy_price = parse_float_vn(data.get("Giá Hỗ Trợ", "0"))
    total_amount = parse_float_vn(data.get("Thành Tiền", "0"))
    paid_amount = parse_float_vn(data.get("Đã Thanh Toán", "0"))
    saved_amount = parse_float_vn(data.get("Lưu Sổ", "0"))
    advance_amount = parse_float_vn(data.get("Tạm Ứng", "0"))

    # Auto-calculate nếu không điền
    if actual_weight == 0 and weight > 0:
        actual_weight = weight - tare_weight
    if dry_rubber == 0 and actual_weight > 0 and degree > 0:
        dry_rubber = round(actual_weight * degree / 100, 2)
    if subsidy_price == 0 and unit_price > 0:
        subsidy_price = unit_price + is_subsidized
    if total_amount == 0 and dry_rubber > 0 and subsidy_price > 0:
        total_amount = round(dry_rubber * subsidy_price, 0)

    from app.db.session import SessionLocal
    from app.models.business import DailyPurchases, Customers
    import uuid as uuid_lib
    
    db = SessionLocal()
    try:
        # Verify customer exists
        customer = db.query(Customers).filter(Customers.hoursehold_id == hoursehold_id).first()
        if not customer:
            await message.reply_text(
                f"⚠️ Mã hộ <b>{hoursehold_id}</b> không tồn tại trong hệ thống.",
                parse_mode=ParseMode.HTML
            )
            return
        
        new_purchase = DailyPurchases(
            id=uuid_lib.uuid4(),
            hoursehold_id=hoursehold_id,
            collection_point_id=cp_id if cp_id else customer.collection_point_id,
            week=week_val,
            day=ngay,
            is_subsidized=is_subsidized,
            weight=weight,
            tare_weight=tare_weight,
            actual_weight=actual_weight,
            degree=degree,
            dry_rubber=dry_rubber,
            unit_price=unit_price,
            subsidy_price=subsidy_price,
            total_amount=total_amount,
            paid_amount=paid_amount,
            saved_amount=saved_amount,
            advance_amount=advance_amount,
            is_checked=False
        )
        db.add(new_purchase)
        db.commit()
        
        def fmt_vn(val):
            if val is None: return "0"
            try:
                return f"{val:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                return str(val)
        
        def fmt_money(val):
            if val is None: return "0 đ"
            try:
                return f"{int(val):,} đ".replace(",", ".")
            except:
                return str(val)
        
        LogInfo(f"[TienNga] Created daily purchase for '{hoursehold_id}' on {ngay_str} by user {message.from_user.id}", LogType.SYSTEM_STATUS)
        
        await message.reply_text(
            f"✅ <b>NHẬP MUA MỦ THÀNH CÔNG</b>\n\n"
            f"<b>Mã Hộ:</b> {hoursehold_id}\n"
            f"<b>Tên KH:</b> {customer.fullname}\n"
            f"<b>Ngày:</b> {ngay_str}\n"
            f"<b>Tuần:</b> {week_val}\n"
            f"<b>Khối Lượng:</b> {fmt_vn(weight)} kg\n"
            f"<b>Khối Lượng Thực Tế:</b> {fmt_vn(actual_weight)} kg\n"
            f"<b>Số Độ:</b> {fmt_vn(degree)}%\n"
            f"<b>Mủ Khô:</b> {fmt_vn(dry_rubber)} kg\n"
            f"<b>Trợ Giá:</b> {fmt_money(is_subsidized)}\n"
            f"<b>Đơn Giá:</b> {fmt_money(unit_price)}\n"
            f"<b>Giá Hỗ Trợ:</b> {fmt_money(subsidy_price)}\n"
            f"<b>Thành Tiền:</b> <code>{fmt_money(total_amount)}</code>\n"
            f"<b>Đã Thanh Toán:</b> {fmt_money(paid_amount)}\n"
            f"<b>Tạm Ứng:</b> {fmt_money(advance_amount)}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LogError(f"Error creating daily purchase: {e}", LogType.SYSTEM_STATUS)
        db.rollback()
        await message.reply_text("❌ Có lỗi xảy ra khi lưu dữ liệu.", parse_mode=ParseMode.HTML)
    finally:
        db.close()


# --- Xuất báo cáo (Export Info) ---
@bot.on_message(filters.command(["tien_nga_export_info"]) | filters.regex(r"^@\w+\s+/tien_nga_export_info\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ncc")
async def tien_nga_export_info_handler(client, message: Message) -> None:
    # Check for custom date arguments
    args = message.text.strip().split()
    time_preset = ""
    
    if len(args) == 3:
        try:
            start = datetime.strptime(args[1], "%d/%m/%Y").date()
            end = datetime.strptime(args[2], "%d/%m/%Y").date()
            time_preset = f"_time_c_{start.strftime('%d%m%y')}_{end.strftime('%d%m%y')}"
        except:
            await message.reply_text("⚠️ Định dạng ngày không hợp lệ. Vui lòng nhập DD/MM/YYYY.\nVí dụ: <code>/tien_nga_export_info 01/05/2025 15/05/2025</code>", parse_mode=ParseMode.HTML)
            return

    # If time_preset is set, we bypass the time-selection menu and embed the time into the module callbacks
    cb_ncc = f"tn_exp_ncc{time_preset}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Nhà cung cấp", callback_data=cb_ncc),
         InlineKeyboardButton("Kinh doanh", callback_data="tn_exp_dummy")],
        [InlineKeyboardButton("Nhân sự", callback_data="tn_exp_dummy"),
         InlineKeyboardButton("Thành phẩm", callback_data="tn_exp_dummy")],
        [InlineKeyboardButton("Đối tác", callback_data="tn_exp_dummy")]
    ])
    
    msg_text = "<b>TRUNG TÂM XUẤT BÁO CÁO Tiến Nga</b>\n\n"
    if time_preset:
        msg_text += f"🗓 Chế độ Tùy chọn ngày: <b>{args[1]} - {args[2]}</b>\n"
    
    msg_text += "Vui lòng chọn module báo cáo tương ứng:"
    
    await message.reply_text(
        msg_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# --- Xử lý Callback Xuất Báo Cáo ---
@bot.on_callback_query(filters.regex(r"^tn_exp_"))
async def tien_nga_export_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    
    if data == "tn_exp_main":
        # Quay lại menu chính
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Nhà cung cấp", callback_data="tn_exp_ncc"),
             InlineKeyboardButton("Kinh doanh", callback_data="tn_exp_dummy")],
            [InlineKeyboardButton("Nhân sự", callback_data="tn_exp_dummy"),
             InlineKeyboardButton("Thành phẩm", callback_data="tn_exp_dummy")],
            [InlineKeyboardButton("Đối tác", callback_data="tn_exp_dummy")]
        ])
        await callback_query.message.edit_text(
            "<b>TRUNG TÂM XUẤT BÁO CÁO Tiến Nga</b>\n\n"
            "Vui lòng chọn module báo cáo tương ứng:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        
    elif data == "tn_exp_cancel":
        await callback_query.message.delete()
        
    elif data == "tn_exp_ncc":
        # Menu chọn Date Range cho Nhà Cung Cấp
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("7 ngày", callback_data="tn_exp_ncc_time_7d"),
             InlineKeyboardButton("14 ngày", callback_data="tn_exp_ncc_time_14d"),
             InlineKeyboardButton("21 ngày", callback_data="tn_exp_ncc_time_21d")],
            [InlineKeyboardButton("1 tháng", callback_data="tn_exp_ncc_time_1m"),
             InlineKeyboardButton("1 quý", callback_data="tn_exp_ncc_time_1q")],
            [InlineKeyboardButton("2 quý", callback_data="tn_exp_ncc_time_2q"),
             InlineKeyboardButton("1 năm", callback_data="tn_exp_ncc_time_1y")],
            [InlineKeyboardButton("Năm trước", callback_data="tn_exp_ncc_time_py")],
            [InlineKeyboardButton("Quay lại", callback_data="tn_exp_main"),
             InlineKeyboardButton("Hủy", callback_data="tn_exp_cancel")]
        ])
        await callback_query.message.edit_text(
            "<b>BÁO CÁO [NHÀ CUNG CẤP]</b>\n\n"
            "Vui lòng chọn chu kỳ dữ liệu. Hoặc nếu muốn khoảng thời gian tùy thích, hãy sử dụng lệnh:\n"
            "<code>/tien_nga_export_info DD/MM/YYYY DD/MM/YYYY</code>\n"
            "<i>(Ví dụ: /tien_nga_export_info 01/05/2025 10/05/2025)</i>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        
    elif data.startswith("tn_exp_ncc_time_"):
        # Lấy được time được chọn
        time_code = data[len("tn_exp_ncc_time_"):]
        
        # Menu chọn Loại Nhà cung cấp cho chu kỳ đó
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Nhà cung cấp Mủ", callback_data=f"tn_exp_ncc_mu_{time_code}")],
            [InlineKeyboardButton("Nhà cung cấp Cũi", callback_data=f"tn_exp_dummy")],
            [InlineKeyboardButton("Nhà cung cấp Acid", callback_data=f"tn_exp_dummy")],
            [InlineKeyboardButton("Quay lại", callback_data="tn_exp_ncc"),
             InlineKeyboardButton("Hủy", callback_data="tn_exp_cancel")]
        ])
        await callback_query.message.edit_text(
            f"<b>CHUYÊN MỤC NHÀ CUNG CẤP</b>\n\n"
            f"Bạn muốn xuất báo cáo cho nguồn cấp nào?",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        
    elif data.startswith("tn_exp_ncc_mu_"):
        time_code = data[len("tn_exp_ncc_mu_"):]
        from app.db.session import SessionLocal
        from app.models.business import CollectionPoint
        db = SessionLocal()
        try:
            points = db.query(CollectionPoint).all()
            buttons = []
            buttons.append([InlineKeyboardButton("Báo cáo tổng", callback_data=f"tn_exp_rall_{time_code}")])
            for p in points:
                short_id = str(p.id)[:8]
                buttons.append([InlineKeyboardButton(p.collection_name, callback_data=f"tn_exp_rcp_{short_id}_{time_code}")])
            buttons.append([InlineKeyboardButton("Chưa phân xưởng", callback_data=f"tn_exp_rnon_{time_code}")])
            
            buttons.append([
                InlineKeyboardButton("Quay lại", callback_data=f"tn_exp_ncc_time_{time_code}"),
                InlineKeyboardButton("Hủy", callback_data="tn_exp_cancel")
            ])
            markup = InlineKeyboardMarkup(buttons)
            await callback_query.message.edit_text(
                "<b>CHỌN ĐIỂM THU MUA (XƯỞNG)</b>\n\nBạn muốn xem báo cáo của Xưởng nào?",
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            LogError(f"Error fetching points: {e}", LogType.SYSTEM_STATUS)
            await callback_query.answer("Lỗi hệ thống.", show_alert=True)
        finally:
            db.close()

    elif data.startswith("tn_exp_rall_") or data.startswith("tn_exp_rnon_") or data.startswith("tn_exp_rcp_"):
        await callback_query.message.edit_text("⏳ <i>Đang tính toán dữ liệu, vui lòng chờ...</i>", parse_mode=ParseMode.HTML)
        
        # parse the time_code and mode
        if data.startswith("tn_exp_rall_"):
            mode = "all"
            target_id = None
            time_code = data[len("tn_exp_rall_"):]
        elif data.startswith("tn_exp_rnon_"):
            mode = "none"
            target_id = None
            time_code = data[len("tn_exp_rnon_"):]
        else:
            mode = "cp"
            # tn_exp_rcp_12345678_...
            parts = data.split("_", 4)
            target_id = parts[3]
            time_code = parts[4]
            
        today = datetime.now().date()
        start_date = today
        end_date = today
        
        if time_code == "7d":
            start_date = today - timedelta(days=7)
        elif time_code == "14d":
            start_date = today - timedelta(days=14)
        elif time_code == "21d":
            start_date = today - timedelta(days=21)
        elif time_code == "1m":
            start_date = today - timedelta(days=30)
        elif time_code == "1q":
            start_date = today - timedelta(days=90)
        elif time_code == "2q":
            start_date = today - timedelta(days=180)
        elif time_code == "1y":
            start_date = today - timedelta(days=365)
        elif time_code == "py":
            last_year = today.year - 1
            start_date = datetime(last_year, 1, 1).date()
            end_date = datetime(last_year, 12, 31).date()
        elif time_code.startswith("c_"):
            parts = time_code.split("_")
            if len(parts) == 3:
                try:
                    start_date = datetime.strptime(parts[1], "%d%m%y").date()
                    end_date = datetime.strptime(parts[2], "%d%m%y").date()
                except:
                    pass
            
        from app.db.session import SessionLocal
        from app.models.business import DailyPurchases, CollectionPoint, Customers
        from sqlalchemy import func, String
        db = SessionLocal()
        try:
            def format_vn_currency(value):
                try:
                    return f"{int(value):,} đ".replace(",", ".")
                except:
                    return "0 đ"
                    
            def format_vn_float(value):
                try:
                    return f"{value:,.1f} kg".replace(",", "X").replace(".", ",").replace("X", ".")
                except:
                    return "0.0 kg"

            # Query base filter
            base_query = db.query(DailyPurchases).filter(
                DailyPurchases.day >= start_date,
                DailyPurchases.day <= end_date
            )

            # Apply mode filter
            cp_entity = None
            if mode == "none":
                base_query = base_query.filter(DailyPurchases.collection_point_id == None)
            elif mode == "cp":
                # Find the actual cp to filter
                cp_entity = db.query(CollectionPoint).filter(CollectionPoint.id.cast(String).startswith(target_id)).first()
                if cp_entity:
                    base_query = base_query.filter(DailyPurchases.collection_point_id == cp_entity.id)
                else:
                    base_query = base_query.filter(DailyPurchases.collection_point_id == None)

            if mode == "all":
                # Aggregate Total Info
                total_stats = db.query(
                    func.sum(DailyPurchases.actual_weight).label('total_weight'),
                    func.sum(DailyPurchases.total_amount).label('total_amount')
                ).filter(
                    DailyPurchases.day >= start_date,
                    DailyPurchases.day <= end_date
                ).first()
                
                t_weight = total_stats.total_weight or 0.0
                t_amount = total_stats.total_amount or 0.0
                
                # Aggregate By Collection Point (Xưởng)
                cp_stats = db.query(
                    CollectionPoint.collection_name,
                    func.sum(DailyPurchases.actual_weight).label('weight'),
                    func.sum(DailyPurchases.total_amount).label('amount')
                ).outerjoin(
                    CollectionPoint, CollectionPoint.id == DailyPurchases.collection_point_id
                ).filter(
                    DailyPurchases.day >= start_date,
                    DailyPurchases.day <= end_date
                ).group_by(
                    CollectionPoint.collection_name
                ).all()

                report = f"<b>BÁO CÁO THU MUA MỦ TỔNG HỢP</b>\n"
                if time_code == "py":
                    report += f"<b>Năm trước ({start_date.year})</b>\n\n"
                else:
                    report += f"<b>Từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}</b>\n\n"
                    
                report += f"<b>TỔNG CỘNG HỆ THỐNG:</b>\n"
                report += f"- Khối lượng thực: <b>{format_vn_float(t_weight)}</b>\n"
                report += f"- Thành tiền: <b>{format_vn_currency(t_amount)}</b>\n\n"
                
                if cp_stats:
                    report += f"<b>CHI TIẾT THEO TỪNG XƯỞNG:</b>\n"
                    for cp in cp_stats:
                        cp_w = cp.weight or 0.0
                        cp_a = cp.amount or 0.0
                        name = cp.collection_name or "Chưa phân xưởng"
                        report += f"<b>{name}</b>:\n"
                        report += f"  • Khối lượng: {format_vn_float(cp_w)}\n"
                        report += f"  • Thành tiền: {format_vn_currency(cp_a)}\n\n"
                else:
                    report += "<i>Không phát sinh dữ liệu mua mủ trong chu kỳ này.</i>\n"
                
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("Quay lại", callback_data=f"tn_exp_ncc_mu_{time_code}")]])
                await callback_query.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb)

            else:
                # MODE CP OR NONE (Report By Xưởng detailed by Hoursehold)
                target_name = cp_entity.collection_name if cp_entity else "Chưa phân xưởng"

                # Aggregate Total Info for this specific point
                total_stats = base_query.with_entities(
                    func.sum(DailyPurchases.actual_weight).label('total_weight'),
                    func.sum(DailyPurchases.total_amount).label('total_amount')
                ).first()
                
                t_weight = total_stats.total_weight or 0.0
                t_amount = total_stats.total_amount or 0.0

                # Aggregate by hoursehold_id
                hh_stats = base_query.with_entities(
                    DailyPurchases.hoursehold_id,
                    func.sum(DailyPurchases.actual_weight).label('weight'),
                    func.sum(DailyPurchases.total_amount).label('amount')
                ).group_by(
                    DailyPurchases.hoursehold_id
                ).all()

                if time_code == "py":
                    timeframe_str = f"Năm trước ({start_date.year})"
                else:
                    timeframe_str = f"Từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}"
                    
                records = []
                if hh_stats:
                    for hh in hh_stats:
                        hh_id = hh.hoursehold_id or "Không rõ mã hộ"
                        hh_w = hh.weight or 0.0
                        hh_a = hh.amount or 0.0
                        
                        cust = db.query(Customers).filter(Customers.hoursehold_id == hh_id).first()
                        cust_name = cust.fullname if cust else ""
                        
                        records.append({
                            "id": hh_id,
                            "name": cust_name,
                            "weight": format_vn_float(hh_w),
                            "amount": format_vn_currency(hh_a)
                        })

                from bot.utils.report_generator import generate_report_image
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("Quay lại", callback_data=f"tn_exp_ncc_mu_{time_code}")]])
                
                if records:
                    buf = await generate_report_image(
                        target_name=target_name.upper(),
                        timeframe=timeframe_str,
                        total_weight=format_vn_float(t_weight),
                        total_amount=format_vn_currency(t_amount),
                        records=records
                    )
                    cap = f"<b>BÁO CÁO THU MUA: {target_name.upper()}</b>\n{timeframe_str}\n\nTổng KL: <b>{format_vn_float(t_weight)}</b>\nTổng Tiền: <b>{format_vn_currency(t_amount)}</b>"
                    await callback_query.message.delete()
                    await client.send_document(chat_id=callback_query.message.chat.id, document=buf, caption=cap, parse_mode=ParseMode.HTML, reply_markup=kb)
                else:
                    report = f"<b>BÁO CÁO THU MUA: {target_name.upper()}</b>\n{timeframe_str}\n\n<i>Không phát sinh dữ liệu mua mủ tại xưởng này trong chu kỳ.</i>\n"
                    await callback_query.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb)

        except Exception as e:
            import traceback
            LogError(f"[TienNga] Error export mu: {traceback.format_exc()}", LogType.SYSTEM_STATUS)
            await callback_query.message.edit_text("❌ Có lỗi xảy ra khi truy vấn dữ liệu.", parse_mode=ParseMode.HTML)
        finally:
            db.close()
            
    elif data == "tn_exp_dummy":
        await callback_query.answer("🚀 Nhánh module này sẽ được phát triển tiếp sau nhé!", show_alert=True)


# ===================== THỐNG KÊ ĐÃ THANH TOÁN (Paid Amount) =====================

@bot.on_message(filters.command(["tien_nga_paid_amount", "tien_nga_da_thanh_toan"]) | filters.regex(r"^@\w+\s+/(tien_nga_paid_amount|tien_nga_da_thanh_toan)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ncc")
async def tien_nga_paid_amount_handler(client, message: Message) -> None:
    """Bước 1: Hiển thị button chọn khoảng thời gian hoặc nhận ngày tùy chọn."""
    args = message.text.strip().split()
    time_preset = ""

    # /tien_nga_paid_amount MÃ_HỘ DD/MM/YYYY DD/MM/YYYY
    if len(args) == 4:
        hh_id = args[1].upper()
        try:
            start = datetime.strptime(args[2], "%d/%m/%Y").date()
            end = datetime.strptime(args[3], "%d/%m/%Y").date()
        except Exception:
            await message.reply_text(
                "⚠️ Định dạng không hợp lệ.\nVí dụ: <code>/tien_nga_paid_amount X001 01/05/2025 15/05/2025</code>",
                parse_mode=ParseMode.HTML
            )
            return

        from app.db.session import SessionLocal
        from app.models.business import DailyPurchases, Customers, CollectionPoint
        from sqlalchemy import func
        db = SessionLocal()
        try:
            def fmt_vn(val):
                try:
                    return f"{int(val):,} đ".replace(",", ".")
                except:
                    return "0 đ"

            customer = db.query(Customers).filter(Customers.hoursehold_id == hh_id).first()
            cust_name = customer.fullname if customer else "Không rõ"
            cp_name = ""
            if customer and customer.collection_point_id:
                cp = db.query(CollectionPoint).filter(CollectionPoint.id == customer.collection_point_id).first()
                cp_name = cp.collection_name if cp else ""

            stats = db.query(
                func.sum(DailyPurchases.paid_amount).label("paid"),
                func.sum(DailyPurchases.total_amount).label("total"),
                func.sum(DailyPurchases.saved_amount).label("saved"),
                func.sum(DailyPurchases.advance_amount).label("advance"),
                func.sum(DailyPurchases.actual_weight).label("weight"),
                func.count(DailyPurchases.id).label("cnt")
            ).filter(
                DailyPurchases.hoursehold_id == hh_id,
                DailyPurchases.day >= start,
                DailyPurchases.day <= end
            ).first()

            paid = stats.paid or 0
            total = stats.total or 0
            saved = stats.saved or 0
            advance = stats.advance or 0
            weight = stats.weight or 0
            cnt = stats.cnt or 0

            report = (
                f"<b>THỐNG KÊ ĐÃ THANH TOÁN - HỘ DÂN</b>\n"
                f"🗓 <b>{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}</b>\n\n"
                f"<b>Mã Hộ:</b> <code>{hh_id}</code>\n"
                f"<b>Tên KH:</b> {cust_name}\n"
                f"<b>Xưởng:</b> {cp_name or 'N/A'}\n"
                f"{'━' * 20}\n"
                f"<b>Số lượt mua:</b> <code>{cnt}</code>\n"
                f"<b>Tổng KL thực tế:</b> <code>{weight:,.1f} kg</code>\n"
                f"<b>Tổng thành tiền:</b> <code>{fmt_vn(total)}</code>\n"
                f"<b>Đã thanh toán:</b> <code>{fmt_vn(paid)}</code>\n"
                f"<b>Lưu sổ:</b> <code>{fmt_vn(saved)}</code>\n"
                f"<b>Tạm ứng:</b> <code>{fmt_vn(advance)}</code>\n"
                f"{'━' * 20}\n"
                f"<b>Còn lại:</b> <code>{fmt_vn(total - paid - saved - advance)}</code>"
            )

            if cnt == 0:
                report = (
                    f"<b>THỐNG KÊ ĐÃ THANH TOÁN - HỘ DÂN</b>\n"
                    f"🗓 <b>{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}</b>\n\n"
                    f"<b>Mã Hộ:</b> <code>{hh_id}</code> | {cust_name}\n\n"
                    f"<i>Không có dữ liệu mua mủ trong khoảng thời gian này.</i>"
                )

            await message.reply_text(report, parse_mode=ParseMode.HTML)
        except Exception as e:
            LogError(f"[PaidAmount] Error hh search: {e}", LogType.SYSTEM_STATUS)
            await message.reply_text("❌ Có lỗi xảy ra.", parse_mode=ParseMode.HTML)
        finally:
            db.close()
        return

    if len(args) == 3:
        try:
            start = datetime.strptime(args[1], "%d/%m/%Y").date()
            end = datetime.strptime(args[2], "%d/%m/%Y").date()
            time_preset = f"c_{start.strftime('%d%m%y')}_{end.strftime('%d%m%y')}"
        except Exception:
            await message.reply_text(
                "⚠️ Định dạng ngày không hợp lệ.\nVí dụ: <code>/tien_nga_paid_amount 01/05/2025 15/05/2025</code>",
                parse_mode=ParseMode.HTML
            )
            return

    if time_preset:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Tất cả (Tổng hợp)", callback_data=f"tn_pa_all_{time_preset}")],
            [InlineKeyboardButton("Từng Xưởng (Chi tiết)", callback_data=f"tn_pa_sel_{time_preset}")],
            [InlineKeyboardButton("Hủy", callback_data="tn_pa_cancel")]
        ])
        await message.reply_text(
            f"<b>THỐNG KÊ ĐÃ THANH TOÁN</b>\n"
            f"🗓 <b>{args[1]} - {args[2]}</b>\n\n"
            f"Chọn phạm vi hiển thị:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Hôm nay", callback_data="tn_pa_time_0d"),
             InlineKeyboardButton("7 Ngày", callback_data="tn_pa_time_7d"),
             InlineKeyboardButton("14 Ngày", callback_data="tn_pa_time_14d")],
            [InlineKeyboardButton("21 Ngày", callback_data="tn_pa_time_21d"),
             InlineKeyboardButton("1 Tháng", callback_data="tn_pa_time_1m"),
             InlineKeyboardButton("1 Quý", callback_data="tn_pa_time_1q")],
            [InlineKeyboardButton("2 Quý", callback_data="tn_pa_time_2q"),
             InlineKeyboardButton("1 Năm", callback_data="tn_pa_time_1y"),
             InlineKeyboardButton("Năm trước", callback_data="tn_pa_time_py")],
            [InlineKeyboardButton("Hủy", callback_data="tn_pa_cancel")]
        ])
        await message.reply_text(
            "<b>THỐNG KÊ ĐÃ THANH TOÁN</b>\n\n"
            "Vui lòng chọn khoảng thời gian: \n"
            "Hoặc nhập: <code>/tien_nga_paid_amount DD/MM/YYYY DD/MM/YYYY</code> \n"
            "Hoặc nhập: <code>/tien_nga_paid_amount [MÃ_HỘ] DD/MM/YYYY DD/MM/YYYY</code>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )


@bot.on_callback_query(filters.regex(r"^tn_pa_"))
async def tien_nga_paid_amount_callback(client, callback_query: CallbackQuery):
    data = callback_query.data

    if data == "tn_pa_cancel":
        await callback_query.message.delete()
        return

    # ── Bước 2: Đã chọn time range → hiển thị "Tất cả" / "Từng xưởng" ──
    if data.startswith("tn_pa_time_"):
        time_code = data[len("tn_pa_time_"):]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Tất cả (Tổng hợp)", callback_data=f"tn_pa_all_{time_code}")],
            [InlineKeyboardButton("Từng Xưởng (Chi tiết)", callback_data=f"tn_pa_sel_{time_code}")],
            [InlineKeyboardButton("Quay lại", callback_data="tn_pa_back_time"),
             InlineKeyboardButton("Hủy", callback_data="tn_pa_cancel")]
        ])
        await callback_query.message.edit_text(
            "<b>THỐNG KÊ ĐÃ THANH TOÁN</b>\n\n"
            "Chọn phạm vi hiển thị:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        return

    # ── Quay lại chọn thời gian ──
    if data == "tn_pa_back_time":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Hôm nay", callback_data="tn_pa_time_0d"),
             InlineKeyboardButton("7 Ngày", callback_data="tn_pa_time_7d"),
             InlineKeyboardButton("14 Ngày", callback_data="tn_pa_time_14d")],
            [InlineKeyboardButton("21 Ngày", callback_data="tn_pa_time_21d"),
             InlineKeyboardButton("1 Tháng", callback_data="tn_pa_time_1m"),
             InlineKeyboardButton("1 Quý", callback_data="tn_pa_time_1q")],
            [InlineKeyboardButton("2 Quý", callback_data="tn_pa_time_2q"),
             InlineKeyboardButton("1 Năm", callback_data="tn_pa_time_1y"),
             InlineKeyboardButton("Năm trước", callback_data="tn_pa_time_py")],
            [InlineKeyboardButton("Hủy", callback_data="tn_pa_cancel")]
        ])
        await callback_query.message.edit_text(
            "<b>THỐNG KÊ ĐÃ THANH TOÁN</b>\n\n"
            "Vui lòng chọn khoảng thời gian:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        return

    # ── Chọn từng xưởng: hiển thị danh sách ──
    if data.startswith("tn_pa_sel_"):
        time_code = data[len("tn_pa_sel_"):]
        from app.db.session import SessionLocal
        from app.models.business import CollectionPoint
        db = SessionLocal()
        try:
            points = db.query(CollectionPoint).all()
            buttons = []
            for p in points:
                short_id = str(p.id)[:8]
                buttons.append([InlineKeyboardButton(p.collection_name, callback_data=f"tn_pa_cp_{short_id}_{time_code}")])
            buttons.append([
                InlineKeyboardButton("Quay lại", callback_data=f"tn_pa_time_{time_code}"),
                InlineKeyboardButton("Hủy", callback_data="tn_pa_cancel")
            ])
            markup = InlineKeyboardMarkup(buttons)
            await callback_query.message.edit_text(
                "<b>CHỌN XƯỞNG</b>\n\nBạn muốn xem thống kê thanh toán của Xưởng nào?",
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            LogError(f"Error listing CPs for paid_amount: {e}", LogType.SYSTEM_STATUS)
            await callback_query.answer("Lỗi hệ thống.", show_alert=True)
        finally:
            db.close()
        return

    # ── Helper: tính date range từ time_code ──
    def _parse_time_range(time_code):
        today = datetime.now().date()
        start_date = today
        end_date = today
        label = "Hôm nay"

        if time_code == "0d":
            label = "Hôm nay"
        elif time_code == "7d":
            start_date = today - timedelta(days=7)
            label = "7 ngày gần nhất"
        elif time_code == "14d":
            start_date = today - timedelta(days=14)
            label = "14 ngày gần nhất"
        elif time_code == "21d":
            start_date = today - timedelta(days=21)
            label = "21 ngày gần nhất"
        elif time_code == "1m":
            start_date = today - timedelta(days=30)
            label = "1 tháng gần nhất"
        elif time_code == "1q":
            start_date = today - timedelta(days=90)
            label = "1 quý gần nhất"
        elif time_code == "2q":
            start_date = today - timedelta(days=180)
            label = "2 quý gần nhất"
        elif time_code == "1y":
            start_date = today - timedelta(days=365)
            label = "1 năm gần nhất"
        elif time_code == "py":
            last_year = today.year - 1
            start_date = datetime(last_year, 1, 1).date()
            end_date = datetime(last_year, 12, 31).date()
            label = f"Năm trước ({last_year})"
        elif time_code.startswith("c_"):
            parts = time_code.split("_")
            if len(parts) == 3:
                try:
                    start_date = datetime.strptime(parts[1], "%d%m%y").date()
                    end_date = datetime.strptime(parts[2], "%d%m%y").date()
                    label = f"Tùy chọn ({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})"
                except Exception:
                    pass
        return start_date, end_date, label

    # ── Bước 3a: TẤT CẢ → Tổng hợp text ──
    if data.startswith("tn_pa_all_"):
        time_code = data[len("tn_pa_all_"):]
        start_date, end_date, time_label = _parse_time_range(time_code)

        await callback_query.message.edit_text("⏳ <i>Đang tính toán dữ liệu...</i>", parse_mode=ParseMode.HTML)

        from app.db.session import SessionLocal
        from app.models.business import DailyPurchases, CollectionPoint
        from sqlalchemy import func
        db = SessionLocal()
        try:
            def fmt_vn(val):
                try:
                    return f"{int(val):,} đ".replace(",", ".")
                except:
                    return "0 đ"

            # Tổng toàn hệ thống
            total = db.query(
                func.sum(DailyPurchases.paid_amount).label("paid")
            ).filter(
                DailyPurchases.day >= start_date,
                DailyPurchases.day <= end_date
            ).first()
            total_paid = total.paid or 0

            # Theo từng xưởng
            cp_stats = db.query(
                CollectionPoint.collection_name,
                func.sum(DailyPurchases.paid_amount).label("paid"),
                func.count(DailyPurchases.id).label("cnt")
            ).outerjoin(
                CollectionPoint, CollectionPoint.id == DailyPurchases.collection_point_id
            ).filter(
                DailyPurchases.day >= start_date,
                DailyPurchases.day <= end_date
            ).group_by(
                CollectionPoint.collection_name
            ).order_by(
                func.sum(DailyPurchases.paid_amount).desc()
            ).all()

            report = (
                f"<b>THỐNG KÊ ĐÃ THANH TOÁN</b>\n"
                f"<b>{time_label}</b>\n"
                f"<i>Từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}</i>\n\n"
                f"<b>TỔNG ĐÃ THANH TOÁN:</b> <code>{fmt_vn(total_paid)}</code>\n"
                f"{'━' * 30}\n\n"
                f"<b>CHI TIẾT THEO TỪNG XƯỞNG:</b>\n\n"
            )

            if cp_stats:
                for idx, cp in enumerate(cp_stats, 1):
                    name = cp.collection_name or "Chưa phân xưởng"
                    paid = cp.paid or 0
                    cnt = cp.cnt or 0
                    pct = (paid / total_paid * 100) if total_paid > 0 else 0
                    report += (
                        f"<b>{idx}. {name}</b>\n"
                        f"   Đã thanh toán: <code>{fmt_vn(paid)}</code>\n"
                        f"   Tỉ lệ: <code>{pct:.1f}%</code> | Số lượt: <code>{cnt}</code>\n\n"
                    )
            else:
                report += "<i>Không có dữ liệu trong khoảng thời gian này.</i>\n"

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Quay lại", callback_data=f"tn_pa_time_{time_code}"),
                 InlineKeyboardButton("Hủy", callback_data="tn_pa_cancel")]
            ])
            await callback_query.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb)

        except Exception as e:
            import traceback
            LogError(f"[PaidAmount] Error all: {traceback.format_exc()}", LogType.SYSTEM_STATUS)
            await callback_query.message.edit_text("❌ Có lỗi xảy ra.", parse_mode=ParseMode.HTML)
        finally:
            db.close()
        return

    # ── Bước 3b: TỪNG XƯỞNG → Tạo ảnh báo cáo ──
    if data.startswith("tn_pa_cp_"):
        # tn_pa_cp_12345678_7d
        parts = data.split("_", 4)
        target_id = parts[3]
        time_code = parts[4]
        start_date, end_date, time_label = _parse_time_range(time_code)

        await callback_query.message.edit_text("⏳ <i>Đang tạo báo cáo thanh toán...</i>", parse_mode=ParseMode.HTML)

        from app.db.session import SessionLocal
        from app.models.business import DailyPurchases, CollectionPoint, Customers
        from sqlalchemy import func, String
        db = SessionLocal()
        try:
            def fmt_vn(val):
                try:
                    return f"{int(val):,} đ".replace(",", ".")
                except:
                    return "0 đ"

            def fmt_weight(val):
                try:
                    return f"{val:,.1f} kg".replace(",", "X").replace(".", ",").replace("X", ".")
                except:
                    return "0,0 kg"

            # Find collection point
            cp_entity = db.query(CollectionPoint).filter(
                CollectionPoint.id.cast(String).startswith(target_id)
            ).first()

            if not cp_entity:
                await callback_query.message.edit_text("⚠️ Không tìm thấy Xưởng.", parse_mode=ParseMode.HTML)
                return

            target_name = cp_entity.collection_name

            # Total paid for this CP
            total_stats = db.query(
                func.sum(DailyPurchases.paid_amount).label("paid"),
                func.sum(DailyPurchases.actual_weight).label("weight")
            ).filter(
                DailyPurchases.day >= start_date,
                DailyPurchases.day <= end_date,
                DailyPurchases.collection_point_id == cp_entity.id
            ).first()

            t_paid = total_stats.paid or 0
            t_weight = total_stats.weight or 0

            # Aggregate by household
            hh_stats = db.query(
                DailyPurchases.hoursehold_id,
                func.sum(DailyPurchases.paid_amount).label("paid"),
                func.sum(DailyPurchases.actual_weight).label("weight")
            ).filter(
                DailyPurchases.day >= start_date,
                DailyPurchases.day <= end_date,
                DailyPurchases.collection_point_id == cp_entity.id
            ).group_by(
                DailyPurchases.hoursehold_id
            ).order_by(
                func.sum(DailyPurchases.paid_amount).desc()
            ).all()

            timeframe_str = f"{time_label}\n{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

            records = []
            for hh in hh_stats:
                hh_id = hh.hoursehold_id or "N/A"
                hh_paid = hh.paid or 0
                hh_w = hh.weight or 0

                cust = db.query(Customers).filter(Customers.hoursehold_id == hh_id).first()
                cust_name = cust.fullname if cust else ""

                records.append({
                    "id": hh_id,
                    "name": cust_name,
                    "weight": fmt_weight(hh_w),
                    "amount": fmt_vn(hh_paid)
                })

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Quay lại", callback_data=f"tn_pa_sel_{time_code}"),
                 InlineKeyboardButton("Hủy", callback_data="tn_pa_cancel")]
            ])

            if records:
                from bot.utils.paid_report_generator import generate_paid_report_image
                buf = await generate_paid_report_image(
                    target_name=target_name.upper(),
                    timeframe=timeframe_str,
                    total_weight=fmt_weight(t_weight),
                    total_paid=fmt_vn(t_paid),
                    records=records
                )

                cap = (
                    f"<b>ĐÃ THANH TOÁN: {target_name.upper()}</b>\n"
                    f"{time_label}\n\n"
                    f"Tổng KL: <b>{fmt_weight(t_weight)}</b>\n"
                    f"Tổng Đã TT: <b>{fmt_vn(t_paid)}</b>\n"
                    f"Số hộ: <b>{len(records)}</b>"
                )
                chat_id = callback_query.message.chat.id
                await callback_query.message.delete()
                await client.send_document(
                    chat_id=chat_id,
                    document=buf,
                    caption=cap,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            else:
                await callback_query.message.edit_text(
                    f"<b>ĐÃ THANH TOÁN: {target_name.upper()}</b>\n"
                    f"{time_label}\n\n"
                    f"<i>Không phát sinh thanh toán tại xưởng này trong chu kỳ.</i>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )

        except Exception as e:
            import traceback
            LogError(f"[PaidAmount] Error cp: {traceback.format_exc()}", LogType.SYSTEM_STATUS)
            try:
                await callback_query.message.edit_text("❌ Có lỗi xảy ra.", parse_mode=ParseMode.HTML)
            except Exception:
                await client.send_message(chat_id=callback_query.message.chat.id, text="❌ Có lỗi xảy ra.")
        finally:
            db.close()
        return


# ===================== THỐNG KÊ LƯU SỔ (Save Amount) =====================

@bot.on_message(filters.command(["tien_nga_save_amount", "tien_nga_luu_so"]) | filters.regex(r"^@\w+\s+/(tien_nga_save_amount|tien_nga_luu_so)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
@require_custom_title("super_main", "main_ncc")
async def tien_nga_save_amount_handler(client, message: Message) -> None:
    """Bước 1: Hiển thị button chọn khoảng thời gian hoặc nhận ngày tùy chọn."""
    args = message.text.strip().split()
    time_preset = ""

    # /tien_nga_save_amount MÃ_HỘ DD/MM/YYYY DD/MM/YYYY
    if len(args) == 4:
        hh_id = args[1].upper()
        try:
            start = datetime.strptime(args[2], "%d/%m/%Y").date()
            end = datetime.strptime(args[3], "%d/%m/%Y").date()
        except Exception:
            await message.reply_text(
                "⚠️ Định dạng không hợp lệ.\nVí dụ: <code>/tien_nga_save_amount X001 01/05/2025 15/05/2025</code>",
                parse_mode=ParseMode.HTML
            )
            return

        from app.db.session import SessionLocal
        from app.models.business import DailyPurchases, Customers, CollectionPoint
        from sqlalchemy import func
        db = SessionLocal()
        try:
            def fmt_vn(val):
                try:
                    return f"{int(val):,} đ".replace(",", ".")
                except:
                    return "0 đ"

            customer = db.query(Customers).filter(Customers.hoursehold_id == hh_id).first()
            cust_name = customer.fullname if customer else "Không rõ"
            cp_name = ""
            if customer and customer.collection_point_id:
                cp = db.query(CollectionPoint).filter(CollectionPoint.id == customer.collection_point_id).first()
                cp_name = cp.collection_name if cp else ""

            stats = db.query(
                func.sum(DailyPurchases.saved_amount).label("saved"),
                func.sum(DailyPurchases.total_amount).label("total"),
                func.sum(DailyPurchases.paid_amount).label("paid"),
                func.sum(DailyPurchases.advance_amount).label("advance"),
                func.sum(DailyPurchases.actual_weight).label("weight"),
                func.count(DailyPurchases.id).label("cnt")
            ).filter(
                DailyPurchases.hoursehold_id == hh_id,
                DailyPurchases.day >= start,
                DailyPurchases.day <= end
            ).first()

            saved = stats.saved or 0
            total = stats.total or 0
            paid = stats.paid or 0
            advance = stats.advance or 0
            weight = stats.weight or 0
            cnt = stats.cnt or 0

            report = (
                f"<b>THỐNG KÊ LƯU SỔ - HỘ DÂN</b>\n"
                f"🗓 <b>{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}</b>\n\n"
                f"<b>Mã Hộ:</b> <code>{hh_id}</code>\n"
                f"<b>Tên KH:</b> {cust_name}\n"
                f"<b>Xưởng:</b> {cp_name or 'N/A'}\n"
                f"{'━' * 30}\n"
                f"<b>Số lượt mua:</b> <code>{cnt}</code>\n"
                f"<b>Tổng KL thực tế:</b> <code>{weight:,.1f} kg</code>\n"
                f"<b>Tổng thành tiền:</b> <code>{fmt_vn(total)}</code>\n"
                f"<b>Lưu sổ:</b> <code>{fmt_vn(saved)}</code>\n"
                f"<b>Đã thanh toán:</b> <code>{fmt_vn(paid)}</code>\n"
                f"<b>Tạm ứng:</b> <code>{fmt_vn(advance)}</code>\n"
                f"{'━' * 30}\n"
                f"<b>Còn lại:</b> <code>{fmt_vn(total - paid - saved - advance)}</code>"
            )

            if cnt == 0:
                report = (
                    f"<b>THỐNG KÊ LƯU SỔ - HỘ DÂN</b>\n"
                    f"🗓 <b>{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}</b>\n\n"
                    f"<b>Mã Hộ:</b> <code>{hh_id}</code> | {cust_name}\n\n"
                    f"<i>Không có dữ liệu trong khoảng thời gian này.</i>"
                )

            await message.reply_text(report, parse_mode=ParseMode.HTML)
        except Exception as e:
            LogError(f"[SaveAmount] Error hh search: {e}", LogType.SYSTEM_STATUS)
            await message.reply_text("❌ Có lỗi xảy ra.", parse_mode=ParseMode.HTML)
        finally:
            db.close()
        return

    if len(args) == 3:
        try:
            start = datetime.strptime(args[1], "%d/%m/%Y").date()
            end = datetime.strptime(args[2], "%d/%m/%Y").date()
            time_preset = f"c_{start.strftime('%d%m%y')}_{end.strftime('%d%m%y')}"
        except Exception:
            await message.reply_text(
                "⚠️ Định dạng ngày không hợp lệ.\nVí dụ: <code>/tien_nga_save_amount 01/05/2025 15/05/2025</code>",
                parse_mode=ParseMode.HTML
            )
            return

    if time_preset:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Tất cả (Tổng hợp)", callback_data=f"tn_sa_all_{time_preset}")],
            [InlineKeyboardButton("Từng Xưởng (Chi tiết)", callback_data=f"tn_sa_sel_{time_preset}")],
            [InlineKeyboardButton("Hủy", callback_data="tn_sa_cancel")]
        ])
        await message.reply_text(
            f"<b>THỐNG KÊ LƯU SỔ</b>\n"
            f"🗓 <b>{args[1]} - {args[2]}</b>\n\n"
            f"Chọn phạm vi hiển thị:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Hôm nay", callback_data="tn_sa_time_0d"),
             InlineKeyboardButton("7 Ngày", callback_data="tn_sa_time_7d"),
             InlineKeyboardButton("14 Ngày", callback_data="tn_sa_time_14d")],
            [InlineKeyboardButton("21 Ngày", callback_data="tn_sa_time_21d"),
             InlineKeyboardButton("1 Tháng", callback_data="tn_sa_time_1m"),
             InlineKeyboardButton("1 Quý", callback_data="tn_sa_time_1q")],
            [InlineKeyboardButton("2 Quý", callback_data="tn_sa_time_2q"),
             InlineKeyboardButton("1 Năm", callback_data="tn_sa_time_1y"),
             InlineKeyboardButton("Năm trước", callback_data="tn_sa_time_py")],
            [InlineKeyboardButton("Hủy", callback_data="tn_sa_cancel")]
        ])
        await message.reply_text(
            "<b>THỐNG KÊ LƯU SỔ</b>\n\n"
            "Vui lòng chọn khoảng thời gian: \n"
            "Hoặc nhập: <code>/tien_nga_save_amount DD/MM/YYYY DD/MM/YYYY</code> \n"
            "Hoặc nhập: <code>/tien_nga_save_amount [MÃ_HỘ] DD/MM/YYYY DD/MM/YYYY</code>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )


@bot.on_callback_query(filters.regex(r"^tn_sa_"))
async def tien_nga_save_amount_callback(client, callback_query: CallbackQuery):
    data = callback_query.data

    if data == "tn_sa_cancel":
        await callback_query.message.delete()
        return

    # ── Bước 2: Đã chọn time range → hiển thị "Tất cả" / "Từng xưởng" ──
    if data.startswith("tn_sa_time_"):
        time_code = data[len("tn_sa_time_"):]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Tất cả (Tổng hợp)", callback_data=f"tn_sa_all_{time_code}")],
            [InlineKeyboardButton("Từng Xưởng (Chi tiết)", callback_data=f"tn_sa_sel_{time_code}")],
            [InlineKeyboardButton("Quay lại", callback_data="tn_sa_back_time"),
             InlineKeyboardButton("Hủy", callback_data="tn_sa_cancel")]
        ])
        await callback_query.message.edit_text(
            "<b>THỐNG KÊ LƯU SỔ</b>\n\n"
            "Chọn phạm vi hiển thị:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        return

    # ── Quay lại chọn thời gian ──
    if data == "tn_sa_back_time":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Hôm nay", callback_data="tn_sa_time_0d"),
             InlineKeyboardButton("7 Ngày", callback_data="tn_sa_time_7d"),
             InlineKeyboardButton("14 Ngày", callback_data="tn_sa_time_14d")],
            [InlineKeyboardButton("21 Ngày", callback_data="tn_sa_time_21d"),
             InlineKeyboardButton("1 Tháng", callback_data="tn_sa_time_1m"),
             InlineKeyboardButton("1 Quý", callback_data="tn_sa_time_1q")],
            [InlineKeyboardButton("2 Quý", callback_data="tn_sa_time_2q"),
             InlineKeyboardButton("1 Năm", callback_data="tn_sa_time_1y"),
             InlineKeyboardButton("Năm trước", callback_data="tn_sa_time_py")],
            [InlineKeyboardButton("Hủy", callback_data="tn_sa_cancel")]
        ])
        await callback_query.message.edit_text(
            "<b>THỐNG KÊ LƯU SỔ</b>\n\n"
            "Vui lòng chọn khoảng thời gian:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        return

    # ── Chọn từng xưởng: hiển thị danh sách ──
    if data.startswith("tn_sa_sel_"):
        time_code = data[len("tn_sa_sel_"):]
        from app.db.session import SessionLocal
        from app.models.business import CollectionPoint
        db = SessionLocal()
        try:
            points = db.query(CollectionPoint).all()
            buttons = []
            for p in points:
                short_id = str(p.id)[:8]
                buttons.append([InlineKeyboardButton(p.collection_name, callback_data=f"tn_sa_cp_{short_id}_{time_code}")])
            buttons.append([
                InlineKeyboardButton("Quay lại", callback_data=f"tn_sa_time_{time_code}"),
                InlineKeyboardButton("Hủy", callback_data="tn_sa_cancel")
            ])
            markup = InlineKeyboardMarkup(buttons)
            await callback_query.message.edit_text(
                "<b>CHỌN XƯỞNG</b>\n\nBạn muốn xem thống kê lưu sổ của Xưởng nào?",
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            LogError(f"Error listing CPs for save_amount: {e}", LogType.SYSTEM_STATUS)
            await callback_query.answer("Lỗi hệ thống.", show_alert=True)
        finally:
            db.close()
        return

    # ── Helper: tính date range từ time_code ──
    def _parse_time_range_sa(time_code):
        today = datetime.now().date()
        start_date = today
        end_date = today
        label = "Hôm nay"

        if time_code == "0d":
            label = "Hôm nay"
        elif time_code == "7d":
            start_date = today - timedelta(days=7)
            label = "7 ngày gần nhất"
        elif time_code == "14d":
            start_date = today - timedelta(days=14)
            label = "14 ngày gần nhất"
        elif time_code == "21d":
            start_date = today - timedelta(days=21)
            label = "21 ngày gần nhất"
        elif time_code == "1m":
            start_date = today - timedelta(days=30)
            label = "1 tháng gần nhất"
        elif time_code == "1q":
            start_date = today - timedelta(days=90)
            label = "1 quý gần nhất"
        elif time_code == "2q":
            start_date = today - timedelta(days=180)
            label = "2 quý gần nhất"
        elif time_code == "1y":
            start_date = today - timedelta(days=365)
            label = "1 năm gần nhất"
        elif time_code == "py":
            last_year = today.year - 1
            start_date = datetime(last_year, 1, 1).date()
            end_date = datetime(last_year, 12, 31).date()
            label = f"Năm trước ({last_year})"
        elif time_code.startswith("c_"):
            parts = time_code.split("_")
            if len(parts) == 3:
                try:
                    start_date = datetime.strptime(parts[1], "%d%m%y").date()
                    end_date = datetime.strptime(parts[2], "%d%m%y").date()
                    label = f"Tùy chọn ({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})"
                except Exception:
                    pass
        return start_date, end_date, label

    # ── Bước 3a: TẤT CẢ → Tổng hợp text ──
    if data.startswith("tn_sa_all_"):
        time_code = data[len("tn_sa_all_"):]
        start_date, end_date, time_label = _parse_time_range_sa(time_code)

        await callback_query.message.edit_text("⏳ <i>Đang tính toán dữ liệu...</i>", parse_mode=ParseMode.HTML)

        from app.db.session import SessionLocal
        from app.models.business import DailyPurchases, CollectionPoint
        from sqlalchemy import func
        db = SessionLocal()
        try:
            def fmt_vn(val):
                try:
                    return f"{int(val):,} đ".replace(",", ".")
                except:
                    return "0 đ"

            # Tổng toàn hệ thống
            total = db.query(
                func.sum(DailyPurchases.saved_amount).label("saved")
            ).filter(
                DailyPurchases.day >= start_date,
                DailyPurchases.day <= end_date
            ).first()
            total_saved = total.saved or 0

            # Theo từng xưởng
            cp_stats = db.query(
                CollectionPoint.collection_name,
                func.sum(DailyPurchases.saved_amount).label("saved"),
                func.count(DailyPurchases.id).label("cnt")
            ).outerjoin(
                CollectionPoint, CollectionPoint.id == DailyPurchases.collection_point_id
            ).filter(
                DailyPurchases.day >= start_date,
                DailyPurchases.day <= end_date
            ).group_by(
                CollectionPoint.collection_name
            ).order_by(
                func.sum(DailyPurchases.saved_amount).desc()
            ).all()

            report = (
                f"<b>THỐNG KÊ LƯU SỔ</b>\n"
                f"<b>{time_label}</b>\n"
                f"<i>Từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}</i>\n\n"
                f"<b>TỔNG LƯU SỔ:</b> <code>{fmt_vn(total_saved)}</code>\n"
                f"{'━' * 30}\n\n"
                f"<b>CHI TIẾT THEO TỪNG XƯỞNG:</b>\n\n"
            )

            if cp_stats:
                for idx, cp in enumerate(cp_stats, 1):
                    name = cp.collection_name or "Chưa phân xưởng"
                    saved = cp.saved or 0
                    cnt = cp.cnt or 0
                    pct = (saved / total_saved * 100) if total_saved > 0 else 0
                    report += (
                        f"<b>{idx}. {name}</b>\n"
                        f"   Lưu sổ: <code>{fmt_vn(saved)}</code>\n"
                        f"   Tỉ lệ: <code>{pct:.1f}%</code> | Số lượt: <code>{cnt}</code>\n\n"
                    )
            else:
                report += "<i>Không có dữ liệu trong khoảng thời gian này.</i>\n"

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Quay lại", callback_data=f"tn_sa_time_{time_code}"),
                 InlineKeyboardButton("Hủy", callback_data="tn_sa_cancel")]
            ])
            await callback_query.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb)

        except Exception as e:
            import traceback
            LogError(f"[SaveAmount] Error all: {traceback.format_exc()}", LogType.SYSTEM_STATUS)
            await callback_query.message.edit_text("❌ Có lỗi xảy ra.", parse_mode=ParseMode.HTML)
        finally:
            db.close()
        return

    # ── Bước 3b: TỪNG XƯỞNG → Tạo ảnh báo cáo ──
    if data.startswith("tn_sa_cp_"):
        # tn_sa_cp_12345678_7d
        parts = data.split("_", 4)
        target_id = parts[3]
        time_code = parts[4]
        start_date, end_date, time_label = _parse_time_range_sa(time_code)

        await callback_query.message.edit_text("⏳ <i>Đang tạo báo cáo lưu sổ...</i>", parse_mode=ParseMode.HTML)

        from app.db.session import SessionLocal
        from app.models.business import DailyPurchases, CollectionPoint, Customers
        from sqlalchemy import func, String
        db = SessionLocal()
        try:
            def fmt_vn(val):
                try:
                    return f"{int(val):,} đ".replace(",", ".")
                except:
                    return "0 đ"

            def fmt_weight(val):
                try:
                    return f"{val:,.1f} kg".replace(",", "X").replace(".", ",").replace("X", ".")
                except:
                    return "0,0 kg"

            # Find collection point
            cp_entity = db.query(CollectionPoint).filter(
                CollectionPoint.id.cast(String).startswith(target_id)
            ).first()

            if not cp_entity:
                await callback_query.message.edit_text("⚠️ Không tìm thấy Xưởng.", parse_mode=ParseMode.HTML)
                return

            target_name = cp_entity.collection_name

            # Total saved for this CP
            total_stats = db.query(
                func.sum(DailyPurchases.saved_amount).label("saved"),
                func.sum(DailyPurchases.actual_weight).label("weight")
            ).filter(
                DailyPurchases.day >= start_date,
                DailyPurchases.day <= end_date,
                DailyPurchases.collection_point_id == cp_entity.id
            ).first()

            t_saved = total_stats.saved or 0
            t_weight = total_stats.weight or 0

            # Aggregate by household
            hh_stats = db.query(
                DailyPurchases.hoursehold_id,
                func.sum(DailyPurchases.saved_amount).label("saved"),
                func.sum(DailyPurchases.actual_weight).label("weight")
            ).filter(
                DailyPurchases.day >= start_date,
                DailyPurchases.day <= end_date,
                DailyPurchases.collection_point_id == cp_entity.id
            ).group_by(
                DailyPurchases.hoursehold_id
            ).order_by(
                func.sum(DailyPurchases.saved_amount).desc()
            ).all()

            timeframe_str = f"{time_label}\n{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

            records = []
            for hh in hh_stats:
                hh_id = hh.hoursehold_id or "N/A"
                hh_saved = hh.saved or 0
                hh_w = hh.weight or 0

                cust = db.query(Customers).filter(Customers.hoursehold_id == hh_id).first()
                cust_name = cust.fullname if cust else ""

                records.append({
                    "id": hh_id,
                    "name": cust_name,
                    "weight": fmt_weight(hh_w),
                    "amount": fmt_vn(hh_saved)
                })

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Quay lại", callback_data=f"tn_sa_sel_{time_code}"),
                 InlineKeyboardButton("Hủy", callback_data="tn_sa_cancel")]
            ])

            if records:
                from bot.utils.save_report_generator import generate_save_report_image
                buf = await generate_save_report_image(
                    target_name=target_name.upper(),
                    timeframe=timeframe_str,
                    total_weight=fmt_weight(t_weight),
                    total_saved=fmt_vn(t_saved),
                    records=records
                )

                cap = (
                    f"<b>LƯU SỔ: {target_name.upper()}</b>\n"
                    f"{time_label}\n\n"
                    f"Tổng KL: <b>{fmt_weight(t_weight)}</b>\n"
                    f"Tổng Lưu Sổ: <b>{fmt_vn(t_saved)}</b>\n"
                    f"Số hộ: <b>{len(records)}</b>"
                )
                chat_id = callback_query.message.chat.id
                await callback_query.message.delete()
                await client.send_document(
                    chat_id=chat_id,
                    document=buf,
                    caption=cap,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            else:
                await callback_query.message.edit_text(
                    f"<b>LƯU SỔ: {target_name.upper()}</b>\n"
                    f"{time_label}\n\n"
                    f"<i>Không phát sinh lưu sổ tại xưởng này trong chu kỳ.</i>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )

        except Exception as e:
            import traceback
            LogError(f"[SaveAmount] Error cp: {traceback.format_exc()}", LogType.SYSTEM_STATUS)
            try:
                await callback_query.message.edit_text("❌ Có lỗi xảy ra.", parse_mode=ParseMode.HTML)
            except Exception:
                await client.send_message(chat_id=callback_query.message.chat.id, text="❌ Có lỗi xảy ra.")
        finally:
            db.close()
        return


# ===================== GỬI TIN NHẮN (Send Message) =====================
# In-memory state for multi-select: {user_id: {"message_id": ..., "chat_id": ..., "selected": set(), "orig_msg": Message}}
_send_msg_state = {}

@bot.on_message(filters.command(["send_message"]) | filters.regex(r"^@\w+\s+/send_message\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("Tiến Nga")
@require_group_role("main")
# @require_custom_title("super_main", "main")
async def send_message_handler(client, message: Message) -> None:
    """
    /send_message [Nội dung]
    Gửi tin nhắn/ảnh/video đến các nhóm thành viên theo dự án.
    Nếu reply một tin nhắn thì nội dung reply sẽ được chuyển tiếp.
    """
    # Kiểm tra nội dung
    has_content = False
    text_content = ""
    
    # Lấy args sau lệnh
    first_line = message.text.strip().split("\n")[0] if message.text else ""
    all_text = message.text or message.caption or ""
    
    # Bỏ phần lệnh, lấy nội dung
    for cmd in ["send_message"]:
        pattern = f"/{cmd}"
        if pattern in all_text:
            idx = all_text.index(pattern) + len(pattern)
            text_content = all_text[idx:].strip()
            break
    
    # Check reply message
    reply_msg = message.reply_to_message
    
    if text_content:
        has_content = True
    elif reply_msg:
        has_content = True
    elif message.photo or message.video or message.document:
        has_content = True
    
    if not has_content:
        await message.reply_text(
            "⚠️ Vui lòng nhập nội dung hoặc reply một tin nhắn.\n\n"
            "Cú pháp:\n"
            "• <code>/send_message [Nội dung văn bản]</code>\n"
            "• Gửi ảnh/video kèm caption <code>/send_message</code>\n"
            "• Reply một tin nhắn rồi gõ <code>/send_message</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Lưu state
    user_id = message.from_user.id
    _send_msg_state[user_id] = {
        "text": text_content,
        "orig_msg": message,
        "reply_msg": reply_msg,
        "selected": set(),
    }
    
    # Hiển thị button chọn Dự án
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Tiến Nga", callback_data="sm_proj_tiennga")],
        [InlineKeyboardButton("Credit", callback_data="sm_proj_dummy"),
         InlineKeyboardButton("Rental", callback_data="sm_proj_dummy")],
        [InlineKeyboardButton("Ggomoonsin", callback_data="sm_proj_dummy"),
         InlineKeyboardButton("Other", callback_data="sm_proj_dummy")],
        [InlineKeyboardButton("Hủy", callback_data="sm_cancel")],
    ])
    
    preview = text_content[:100] + "..." if len(text_content) > 100 else text_content
    if reply_msg:
        preview = "[Reply tin nhắn]"
    elif message.photo:
        preview = f"[Ảnh] {preview}" if preview else "[Ảnh]"
    elif message.video:
        preview = f"[Video] {preview}" if preview else "[Video]"
    
    await message.reply_text(
        f"<b>GỬI TIN NHẮN ĐẾN NHÓM</b>\n\n"
        f"Nội dung: <i>{preview or '(không có text)'}</i>\n\n"
        f"Chọn Dự án:",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )


@bot.on_callback_query(filters.regex(r"^sm_"))
async def send_message_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "sm_cancel":
        _send_msg_state.pop(user_id, None)
        await callback_query.message.edit_text("❌ Đã hủy gửi tin nhắn.", parse_mode=ParseMode.HTML)
        return
    
    state = _send_msg_state.get(user_id)
    if not state:
        await callback_query.answer("⚠️ Phiên đã hết hạn. Vui lòng gõ lại /send_message", show_alert=True)
        return
    
    # === Chọn Dự án: Tiến Nga ===
    if data == "sm_proj_tiennga":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Gửi tất cả nhóm", callback_data="sm_tn_all")],
            [InlineKeyboardButton("Nhà cung cấp", callback_data="sm_tn_ncc")],
            [InlineKeyboardButton("Kinh doanh", callback_data="sm_tn_dummy")],
            [InlineKeyboardButton("Nhân sự", callback_data="sm_tn_dummy")],
            [InlineKeyboardButton("QL Thành phẩm", callback_data="sm_tn_dummy")],
            [InlineKeyboardButton("QL Đối tác", callback_data="sm_tn_dummy")],
            [InlineKeyboardButton("Hủy", callback_data="sm_cancel"),
             InlineKeyboardButton("Quay lại", callback_data="sm_back_proj")],
        ])
        await callback_query.message.edit_text(
            "<b>DỰ ÁN: TIẾN NGA</b>\n\nChọn nhóm nhận tin:",
            parse_mode=ParseMode.HTML, reply_markup=kb
        )
    
    # === Quay lại chọn Dự án ===
    elif data == "sm_back_proj":
        state["selected"] = set()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Tiến Nga", callback_data="sm_proj_tiennga")],
            [InlineKeyboardButton("Credit", callback_data="sm_proj_dummy"),
             InlineKeyboardButton("Rental", callback_data="sm_proj_dummy")],
            [InlineKeyboardButton("Ggomoonsin", callback_data="sm_proj_dummy"),
             InlineKeyboardButton("Other", callback_data="sm_proj_dummy")],
            [InlineKeyboardButton("Hủy", callback_data="sm_cancel")],
        ])
        await callback_query.message.edit_text(
            "<b>GỬI TIN NHẮN ĐẾN NHÓM</b>\n\nChọn Dự án:",
            parse_mode=ParseMode.HTML, reply_markup=kb
        )
    
    # === Nhà cung cấp -> Multi-select sub-categories ===
    elif data == "sm_tn_ncc":
        state["selected"] = set()
        await _render_ncc_select(callback_query, state)
    
    # === Toggle NCC sub-category ===
    elif data.startswith("sm_tn_ncc_tog_"):
        ncc_key = data.replace("sm_tn_ncc_tog_", "")
        selected = state.get("selected", set())
        if ncc_key in selected:
            selected.discard(ncc_key)
        else:
            selected.add(ncc_key)
        state["selected"] = selected
        await _render_ncc_select(callback_query, state)
    
    # === Gửi đến NCC đã chọn ===
    elif data == "sm_tn_ncc_send":
        selected = state.get("selected", set())
        if not selected:
            await callback_query.answer("⚠️ Vui lòng chọn ít nhất 1 nhà cung cấp!", show_alert=True)
            return
        
        await callback_query.message.edit_text("⏳ <i>Đang gửi tin nhắn...</i>", parse_mode=ParseMode.HTML)
        
        # Map NCC keys to custom_titles
        ncc_map = {
            "mu": "member_ncc",
            "cui": "member_ncc_cui",
            "acid": "member_ncc_acid",
        }
        
        target_titles = [ncc_map[k] for k in selected if k in ncc_map]
        sent, failed = await _do_send_to_groups(client, state, "Tiến Nga", target_titles)
        
        _send_msg_state.pop(user_id, None)
        
        ncc_labels = {"mu": "Mủ", "cui": "Củi", "acid": "Acid"}
        selected_names = ", ".join(ncc_labels.get(k, k) for k in selected)
        
        await callback_query.message.edit_text(
            f"✅ <b>ĐÃ GỬI TIN NHẮN</b>\n\n"
            f"Nhóm: <b>NCC ({selected_names})</b>\n"
            f"Gửi thành công: <b>{sent}</b> nhóm\n"
            f"Thất bại: <b>{failed}</b> nhóm",
            parse_mode=ParseMode.HTML
        )
    
    # === Gửi tất cả nhóm Tiến Nga ===
    elif data == "sm_tn_all":
        await callback_query.message.edit_text("⏳ <i>Đang gửi tin nhắn đến tất cả nhóm...</i>", parse_mode=ParseMode.HTML)
        
        sent, failed = await _do_send_to_groups(client, state, "Tiến Nga", None)
        
        _send_msg_state.pop(user_id, None)
        
        await callback_query.message.edit_text(
            f"✅ <b>ĐÃ GỬI TIN NHẮN</b>\n\n"
            f"Nhóm: <b>Tất cả nhóm Tiến Nga</b>\n"
            f"Gửi thành công: <b>{sent}</b> nhóm\n"
            f"Thất bại: <b>{failed}</b> nhóm",
            parse_mode=ParseMode.HTML
        )
    
    # === Dummy buttons ===
    elif data == "sm_tn_dummy" or data == "sm_proj_dummy":
        await callback_query.answer("🚀 Nhánh này sẽ được phát triển tiếp sau!", show_alert=True)


async def _render_ncc_select(callback_query, state):
    """Render NCC multi-select buttons."""
    selected = state.get("selected", set())
    
    ncc_items = [
        ("mu", "Nhà cung cấp Mủ"),
        ("cui", "Nhà cung cấp Củi"),
        ("acid", "Nhà cung cấp Acid"),
    ]
    
    buttons = []
    for key, label in ncc_items:
        check = "✅" if key in selected else "⬜"
        buttons.append([InlineKeyboardButton(f"{check} {label}", callback_data=f"sm_tn_ncc_tog_{key}")])
    
    buttons.append([InlineKeyboardButton("Gửi", callback_data="sm_tn_ncc_send")])
    buttons.append([
        InlineKeyboardButton("Hủy", callback_data="sm_cancel"),
        InlineKeyboardButton("Quay lại", callback_data="sm_proj_tiennga"),
    ])
    
    selected_text = ", ".join(
        {"mu": "Mủ", "cui": "Củi", "acid": "Acid"}.get(k, k) for k in selected
    ) or "Chưa chọn"
    
    kb = InlineKeyboardMarkup(buttons)
    await callback_query.message.edit_text(
        f"<b>NHÀ CUNG CẤP</b>\n\n"
        f"Đã chọn: <b>{selected_text}</b>\n\n"
        f"Nhấn để chọn/bỏ chọn, sau đó nhấn <b>Gửi</b>:",
        parse_mode=ParseMode.HTML, reply_markup=kb
    )


async def _do_send_to_groups(client, state, project_name: str, target_titles: list = None):
    """
    Gửi tin nhắn/ảnh/video đến các nhóm member.
    target_titles=None -> gửi tất cả nhóm member trong dự án.
    Returns (sent_count, failed_count).
    """
    from app.db.session import SessionLocal
    from app.models.business import Projects
    from app.models.telegram import TelegramProjectMember
    
    db = SessionLocal()
    sent = 0
    failed = 0
    
    try:
        project = db.query(Projects).filter(Projects.project_name == project_name).first()
        if not project:
            return 0, 0
        
        query = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.project_id == project.id,
        )
        
        if target_titles:
            query = query.filter(TelegramProjectMember.custom_title.in_(target_titles))
        else:
            # Tất cả nhóm member (custom_title bắt đầu bằng member_)
            query = query.filter(TelegramProjectMember.custom_title.like("member_%"))
        
        members = query.all()
        chat_ids = list(set(m.chat_id for m in members))
        
        if not chat_ids:
            return 0, 0
        
        orig_msg = state.get("orig_msg")
        reply_msg = state.get("reply_msg")
        text_content = state.get("text", "")
        
        # Clean caption: remove /send_message command from original caption
        clean_caption = text_content
        if not clean_caption and orig_msg:
            raw_caption = orig_msg.caption or ""
            # Loại bỏ /send_message khỏi caption
            import re as _re
            clean_caption = _re.sub(r'/send_message\s*', '', raw_caption).strip()
        
        for chat_id in chat_ids:
            try:
                if reply_msg:
                    # Forward reply message
                    await reply_msg.forward(int(chat_id))
                elif orig_msg and orig_msg.photo:
                    await client.send_photo(
                        chat_id=int(chat_id),
                        photo=orig_msg.photo.file_id,
                        caption=clean_caption,
                        parse_mode=ParseMode.HTML
                    )
                elif orig_msg and orig_msg.video:
                    await client.send_video(
                        chat_id=int(chat_id),
                        video=orig_msg.video.file_id,
                        caption=clean_caption,
                        parse_mode=ParseMode.HTML
                    )
                elif orig_msg and orig_msg.document:
                    await client.send_document(
                        chat_id=int(chat_id),
                        document=orig_msg.document.file_id,
                        caption=clean_caption,
                        parse_mode=ParseMode.HTML
                    )
                elif text_content:
                    await client.send_message(
                        chat_id=int(chat_id),
                        text=text_content,
                        parse_mode=ParseMode.HTML
                    )
                sent += 1
            except Exception as e:
                LogError(f"[SendMsg] Failed to send to {chat_id}: {e}", LogType.SYSTEM_STATUS)
                failed += 1
    except Exception as e:
        LogError(f"[SendMsg] Error: {e}", LogType.SYSTEM_STATUS)
    finally:
        db.close()
    
    return sent, failed
