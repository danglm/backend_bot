"""
Menu nút bấm cho các lệnh Nhân sự — dùng chung Tiến Nga và Ggomoosin.

Mọi callback của HR nằm ở đây (không nằm trong bot/utils/human_resource.py, vì
file đó được import lazy nên decorator sẽ không đăng ký lúc bot khởi động).
Dự án được suy ra từ callback_query.message.chat.id, y như lệnh gốc — nên cùng
một bộ handler phục vụ cả hai dự án mà không cần nhét project vào callback_data.

Mỗi luồng có một prefix riêng (xem BẢNG PREFIX bên dưới) và tối đa 4 handler nền:
_p (phân trang), _s (chọn nhân viên), _noop (nút đếm trang), _x (hủy).

BẢNG PREFIX
    hrn  tạo nhân viên           hrp  xuất bảng lương
    hru  cập nhật nhân viên      hrr  tạo lại bảng chấm công
    hrd  xóa nhân viên           hra  danh sách chấm công
    hrt  giao việc               hrl  xuất danh sách lương
    hrk  danh sách công việc     hrv  danh sách nhân viên
"""

from dataclasses import dataclass
from functools import wraps
from typing import Callable, Optional

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.db.session import SessionLocal
from bot.utils import hr_picker as hp
from bot.utils.bot import bot
from bot.utils.enums import CustomTitle, UserType
from bot.utils.logger import LogError, LogType
from bot.utils.utils import (
    command_timeout,
    require_custom_title,
    require_group_role,
    require_user_type,
)

# Luồng nhiều bước (chọn NV -> chọn tháng -> xác nhận) rất dễ vượt 30 giây mặc
# định của command_timeout, nên nới rộng như form hợp đồng bên Rental.
HR_MENU_TIMEOUT = 600


# ══════════════════════════════════════════════════════════════
# Hạ tầng đăng ký handler
# ══════════════════════════════════════════════════════════════

def hr_callback(pattern: str):
    """
    Đăng ký một callback HR kèm đủ bộ decorator quyền và bọc try/except chung.

    Quyền giữ nguyên như lệnh gốc: Owner/Admin, nhóm main, custom title
    SUPER_MAIN hoặc MAIN_HR.
    """
    def decorator(func):
        @wraps(func)
        async def guarded(client, callback_query: CallbackQuery, *args, **kwargs):
            try:
                return await func(client, callback_query, *args, **kwargs)
            except Exception as e:
                LogError(f"Error in {func.__name__}: {e}", LogType.SYSTEM_STATUS)
                try:
                    await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
                except Exception:
                    pass

        return bot.on_callback_query(filters.regex(pattern))(
            require_user_type(UserType.OWNER, UserType.ADMIN)(
                require_group_role("main")(
                    require_custom_title(CustomTitle.SUPER_MAIN, CustomTitle.MAIN_HR)(
                        command_timeout(timeout_seconds=HR_MENU_TIMEOUT, auto_delete_cmd=True)(guarded)
                    )
                )
            )
        )
    return decorator


async def delete_menu(callback_query: CallbackQuery) -> None:
    """Xóa tin nhắn menu sau khi đã gửi kết quả bằng tin mới (idiom của Rental)."""
    try:
        await callback_query.message.delete()
    except Exception:
        pass


def register_common(prefix: str) -> None:
    """Đăng ký nút đếm trang và nút Hủy cho một prefix."""

    @hr_callback(rf"^{prefix}_noop$")
    async def _noop(client, callback_query: CallbackQuery):
        await callback_query.answer()

    @hr_callback(rf"^{prefix}_x$")
    async def _cancel(client, callback_query: CallbackQuery):
        await delete_menu(callback_query)


# ══════════════════════════════════════════════════════════════
# Luồng danh sách nhân viên
# ══════════════════════════════════════════════════════════════

@dataclass
class HRFlow:
    prefix: str
    title: str
    hint: str = "Chọn nhân viên:"
    # async (client, callback_query, employee, page) -> None
    on_select: Optional[Callable] = None
    # (employee|None) -> list[list[InlineKeyboardButton]]
    action_rows: Optional[Callable] = None
    # Hiện ô tick ✅/⬜ trên từng nút (chỉ luồng ở lại màn danh sách mới cần)
    show_selection: bool = False
    only_active: bool = True


async def render_list(
    callback_query: CallbackQuery,
    flow: HRFlow,
    page: int,
    selected_id: Optional[str] = None,
) -> None:
    """
    Vẽ lại màn danh sách nhân viên ở trang / lựa chọn cho trước.

    Lấy dữ liệu xong là TRẢ CONNECTION NGAY, rồi mới gọi Telegram. Handler của
    bot là code đồng bộ chạy trong event loop nên giữ connection xuyên qua một
    lệnh gọi mạng là cách nhanh nhất làm cạn pool và treo cả bot — xem chú thích
    ở app/db/session.py.
    """
    selected_id = selected_id or None

    db = SessionLocal()
    try:
        diagnostic = hp.project_employees_diagnostic(
            db, callback_query.message.chat.id, only_active=flow.only_active
        )
        employees = diagnostic["matched"]
        selected = next((e for e in employees if e.id == selected_id), None)
        text = markup = None
        if employees:
            text = hp.build_employee_header(
                employees, selected, flow.title, flow.hint, diagnostic
            )
            markup = hp.build_employee_keyboard(
                employees,
                page,
                flow.prefix,
                selected_id if flow.show_selection else None,
                flow.action_rows(selected) if flow.action_rows else None,
            )
    finally:
        db.close()

    if not employees:
        await callback_query.answer(
            "ℹ️ Không có nhân viên nào thuộc dự án này.", show_alert=True
        )
        return

    await hp.safe_edit(callback_query, text, markup)
    await callback_query.answer()


def register_employee_list(flow: HRFlow) -> None:
    """Đăng ký handler phân trang + chọn nhân viên cho một luồng."""

    @hr_callback(rf"^{flow.prefix}_p\|(\d+)\|(.*)$")
    async def _page(client, callback_query: CallbackQuery):
        page = int(callback_query.matches[0].group(1))
        selected_id = callback_query.matches[0].group(2) or None
        await render_list(callback_query, flow, page, selected_id)

    @hr_callback(rf"^{flow.prefix}_s\|([^|]+)\|(\d+)$")
    async def _select(client, callback_query: CallbackQuery):
        emp_id = callback_query.matches[0].group(1)
        page = int(callback_query.matches[0].group(2))

        db = SessionLocal()
        try:
            employee = hp.employee_in_project(db, callback_query.message.chat.id, emp_id)
        finally:
            db.close()

        # employee đã detach nhưng mọi cột đã nạp sẵn nên đọc thuộc tính vẫn an
        # toàn; on_select nào cần DB thì tự mở session của nó.
        if not employee:
            await callback_query.answer(
                "⚠️ Nhân viên này không thuộc dự án hiện tại.", show_alert=True
            )
            return

        if flow.on_select:
            await flow.on_select(client, callback_query, employee, page)
        else:
            await callback_query.answer()


# ══════════════════════════════════════════════════════════════
# Luồng chọn thời gian
# ══════════════════════════════════════════════════════════════

def register_month_flow(
    prefix: str,
    title: str,
    on_pick: Callable,
    allow_custom_period: bool = False,
) -> None:
    """
    Đăng ký các handler chọn tháng: quay lại lưới nhanh (_q), lưới 12 tháng (_g),
    và chốt tháng (_m). `on_pick` là async (client, callback_query, arg, month, year).
    """

    @hr_callback(rf"^{prefix}_q\|([^|]*)$")
    async def _quick(client, callback_query: CallbackQuery):
        arg = callback_query.matches[0].group(1)
        await hp.safe_edit(
            callback_query,
            hp.month_header(title, arg),
            hp.build_month_quick_keyboard(prefix, arg, allow_custom_period),
        )
        await callback_query.answer()

    @hr_callback(rf"^{prefix}_g\|([^|]*)\|(\d+)$")
    async def _grid(client, callback_query: CallbackQuery):
        arg = callback_query.matches[0].group(1)
        year = int(callback_query.matches[0].group(2))
        await hp.safe_edit(
            callback_query,
            hp.month_header(title, arg),
            hp.build_month_grid_keyboard(prefix, arg, year),
        )
        await callback_query.answer()

    @hr_callback(rf"^{prefix}_m\|([^|]*)\|(\d+)\|(\d+)$")
    async def _pick(client, callback_query: CallbackQuery):
        arg = callback_query.matches[0].group(1)
        month = int(callback_query.matches[0].group(2))
        year = int(callback_query.matches[0].group(3))
        await on_pick(client, callback_query, arg, month, year)


async def switch_to_month_menu(callback_query: CallbackQuery, prefix: str, title: str, arg: str,
                               allow_custom_period: bool = False) -> None:
    """Chuyển màn danh sách nhân viên sang màn chọn thời gian."""
    await hp.safe_edit(
        callback_query,
        hp.month_header(title, arg),
        hp.build_month_quick_keyboard(prefix, arg, allow_custom_period),
    )
    await callback_query.answer()


# ══════════════════════════════════════════════════════════════
# hrn — Tạo nhân viên
# ══════════════════════════════════════════════════════════════

async def _hrn_select(client, callback_query, employee, page):
    """Danh sách ở đây chỉ để tham khảo mã đã dùng; bấm vào chỉ xem nhanh."""
    full_name = f"{employee.last_name or ''} {employee.first_name or ''}".strip()
    await callback_query.answer(
        f"{employee.id} — {full_name}\nMã này đã được sử dụng.", show_alert=True
    )


FLOW_HRN = HRFlow(
    prefix="hrn",
    title="THÊM NHÂN VIÊN",
    hint="Danh sách nhân viên hiện có (để tránh trùng mã):",
    on_select=_hrn_select,
    action_rows=lambda _selected: [
        [InlineKeyboardButton("Thêm mới nhân viên", callback_data="hrn_add")]
    ],
    only_active=False,
)
register_employee_list(FLOW_HRN)
register_common("hrn")


@hr_callback(r"^hrn_add$")
async def hrn_add_callback(client, callback_query: CallbackQuery):
    """Mở form tạo nhân viên (form 55 trường giữ nguyên như cũ)."""
    from bot.utils.human_resource import EMPLOYEE_FORM_TEMPLATE

    db = SessionLocal()
    try:
        command = hp.project_command(db, callback_query.message.chat.id, "tao_nhan_vien")
    finally:
        db.close()

    await callback_query.message.reply_text(
        EMPLOYEE_FORM_TEMPLATE.format(cmd=command), parse_mode=ParseMode.HTML
    )
    await delete_menu(callback_query)
    await callback_query.answer()


# ══════════════════════════════════════════════════════════════
# hru — Cập nhật nhân viên
# ══════════════════════════════════════════════════════════════

async def _hru_select(client, callback_query, employee, page):
    from bot.utils.human_resource import _build_prefilled_update_form

    db = SessionLocal()
    try:
        command = hp.project_command(db, callback_query.message.chat.id, "cap_nhat_nhan_vien")
    finally:
        db.close()

    await callback_query.message.reply_text(
        _build_prefilled_update_form(employee, command), parse_mode=ParseMode.HTML
    )
    await delete_menu(callback_query)
    await callback_query.answer()


FLOW_HRU = HRFlow(
    prefix="hru",
    title="CẬP NHẬT NHÂN VIÊN",
    hint="Chọn nhân viên cần cập nhật:",
    on_select=_hru_select,
    only_active=False,
)
register_employee_list(FLOW_HRU)
register_common("hru")


# ══════════════════════════════════════════════════════════════
# hrd — Xóa nhân viên
# ══════════════════════════════════════════════════════════════

def build_delete_confirm(employee) -> tuple[str, InlineKeyboardMarkup]:
    """Màn xác nhận xóa — dùng lại callback del_emp_confirm / del_emp_cancel sẵn có."""
    full_name = f"{employee.last_name or ''} {employee.first_name or ''}".strip()
    text = (
        f"<b>XÁC NHẬN XÓA NHÂN VIÊN</b>\n\n"
        f"<b>Mã NV:</b> {employee.id}\n"
        f"<b>Họ tên:</b> {full_name} (@{employee.username or 'N/A'})\n"
        f"<b>Trạng thái hiện tại:</b> {employee.status or 'active'}\n\n"
        f"<i>Nhân viên sẽ được chuyển sang trạng thái <b>inactive</b> (nghỉ việc).\n"
        f"Thao tác này không xóa hoàn toàn khỏi hệ thống.</i>\n\n"
        f"Bạn có chắc chắn muốn thực hiện?"
    )
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Xác nhận", callback_data=f"del_emp_confirm|{employee.id}"),
        InlineKeyboardButton("Huỷ", callback_data=f"del_emp_cancel|{employee.id}"),
    ]])
    return text, markup


async def _hrd_select(client, callback_query, employee, page):
    if (employee.status or "") == "inactive":
        await callback_query.answer(
            f"⚠️ Nhân viên {employee.id} đã ở trạng thái inactive rồi.", show_alert=True
        )
        return

    text, markup = build_delete_confirm(employee)
    await hp.safe_edit(callback_query, text, markup)
    await callback_query.answer()


FLOW_HRD = HRFlow(
    prefix="hrd",
    title="XÓA NHÂN VIÊN",
    hint="Chọn nhân viên cần xóa:",
    on_select=_hrd_select,
)
register_employee_list(FLOW_HRD)
register_common("hrd")


# ══════════════════════════════════════════════════════════════
# hrt — Giao việc
# ══════════════════════════════════════════════════════════════

async def _hrt_select(client, callback_query, employee, page):
    from bot.utils.human_resource import TASK_FORM_TEMPLATE

    db = SessionLocal()
    try:
        command = hp.project_command(db, callback_query.message.chat.id, "giao_viec")
    finally:
        db.close()

    # Điền sẵn mã nhân viên vào ô "Người nhận" để khỏi phải gõ tay
    form = TASK_FORM_TEMPLATE.format(cmd=command).replace(
        "Người nhận: [mã nhân viên]", f"Người nhận: {employee.id}"
    )
    await callback_query.message.reply_text(form, parse_mode=ParseMode.HTML)
    await delete_menu(callback_query)
    await callback_query.answer()


FLOW_HRT = HRFlow(
    prefix="hrt",
    title="GIAO VIỆC",
    hint="Chọn nhân viên nhận việc:",
    on_select=_hrt_select,
)
register_employee_list(FLOW_HRT)
register_common("hrt")


# ══════════════════════════════════════════════════════════════
# hrk — Danh sách công việc
# ══════════════════════════════════════════════════════════════

async def _hrk_select(client, callback_query, employee, page):
    full_name = f"{employee.last_name or ''} {employee.first_name or ''}".strip()
    await hp.safe_edit(
        callback_query,
        f"<b>XEM CÔNG VIỆC NHÂN VIÊN</b>\n\n"
        f"Nhân viên: <b>{full_name}</b> (<code>{employee.id}</code>)\n\n"
        f"Xem công việc trong bao lâu gần đây?",
        hp.build_months_count_keyboard("hrk", employee.id),
    )
    await callback_query.answer()


FLOW_HRK = HRFlow(
    prefix="hrk",
    title="XEM CÔNG VIỆC NHÂN VIÊN",
    on_select=_hrk_select,
)
register_employee_list(FLOW_HRK)
register_common("hrk")


@hr_callback(r"^hrk_n\|([^|]+)\|(\d+)$")
async def hrk_months_callback(client, callback_query: CallbackQuery):
    from bot.utils.human_resource import execute_check_tasks

    emp_id = callback_query.matches[0].group(1)
    months = int(callback_query.matches[0].group(2))

    await callback_query.answer("⏳ Đang lấy danh sách công việc...")
    await execute_check_tasks(client, callback_query.message, emp_id, months)
    await delete_menu(callback_query)


# ══════════════════════════════════════════════════════════════
# hrp — Xuất bảng lương
# ══════════════════════════════════════════════════════════════

HRP_TITLE = "XUẤT BẢNG LƯƠNG"


async def _hrp_select(client, callback_query, employee, page):
    await switch_to_month_menu(callback_query, "hrp", HRP_TITLE, employee.id,
                               allow_custom_period=True)


async def _hrp_pick(client, callback_query: CallbackQuery, arg: str, month: int, year: int):
    from bot.utils.human_resource import execute_export_payroll

    start_date, end_date = hp.month_bounds(month, year)

    # Ghi Payroll + cộng dồn total_debt -> phải chặn bấm trùng TRƯỚC mọi await
    tag = f"hrp|{arg}|{month}|{year}"
    if not hp.hr_cb_claim(callback_query, tag):
        await callback_query.answer("⏳ Bảng lương này đang được xử lý.", show_alert=True)
        return

    await callback_query.answer("⏳ Đang tính toán và xuất bảng lương...")
    try:
        await execute_export_payroll(client, callback_query.message, arg, start_date, end_date)
    except Exception:
        hp.hr_cb_release(callback_query, tag)
        raise
    await delete_menu(callback_query)


FLOW_HRP = HRFlow(prefix="hrp", title=HRP_TITLE, on_select=_hrp_select)
register_employee_list(FLOW_HRP)
register_month_flow("hrp", HRP_TITLE, _hrp_pick, allow_custom_period=True)
register_common("hrp")


@hr_callback(r"^hrp_c\|([^|]+)$")
async def hrp_custom_period_callback(client, callback_query: CallbackQuery):
    """
    Kỳ tùy chọn: hiện lệnh mẫu để copy. Repo không có cơ chế chờ nhập liệu nên
    đây là cách gọn nhất mà không phải thêm trạng thái mới.
    """
    import datetime

    emp_id = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        command = hp.project_command(db, callback_query.message.chat.id, "xuat_luong")
    finally:
        db.close()

    today = datetime.date.today()
    prev_year, prev_month = hp.shift_month(today.year, today.month, -1)
    sample_start = datetime.date(prev_year, prev_month, 5)
    sample_end = datetime.date(today.year, today.month, 4)

    await hp.safe_edit(
        callback_query,
        f"<b>{HRP_TITLE} — KỲ TÙY CHỌN</b>\n\n"
        f"Nhân viên: <code>{emp_id}</code>\n\n"
        f"Sao chép lệnh dưới đây, sửa lại khoảng ngày rồi gửi:\n\n"
        f"<pre>{command} {emp_id} {sample_start.strftime('%d/%m/%Y')} - "
        f"{sample_end.strftime('%d/%m/%Y')}</pre>\n"
        f"<i>Kỳ được ghi sổ vào tháng bắt đầu của khoảng ngày.</i>",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("Quay lại", callback_data=f"hrp_q|{emp_id}")],
            [InlineKeyboardButton("Hủy", callback_data="hrp_x")],
        ]),
    )
    await callback_query.answer()


# ══════════════════════════════════════════════════════════════
# hrr — Tạo lại bảng chấm công
# ══════════════════════════════════════════════════════════════

HRR_TITLE = "TẠO LẠI BẢNG CHẤM CÔNG"


async def _hrr_select(client, callback_query, employee, page):
    await switch_to_month_menu(callback_query, "hrr", HRR_TITLE, employee.id)


async def _hrr_pick(client, callback_query: CallbackQuery, arg: str, month: int, year: int):
    from bot.utils.human_resource import execute_recreate_attendance

    await callback_query.answer("⏳ Đang tạo lại bảng chấm công...")
    await execute_recreate_attendance(client, callback_query.message, arg, month, year)
    await delete_menu(callback_query)


FLOW_HRR = HRFlow(prefix="hrr", title=HRR_TITLE, on_select=_hrr_select)
register_employee_list(FLOW_HRR)
register_month_flow("hrr", HRR_TITLE, _hrr_pick)
register_common("hrr")


# ══════════════════════════════════════════════════════════════
# hra — Danh sách chấm công (Excel)
# ══════════════════════════════════════════════════════════════

HRA_TITLE = "XUẤT DANH SÁCH CHẤM CÔNG"


async def _hra_select(client, callback_query, employee, page):
    await switch_to_month_menu(callback_query, "hra", HRA_TITLE, employee.id)


async def _hra_pick(client, callback_query: CallbackQuery, arg: str, month: int, year: int):
    from bot.utils.human_resource import execute_list_attendance_excel

    await callback_query.answer("⏳ Đang tạo file Excel chấm công...")
    await execute_list_attendance_excel(client, callback_query.message, arg, month, year)
    await delete_menu(callback_query)


FLOW_HRA = HRFlow(prefix="hra", title=HRA_TITLE, on_select=_hra_select)
register_employee_list(FLOW_HRA)
register_month_flow("hra", HRA_TITLE, _hra_pick)
register_common("hra")


# ══════════════════════════════════════════════════════════════
# hrl — Xuất danh sách lương (cả dự án, không cần chọn nhân viên)
# ══════════════════════════════════════════════════════════════

HRL_TITLE = "XUẤT DANH SÁCH LƯƠNG"


async def _hrl_pick(client, callback_query: CallbackQuery, arg: str, month: int, year: int):
    from bot.utils.human_resource import execute_list_payroll_excel

    await callback_query.answer("⏳ Đang tạo file Excel bảng lương...")
    await execute_list_payroll_excel(client, callback_query.message, month, year)
    await delete_menu(callback_query)


register_month_flow("hrl", HRL_TITLE, _hrl_pick)
register_common("hrl")


# ══════════════════════════════════════════════════════════════
# hrv — Danh sách nhân viên
# ══════════════════════════════════════════════════════════════

def _hrv_action_rows(selected):
    rows = []
    if selected is not None:
        rows.append([InlineKeyboardButton("Cập nhật nhân viên", callback_data=f"hrv_upd|{selected.id}")])
        rows.append([InlineKeyboardButton("Xóa nhân viên", callback_data=f"hrv_del|{selected.id}")])
    rows.append([InlineKeyboardButton("Xuất Excel danh sách", callback_data="hrv_xls")])
    return rows


async def _hrv_select(client, callback_query, employee, page):
    await render_list(callback_query, FLOW_HRV, page, employee.id)


FLOW_HRV = HRFlow(
    prefix="hrv",
    title="DANH SÁCH NHÂN VIÊN",
    hint="Chọn nhân viên để xem thao tác:",
    on_select=_hrv_select,
    action_rows=_hrv_action_rows,
    show_selection=True,
    only_active=False,
)
register_employee_list(FLOW_HRV)
register_common("hrv")


@hr_callback(r"^hrv_upd\|([^|]+)$")
async def hrv_update_callback(client, callback_query: CallbackQuery):
    from bot.utils.human_resource import _build_prefilled_update_form

    emp_id = callback_query.matches[0].group(1)
    form = None
    db = SessionLocal()
    try:
        employee = hp.employee_in_project(db, callback_query.message.chat.id, emp_id)
        if employee:
            command = hp.project_command(db, callback_query.message.chat.id, "cap_nhat_nhan_vien")
            form = _build_prefilled_update_form(employee, command)
    finally:
        db.close()

    if not form:
        await callback_query.answer("⚠️ Nhân viên này không thuộc dự án hiện tại.", show_alert=True)
        return

    await callback_query.message.reply_text(form, parse_mode=ParseMode.HTML)
    await delete_menu(callback_query)
    await callback_query.answer()


@hr_callback(r"^hrv_del\|([^|]+)$")
async def hrv_delete_callback(client, callback_query: CallbackQuery):
    emp_id = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        employee = hp.employee_in_project(db, callback_query.message.chat.id, emp_id)
        confirm = build_delete_confirm(employee) if employee else None
    finally:
        db.close()

    if not employee:
        await callback_query.answer("⚠️ Nhân viên này không thuộc dự án hiện tại.", show_alert=True)
        return
    if (employee.status or "") == "inactive":
        await callback_query.answer(
            f"⚠️ Nhân viên {emp_id} đã ở trạng thái inactive rồi.", show_alert=True
        )
        return

    await hp.safe_edit(callback_query, *confirm)
    await callback_query.answer()


@hr_callback(r"^hrv_xls$")
async def hrv_excel_callback(client, callback_query: CallbackQuery):
    """Xuất Excel danh sách nhân viên — chạy lại đúng lệnh gốc của dự án."""
    db = SessionLocal()
    try:
        _, project_name = hp.resolve_project(db, callback_query.message.chat.id)
        command_prefix = hp.project_command_prefix(project_name)
    finally:
        db.close()

    if not command_prefix:
        await callback_query.answer("⚠️ Không xác định được dự án.", show_alert=True)
        return

    await callback_query.answer("⏳ Đang tạo file Excel danh sách nhân viên...")
    await export_employee_excel(client, callback_query.message)
    await delete_menu(callback_query)


# ══════════════════════════════════════════════════════════════
# hrh — Nghỉ ngày lễ (áp cho toàn bộ nhân viên của dự án)
# ══════════════════════════════════════════════════════════════

HRH_TITLE = "CHẤM CÔNG NGHỈ NGÀY LỄ"

# Ngày đi trong callback_data dạng YYYY-MM-DD cho gọn và không lẫn với dấu "|"
HRH_DATE_FORMAT = "%Y-%m-%d"


def build_holiday_date_keyboard() -> InlineKeyboardMarkup:
    import datetime

    today = datetime.date.today()
    options = [
        ("Ngày mai", today + datetime.timedelta(days=1)),
        ("Hôm nay", today),
        ("Hôm qua", today - datetime.timedelta(days=1)),
    ]
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"{label} {d.strftime('%d/%m')}",
                callback_data=f"hrh_d|{d.strftime(HRH_DATE_FORMAT)}",
            )
            for label, d in options
        ],
        [InlineKeyboardButton("Ngày khác", callback_data="hrh_other")],
        [InlineKeyboardButton("Hủy", callback_data="hrh_x")],
    ])


def build_holiday_preview_keyboard(employees, page: int, date_str: str) -> InlineKeyboardMarkup:
    """Danh sách nhân viên sẽ bị ảnh hưởng + nút xác nhận. Ngày đi kèm mọi nút."""
    page, total_pages = hp.clamp_page(len(employees), page)
    start = page * hp.HR_PAGE_SIZE

    rows = [
        [InlineKeyboardButton(hp.employee_label(e), callback_data=f"hrh_s|{e.id}|{page}")]
        for e in employees[start:min(start + hp.HR_PAGE_SIZE, len(employees))]
    ]

    nav_row = hp.build_nav_row("hrh", page, total_pages, suffix=f"|{date_str}")
    if nav_row:
        rows.append(nav_row)

    rows.append([InlineKeyboardButton("Xác nhận chấm nghỉ lễ", callback_data=f"hrh_ok|{date_str}")])
    rows.append([InlineKeyboardButton("Hủy", callback_data="hrh_x")])
    return InlineKeyboardMarkup(rows)


def holiday_preview_header(employees, target_date) -> str:
    day_names = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5",
                 4: "Thứ 6", 5: "Thứ 7", 6: "Chủ Nhật"}
    return (
        f"<b>{HRH_TITLE}</b>\n\n"
        f"Ngày: <b>{target_date.strftime('%d/%m/%Y')}</b> ({day_names.get(target_date.weekday(), '')})\n"
        f"Số nhân viên bị ảnh hưởng: <b>{len(employees)}</b>\n\n"
        f"<i>Nhân viên đã có dữ liệu chấm công ngày này sẽ được bỏ qua.</i>\n\n"
        f"Kiểm tra danh sách rồi bấm xác nhận:"
    )


async def open_holiday_menu(message) -> None:
    """Điểm vào của lệnh nghỉ ngày lễ khi gõ không kèm tham số."""
    await message.reply_text(
        f"<b>{HRH_TITLE}</b>\n\nChọn ngày nghỉ lễ:",
        reply_markup=build_holiday_date_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def render_holiday_preview(callback_query: CallbackQuery, date_str: str, page: int = 0) -> None:
    import datetime

    target_date = datetime.datetime.strptime(date_str, HRH_DATE_FORMAT).date()
    db = SessionLocal()
    try:
        employees = hp.project_employees(db, callback_query.message.chat.id)
    finally:
        db.close()

    if not employees:
        await callback_query.answer("ℹ️ Không có nhân viên nào thuộc dự án này.", show_alert=True)
        return

    await hp.safe_edit(
        callback_query,
        holiday_preview_header(employees, target_date),
        build_holiday_preview_keyboard(employees, page, date_str),
    )
    await callback_query.answer()


@hr_callback(r"^hrh_d\|(\d{4}-\d{2}-\d{2})$")
async def hrh_date_callback(client, callback_query: CallbackQuery):
    await render_holiday_preview(callback_query, callback_query.matches[0].group(1))


@hr_callback(r"^hrh_p\|(\d+)\|(\d{4}-\d{2}-\d{2})$")
async def hrh_page_callback(client, callback_query: CallbackQuery):
    page = int(callback_query.matches[0].group(1))
    await render_holiday_preview(callback_query, callback_query.matches[0].group(2), page)


@hr_callback(r"^hrh_s\|([^|]+)\|(\d+)$")
async def hrh_employee_callback(client, callback_query: CallbackQuery):
    """Bấm vào một nhân viên trong màn xem trước chỉ để xem nhanh, không chọn gì."""
    await callback_query.answer(
        f"{callback_query.matches[0].group(1)} sẽ được chấm nghỉ lễ.", show_alert=False
    )


@hr_callback(r"^hrh_other$")
async def hrh_other_date_callback(client, callback_query: CallbackQuery):
    """Nhập ngày tự do: hiện lệnh mẫu để copy (repo không có cơ chế chờ nhập liệu)."""
    db = SessionLocal()
    try:
        command = hp.project_command(db, callback_query.message.chat.id, "nghi_ngay_le")
    finally:
        db.close()

    await hp.safe_edit(
        callback_query,
        f"<b>{HRH_TITLE}</b>\n\n"
        f"Sao chép lệnh dưới đây, sửa lại ngày rồi gửi:\n\n"
        f"<pre>{command} dd/mm/yyyy</pre>\n"
        f"Kèm ghi chú (tùy chọn):\n"
        f"<pre>{command} 01/05/2026 Quốc tế Lao động</pre>",
        InlineKeyboardMarkup([[InlineKeyboardButton("Hủy", callback_data="hrh_x")]]),
    )
    await callback_query.answer()


@hr_callback(r"^hrh_ok\|(\d{4}-\d{2}-\d{2})$")
async def hrh_confirm_callback(client, callback_query: CallbackQuery):
    import datetime

    from bot.utils.human_resource import execute_public_holiday

    date_str = callback_query.matches[0].group(1)

    # Ghi Attendance -> chặn bấm trùng TRƯỚC mọi await
    tag = f"hrh|{date_str}"
    if not hp.hr_cb_claim(callback_query, tag):
        await callback_query.answer("⏳ Ngày này đang được xử lý.", show_alert=True)
        return

    target_date = datetime.datetime.strptime(date_str, HRH_DATE_FORMAT).date()
    await callback_query.answer("⏳ Đang chấm công nghỉ lễ...")
    try:
        await execute_public_holiday(client, callback_query.message, target_date)
    except Exception:
        hp.hr_cb_release(callback_query, tag)
        raise
    await delete_menu(callback_query)


# Đăng ký hrh_noop (nút đếm trang, do build_nav_row sinh ra) và hrh_x (Hủy) như 10 luồng
# còn lại. Phải gọi SAU khối hrh ở trên: register_common chỉ đăng ký _noop và _x, nên nó
# không đụng tới hrh_p|<trang>|<ngày> và hrh_s|<id>|<trang> vốn có chữ ký riêng kèm ngày.
# Thân _cancel của register_common giống hệt hrh_cancel_callback cũ (delete_menu), nên
# hành vi nút Hủy không đổi — giữ cả hai chỉ tạo ra một handler chết.
register_common("hrh")


# ══════════════════════════════════════════════════════════════
# Điểm vào cho các lệnh (được tien_nga.py / ggomoosin.py gọi)
# ══════════════════════════════════════════════════════════════

FLOWS = {
    flow.prefix: flow
    for flow in (FLOW_HRN, FLOW_HRU, FLOW_HRD, FLOW_HRT, FLOW_HRK,
                 FLOW_HRP, FLOW_HRR, FLOW_HRA, FLOW_HRV)
}

# Các luồng không cần chọn nhân viên: mở thẳng màn chọn thời gian
MONTH_ONLY_FLOWS = {
    "hrl": HRL_TITLE,
}


async def open_flow(message, prefix: str) -> None:
    """
    Mở menu của một lệnh HR. Tiêu đề / gợi ý / bộ nút lấy từ chính định nghĩa
    luồng, nên wrapper ở tien_nga.py và ggomoosin.py không phải lặp lại.
    """
    if prefix in MONTH_ONLY_FLOWS:
        await hp.open_month_menu(message, prefix, MONTH_ONLY_FLOWS[prefix])
        return

    flow = FLOWS[prefix]
    db = SessionLocal()
    try:
        text, markup = hp.build_employee_menu(
            db,
            message.chat.id,
            flow.prefix,
            flow.title,
            flow.hint,
            extra_rows=flow.action_rows(None) if flow.action_rows else None,
            only_active=flow.only_active,
        )
    finally:
        db.close()

    await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def export_employee_excel(client, reply_to) -> None:
    """Xuất Excel danh sách nhân viên của dự án — dùng chung cho lệnh và nút bấm."""
    import os

    from bot.utils.hr_excel import build_employee_excel

    # Dựng file xong mới trả connection, rồi mới upload — không giữ connection
    # xuyên qua lệnh gọi mạng.
    temp_path = file_name = caption = None
    db = SessionLocal()
    try:
        employees = hp.project_employees(db, reply_to.chat.id, only_active=False)
        employees.sort(key=lambda e: (e.last_name or "", e.first_name or ""))
        if employees:
            _, project_name = hp.resolve_project(db, reply_to.chat.id)
            temp_path, file_name, caption = build_employee_excel(employees, project_name)
    finally:
        db.close()

    if not temp_path:
        await reply_to.reply_text(
            "⚠️ Không có nhân viên nào thuộc dự án này.", parse_mode=ParseMode.HTML
        )
        return

    try:
        await client.send_document(
            chat_id=reply_to.chat.id,
            document=temp_path,
            file_name=file_name,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
