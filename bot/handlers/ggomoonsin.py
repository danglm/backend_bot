from pyrogram import filters
from bot.utils.enums import CustomTitle
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from bot.utils.bot import bot
from bot.utils.utils import check_command_target, require_user_type, require_project_name, require_custom_title
from bot.utils.enums import UserType
import re

# GGoMoonSin project handlers

# --- Thêm nhân viên ---
@bot.on_message(filters.command(["ggomoonsin_create_employee", "ggomoonsin_tao_nhan_vien"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_create_employee|ggomoonsin_tao_nhan_vien)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.SUPER_MAIN, CustomTitle.MAIN_HR)
async def ggomoonsin_create_employee_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_create_employee", "ggomoonsin_tao_nhan_vien"])
    if args is None: return

    from bot.utils.human_resource import handle_create_employee
    await handle_create_employee(client, message, "/ggomoonsin_create_employee")


# --- Cập nhật nhân viên ---
@bot.on_message(filters.command(["ggomoonsin_update_employee", "ggomoonsin_cap_nhat_nhan_vien"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_update_employee|ggomoonsin_cap_nhat_nhan_vien)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.SUPER_MAIN, CustomTitle.MAIN_HR)
async def ggomoonsin_update_employee_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_update_employee", "ggomoonsin_cap_nhat_nhan_vien"])
    if args is None: return

    from bot.utils.human_resource import handle_update_employee
    await handle_update_employee(client, message, "/ggomoonsin_update_employee")


# --- Xóa nhân viên (soft delete) ---
@bot.on_message(filters.command(["ggomoonsin_delete_employee", "ggomoonsin_xoa_nhan_vien"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_delete_employee|ggomoonsin_xoa_nhan_vien)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.SUPER_MAIN, CustomTitle.MAIN_HR)
async def ggomoonsin_delete_employee_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_delete_employee", "ggomoonsin_xoa_nhan_vien"])
    if args is None: return

    from bot.utils.human_resource import handle_delete_employee
    await handle_delete_employee(client, message, "/ggomoonsin_delete_employee")


# --- Chấm công (Check-in) ---
@bot.on_message(filters.command(["ggomoonsin_check_in", "ggomoonsin_cham_cong"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_check_in|ggomoonsin_cham_cong)\b"))
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.MEMBER_HR)
async def ggomoonsin_check_in_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_check_in", "ggomoonsin_cham_cong"])
    if args is None: return

    from bot.utils.human_resource import handle_check_in
    await handle_check_in(client, message, "/ggomoonsin_check_in")


# --- Tan ca (Check-out) ---
@bot.on_message(filters.command(["ggomoonsin_check_out", "ggomoonsin_tan_ca"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_check_out|ggomoonsin_tan_ca)\b"))
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.MEMBER_HR)
async def ggomoonsin_check_out_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_check_out", "ggomoonsin_tan_ca"])
    if args is None: return

    from bot.utils.human_resource import handle_check_out
    await handle_check_out(client, message, "/ggomoonsin_check_out")


# --- Xin nghỉ phép (Request Leave) ---
@bot.on_message(filters.command(["ggomoonsin_request_leave", "ggomoonsin_xin_nghi_phep"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_request_leave|ggomoonsin_xin_nghi_phep)\b"))
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.MEMBER_HR)
async def ggomoonsin_request_leave_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_request_leave", "ggomoonsin_xin_nghi_phep"])
    if args is None: return

    from bot.utils.human_resource import handle_request_leave
    await handle_request_leave(client, message, "/ggomoonsin_request_leave")


# --- Đăng ký tăng ca (Request Overtime) ---
@bot.on_message(filters.command(["ggomoonsin_request_overtime", "ggomoonsin_dang_ky_tang_ca"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_request_overtime|ggomoonsin_dang_ky_tang_ca)\b"))
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.MEMBER_HR)
async def ggomoonsin_request_overtime_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_request_overtime", "ggomoonsin_dang_ky_tang_ca"])
    if args is None: return

    from bot.utils.human_resource import handle_request_overtime
    await handle_request_overtime(client, message, "/ggomoonsin_request_overtime")


# --- Xem chấm công (List Check-in) ---
@bot.on_message(filters.command(["ggomoonsin_list_check_in", "ggomoonsin_xem_cham_cong"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_list_check_in|ggomoonsin_xem_cham_cong)\b"))
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.MEMBER_HR)
async def ggomoonsin_list_check_in_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_list_check_in", "ggomoonsin_xem_cham_cong"])
    if args is None: return

    from bot.utils.human_resource import handle_list_check_in
    await handle_list_check_in(client, message, "/ggomoonsin_list_check_in")


# --- Xem danh sách nghỉ phép (List Request Leave) ---
@bot.on_message(filters.command(["ggomoonsin_list_request_leave", "ggomoonsin_xem_nghi_phep"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_list_request_leave|ggomoonsin_xem_nghi_phep)\b"))
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.MEMBER_HR)
async def ggomoonsin_list_request_leave_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_list_request_leave", "ggomoonsin_xem_nghi_phep"])
    if args is None: return

    from bot.utils.human_resource import handle_list_request_leave
    await handle_list_request_leave(client, message, "/ggomoonsin_list_request_leave")


# --- Giao việc (Create Task) ---
@bot.on_message(filters.command(["ggomoonsin_create_task", "ggomoonsin_giao_viec"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_create_task|ggomoonsin_giao_viec)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.SUPER_MAIN, CustomTitle.MAIN_HR)
async def ggomoonsin_create_task_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_create_task", "ggomoonsin_giao_viec"])
    if args is None: return

    from bot.utils.human_resource import handle_create_task
    await handle_create_task(client, message, "/ggomoonsin_create_task")


# --- Xem danh sách task (List Tasks) ---
@bot.on_message(filters.command(["ggomoonsin_list_tasks", "ggomoonsin_xem_cong_viec"]) | filters.regex(r"^@\w+\s+/(ggomoonsin_list_tasks|ggomoonsin_xem_cong_viec)\b"))
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.MEMBER_HR)
async def ggomoonsin_list_tasks_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_list_tasks", "ggomoonsin_xem_cong_viec"])
    if args is None: return

    from bot.utils.human_resource import handle_list_tasks
    await handle_list_tasks(client, message, "/ggomoonsin_list_tasks")


# --- Hủy task (Reply /cancel vào tin nhắn task) ---
@bot.on_message(filters.command(["cancel", "huy_task"]) & filters.reply)
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.SUPER_MAIN, CustomTitle.MAIN_HR)
async def ggomoonsin_cancel_task_handler(client, message: Message) -> None:
    from bot.utils.human_resource import handle_cancel_task_reply
    await handle_cancel_task_reply(client, message)


# --- Xuất bảng lương (Export Payroll) ---
@bot.on_message(filters.command(["export_payroll", "ggomoonsin_xuat_luong", "ggomoonsin_export_payroll"]) | filters.regex(r"^@\w+\s+/(export_payroll|ggomoonsin_xuat_luong|ggomoonsin_export_payroll)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.SUPER_MAIN, CustomTitle.MAIN_HR)
async def ggomoonsin_export_payroll_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["export_payroll", "ggomoonsin_xuat_luong", "ggomoonsin_export_payroll"])
    if args is None: return

    from bot.utils.human_resource import handle_export_payroll
    # Re-construct message.text for the actual handler to parse args
    import re
    cmd = args[0] if args else "export_payroll"
    message.text = f"/{cmd} " + " ".join(args[1:]) if len(args) > 1 else f"/{cmd}"
    await handle_export_payroll(client, message, f"/{cmd}")


# --- Tạo lại bảng chấm công (Recreate Attendance Report) ---
@bot.on_message(filters.command(["ggomoonsin_recreate_attendance_report"]) | filters.regex(r"^@\w+\s+/ggomoonsin_recreate_attendance_report\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_project_name("GGoMoonSin")
@require_custom_title(CustomTitle.SUPER_MAIN, CustomTitle.MAIN_HR)
async def ggomoonsin_recreate_attendance_report_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["ggomoonsin_recreate_attendance_report"])
    if args is None: return

    from bot.utils.human_resource import handle_recreate_attendance_report
    import re
    cmd = args[0] if args else "ggomoonsin_recreate_attendance_report"
    message.text = f"/{cmd} " + " ".join(args[1:]) if len(args) > 1 else f"/{cmd}"
    await handle_recreate_attendance_report(client, message, f"/{cmd}")
