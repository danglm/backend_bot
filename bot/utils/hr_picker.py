"""
Tiện ích dùng chung cho menu nút bấm của các lệnh Nhân sự (Tiến Nga / Ggomoosin).

Module này CHỈ chứa hàm thuần (query + dựng bàn phím). Toàn bộ handler
`@bot.on_callback_query` nằm ở bot/handlers/hr_menu.py — vì module này được
import lazy nên decorator đặt ở đây sẽ không được đăng ký lúc bot khởi động.

Quy ước bàn phím bám theo bot/handlers/rental.py:
    - 10 nút / trang
    - hàng điều hướng: "<< Trước | n/N | Sau >>", ẩn hẳn khi chỉ có 1 trang
    - nút "Hủy" luôn là hàng cuối cùng
    - page trong callback_data là 0-based, hiển thị ra là page + 1

Callback_data (giới hạn 64 byte của Telegram):
    {prefix}_p|<page>|<selected_id>     phân trang danh sách nhân viên
    {prefix}_s|<emp_id>|<page>          chọn 1 nhân viên
    {prefix}_q|<arg>                    mở màn chọn thời gian
    {prefix}_g|<arg>|<year>             lưới 12 tháng của <year>
    {prefix}_m|<arg>|<month>|<year>     chốt tháng
    {prefix}_n|<arg>|<months>           chốt số tháng
    {prefix}_c|<arg>                    kỳ tùy chọn
    {prefix}_noop                       nút đếm trang
    {prefix}_x                          hủy
"""

import calendar
import datetime

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.employee import Employee

HR_PAGE_SIZE = 10

# Số năm cho phép lùi/tiến trong lưới chọn tháng
HR_YEAR_SPAN = 5

# Không có nhân viên gắn với thao tác (vd: xuất danh sách lương cả dự án)
NO_ARG = "-"

# Tiền tố mã nhân viên theo dự án.
# Khóa đối chiếu với Projects.project_name bằng so khớp chuỗi con không phân biệt
# hoa thường — đúng ngữ nghĩa của require_project_name (bot/utils/utils.py:232),
# để "ai được gõ lệnh" và "dữ liệu nào được đụng" không lệch nhau.
# Dự án không khai báo ở đây thì bỏ qua điều kiện tiền tố.
# LƯU Ý: "G" rất ngắn — nếu sau này có dự án mã bắt đầu bằng G (vd "GA...") thì
# phải đổi sang tiền tố dài hơn, nếu không hai dự án sẽ lẫn nhân viên.
HR_PROJECT_ID_PREFIXES = {
    "tiến nga": "TN",
    "ggomoosin": "G",
}

# Tiền tố tên lệnh theo dự án — dùng để nhúng đúng tên lệnh vào form mẫu khi
# form được mở từ nút bấm (vd "/tien_nga_giao_viec" so với "/ggomoosin_giao_viec").
HR_PROJECT_COMMAND_PREFIXES = {
    "tiến nga": "tien_nga",
    "ggomoosin": "ggomoosin",
}


# ══════════════════════════════════════════════════════════════
# Chống bấm trùng trên các nút ghi dữ liệu.
# Event loop chạy đơn luồng nên kiểm tra + đánh dấu ở đây là atomic,
# miễn là gọi TRƯỚC mọi lệnh await trong handler.
# ══════════════════════════════════════════════════════════════
_HR_CB_ONCE: dict[str, datetime.datetime] = {}
_HR_CB_ONCE_TTL_SECONDS = 3600


def hr_cb_claim(callback_query, tag: str) -> bool:
    """
    Giành quyền xử lý một lần cho nút này. Trả True nếu đây là lần bấm đầu tiên,
    False nếu nút đã được xử lý (bấm trùng / gửi lại callback_data).
    """
    now = datetime.datetime.now()
    for k, ts in list(_HR_CB_ONCE.items()):
        if (now - ts).total_seconds() > _HR_CB_ONCE_TTL_SECONDS:
            _HR_CB_ONCE.pop(k, None)

    key = f"{callback_query.message.chat.id}:{callback_query.message.id}:{tag}"
    if key in _HR_CB_ONCE:
        return False
    _HR_CB_ONCE[key] = now
    return True


def hr_cb_release(callback_query, tag: str) -> None:
    """Nhả lại quyền khi thao tác thất bại, để người dùng bấm lại được."""
    _HR_CB_ONCE.pop(f"{callback_query.message.chat.id}:{callback_query.message.id}:{tag}", None)


# ══════════════════════════════════════════════════════════════
# Lọc nhân viên theo dự án
#
# Nhân viên thuộc dự án X  ⟺  telegram_group khớp một nhóm role="member" của X
#                             VÀ Employee.id bắt đầu bằng tiền tố của X.
# ══════════════════════════════════════════════════════════════

def resolve_project(db, chat_id):
    """(project_id, project_name) của dự án sở hữu nhóm chat này, (None, None) nếu chưa /syncchat."""
    from app.models.business import Projects
    from app.models.telegram import TelegramProjectMember

    member = db.query(TelegramProjectMember).filter(
        TelegramProjectMember.chat_id == str(chat_id)
    ).first()
    if not member or not member.project_id:
        return None, None

    project = db.query(Projects).filter(Projects.id == member.project_id).first()
    return member.project_id, (project.project_name if project else None)


def _lookup_by_project_name(table: dict, project_name) -> str | None:
    """Tra bảng theo project_name bằng so khớp chuỗi con, không phân biệt hoa thường."""
    name_lower = (project_name or "").lower()
    if not name_lower:
        return None
    for keyword, value in table.items():
        if keyword in name_lower:
            return value
    return None


def project_id_prefix(project_name) -> str | None:
    """Tiền tố mã nhân viên của dự án, None nếu dự án không khai báo tiền tố."""
    return _lookup_by_project_name(HR_PROJECT_ID_PREFIXES, project_name)


def project_command_prefix(project_name) -> str | None:
    """Tiền tố tên lệnh của dự án (vd "tien_nga"), None nếu không khai báo."""
    return _lookup_by_project_name(HR_PROJECT_COMMAND_PREFIXES, project_name)


def project_command(db, chat_id, suffix: str) -> str:
    """
    Tên lệnh đầy đủ của dự án sở hữu nhóm chat này, vd "/tien_nga_giao_viec".
    Dùng để nhúng vào form mẫu mở từ nút bấm.
    """
    _, project_name = resolve_project(db, chat_id)
    prefix = project_command_prefix(project_name)
    return f"/{prefix}_{suffix}" if prefix else f"/{suffix}"


def matches_id_prefix(emp_id, prefix: str | None) -> bool:
    """
    Mã nhân viên có đúng tiền tố dự án không.

    Chuẩn hóa upper() cả hai vế để lỗi gõ thường ("tn001") không biến nhân viên
    thành mất tích. Dự án không có tiền tố (prefix=None) thì mọi mã đều hợp lệ.
    """
    if not prefix:
        return True
    return (emp_id or "").strip().upper().startswith(prefix.upper())


def project_member_group_keys(db, project_id) -> tuple[set, set]:
    """Tập chat_id và tập group_name của các nhóm member thuộc dự án."""
    from app.models.telegram import TelegramProjectMember

    member_groups = db.query(TelegramProjectMember).filter(
        TelegramProjectMember.project_id == project_id,
        TelegramProjectMember.role == "member",
        TelegramProjectMember.is_bot == False,  # noqa: E712 - SQLAlchemy cần ==
    ).all()

    chat_ids = {mg.chat_id.strip() for mg in member_groups if mg.chat_id}
    group_names = {mg.group_name.strip() for mg in member_groups if mg.group_name}
    return chat_ids, group_names


def project_employees_diagnostic(db, chat_id, only_active: bool = True) -> dict:
    """
    Phân loại nhân viên theo hai điều kiện của dự án. Trả về dict:

        matched       -> thỏa CẢ HAI, đây là danh sách chính thức
        wrong_prefix  -> khớp nhóm member nhưng mã sai tiền tố
        missing_group -> đúng tiền tố nhưng không khớp nhóm member nào
        prefix        -> tiền tố đang áp dụng (None nếu dự án không khai báo)

    Hai nhóm sau bị loại khỏi danh sách; hiển thị số lượng ra cho người dùng để
    lỗi cấu hình lộ ra thay vì âm thầm biến mất.
    """
    empty = {"matched": [], "wrong_prefix": [], "missing_group": [], "prefix": None}

    project_id, project_name = resolve_project(db, chat_id)
    if not project_id:
        return empty

    prefix = project_id_prefix(project_name)
    member_chat_ids, member_group_names = project_member_group_keys(db, project_id)

    query = db.query(Employee)
    if only_active:
        query = query.filter(Employee.status != "inactive")

    matched, wrong_prefix, missing_group = [], [], []
    for emp in query.all():
        group = (emp.telegram_group or "").strip()
        in_group = bool(group) and (group in member_chat_ids or group in member_group_names)
        ok_prefix = matches_id_prefix(emp.id, prefix)

        if in_group and ok_prefix:
            matched.append(emp)
        elif in_group:
            wrong_prefix.append(emp)
        elif ok_prefix and prefix:
            # Chỉ tính là "thiếu nhóm" khi tiền tố đủ đặc trưng để quy về dự án này.
            missing_group.append(emp)

    for group_list in (matched, wrong_prefix, missing_group):
        group_list.sort(key=lambda e: (e.id or ""))

    return {
        "matched": matched,
        "wrong_prefix": wrong_prefix,
        "missing_group": missing_group,
        "prefix": prefix,
    }


def project_employees(db, chat_id, only_active: bool = True) -> list:
    """Nhân viên thuộc dự án sở hữu nhóm chat này (thỏa cả hai điều kiện)."""
    return project_employees_diagnostic(db, chat_id, only_active)["matched"]


def employee_in_project(db, chat_id, emp_id: str):
    """
    Employee theo mã, CHỈ khi nhân viên đó thuộc dự án của nhóm chat này.
    Chặn việc dùng callback/lệnh của dự án này để đụng vào nhân viên dự án khác.
    """
    for emp in project_employees(db, chat_id, only_active=False):
        if emp.id == emp_id:
            return emp
    return None


def employee_label(emp) -> str:
    full_name = f"{emp.last_name or ''} {emp.first_name or ''}".strip()
    return f"{emp.id} - {full_name}" if full_name else str(emp.id)


# ══════════════════════════════════════════════════════════════
# Bàn phím danh sách nhân viên
# ══════════════════════════════════════════════════════════════

def clamp_page(total_items: int, page: int, page_size: int = HR_PAGE_SIZE) -> tuple[int, int]:
    """Trả về (page đã ép về khoảng hợp lệ, tổng số trang)."""
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    return max(0, min(page, total_pages - 1)), total_pages


def build_nav_row(prefix: str, page: int, total_pages: int, suffix: str = "") -> list:
    """
    Hàng điều hướng "<< Trước | n/N | Sau >>".
    Trả về [] khi chỉ có 1 trang (để hàm gọi bỏ hẳn hàng này đi).
    """
    row = []
    if page > 0:
        row.append(InlineKeyboardButton("<< Trước", callback_data=f"{prefix}_p|{page - 1}{suffix}"))
    row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data=f"{prefix}_noop"))
    if page < total_pages - 1:
        row.append(InlineKeyboardButton("Sau >>", callback_data=f"{prefix}_p|{page + 1}{suffix}"))
    return row if len(row) > 1 else []


def build_employee_keyboard(
    employees,
    page: int,
    prefix: str,
    selected_id: str | None = None,
    extra_rows: list | None = None,
    cancel_label: str = "Hủy",
) -> InlineKeyboardMarkup:
    """
    Danh sách nhân viên dạng nút, 10 nút/trang.

    extra_rows: các hàng nút chèn giữa hàng điều hướng và nút Hủy — dùng cho
    "Thêm mới nhân viên", "Cập nhật nhân viên", "Xóa nhân viên", "Xuất Excel"...
    """
    page, total_pages = clamp_page(len(employees), page)
    start = page * HR_PAGE_SIZE
    page_employees = employees[start:min(start + HR_PAGE_SIZE, len(employees))]

    buttons = []
    for emp in page_employees:
        label = employee_label(emp)
        if selected_id is not None:
            label = f"{'✅' if emp.id == selected_id else '⬜'} {label}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"{prefix}_s|{emp.id}|{page}")])

    nav_row = build_nav_row(prefix, page, total_pages, suffix=f"|{selected_id or ''}")
    if nav_row:
        buttons.append(nav_row)

    if extra_rows:
        buttons.extend(extra_rows)

    buttons.append([InlineKeyboardButton(cancel_label, callback_data=f"{prefix}_x")])
    return InlineKeyboardMarkup(buttons)


def build_diagnostic_lines(diagnostic: dict | None) -> list:
    """Cảnh báo về nhân viên bị loại khỏi danh sách, để lỗi cấu hình không âm thầm."""
    if not diagnostic:
        return []

    lines = []
    prefix = diagnostic.get("prefix")
    wrong_prefix = len(diagnostic.get("wrong_prefix") or [])
    missing_group = len(diagnostic.get("missing_group") or [])

    if wrong_prefix:
        lines.append(
            f"<i>⚠️ {wrong_prefix} nhân viên khớp nhóm nhưng mã không bắt đầu bằng "
            f"\"{prefix}\" — không hiển thị.</i>"
        )
    if missing_group:
        lines.append(
            f"<i>⚠️ {missing_group} nhân viên có mã \"{prefix}\" nhưng chưa gán nhóm "
            f"Telegram — không hiển thị.</i>"
        )
    return lines


def build_employee_header(
    employees,
    selected,
    title: str,
    hint: str = "Chọn nhân viên:",
    diagnostic: dict | None = None,
) -> str:
    """Phần chữ đi kèm bàn phím danh sách nhân viên."""
    lines = [f"<b>{title}</b>", ""]
    if selected is not None:
        full_name = f"{selected.last_name or ''} {selected.first_name or ''}".strip()
        lines.append(f"<b>Đã chọn:</b> {full_name} (<code>{selected.id}</code>)")
        if selected.position:
            lines.append(f"Vị trí: {selected.position}")
        lines.append("")
    lines.append(f"Tổng: <b>{len(employees)}</b> nhân viên")
    lines.extend(build_diagnostic_lines(diagnostic))
    lines.append("")
    lines.append(hint)
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# Bàn phím chọn thời gian
# ══════════════════════════════════════════════════════════════

def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    """Cộng/trừ tháng, tự cuốn năm."""
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def month_bounds(month: int, year: int) -> tuple[datetime.date, datetime.date]:
    """(ngày đầu, ngày cuối) của tháng dương lịch."""
    return (
        datetime.date(year, month, 1),
        datetime.date(year, month, calendar.monthrange(year, month)[1]),
    )


def is_full_calendar_month(start: datetime.date, end: datetime.date) -> bool:
    """Khoảng ngày này có đúng bằng trọn một tháng dương lịch không."""
    return (start, end) == month_bounds(start.month, start.year)


def month_windows(start: datetime.date, end: datetime.date):
    """
    Cắt [start, end] thành từng cửa sổ theo tháng dương lịch.

    Sinh ra (year, month, window_start, window_end). Cửa sổ phủ trọn một tháng
    trải từ mùng 1 tới ngày cuối — chính điều này giữ cho kết quả chế độ "trọn
    tháng" và chế độ "khoảng ngày" giống hệt nhau khi khoảng đúng bằng 1 tháng.
    """
    cursor = datetime.date(start.year, start.month, 1)
    while cursor <= end:
        last_day = datetime.date(
            cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1]
        )
        yield cursor.year, cursor.month, max(cursor, start), min(last_day, end)
        cursor = last_day + datetime.timedelta(days=1)


def working_days(
    year: int, month: int, work_type: int, first_day: int = 1, last_day: int | None = None
) -> int:
    """Đếm ngày công chuẩn của tháng, từ first_day đến last_day (bao gồm hai đầu)."""
    from bot.utils.scheduler import _is_working_day

    if last_day is None:
        last_day = calendar.monthrange(year, month)[1]
    return sum(
        1 for d in range(first_day, last_day + 1)
        if _is_working_day(datetime.date(year, month, d).weekday(), work_type)
    )


def format_period(start: datetime.date, end: datetime.date) -> str:
    """Nhãn kỳ để hiển thị: trọn tháng thì ghi tháng, còn lại ghi khoảng ngày."""
    if is_full_calendar_month(start, end):
        return f"Tháng {start.month:02d}/{start.year}"
    return f"{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}"


def build_month_quick_keyboard(
    prefix: str,
    arg: str,
    allow_custom_period: bool = False,
) -> InlineKeyboardMarkup:
    """
    [Tháng này MM/YYYY] [Tháng trước MM/YYYY]
    [Chọn tháng]
    [Kỳ tùy chọn]        (chỉ khi allow_custom_period)
    [Hủy]

    Tháng này / tháng trước được tính sẵn lúc dựng bàn phím và nhúng thẳng vào
    callback_data, nên chỉ cần một handler `_m` duy nhất xử lý mọi lối chọn.
    """
    today = datetime.date.today()
    prev_year, prev_month = shift_month(today.year, today.month, -1)

    buttons = [
        [
            InlineKeyboardButton(
                f"Tháng này {today.month:02d}/{today.year}",
                callback_data=f"{prefix}_m|{arg}|{today.month}|{today.year}",
            ),
            InlineKeyboardButton(
                f"Tháng trước {prev_month:02d}/{prev_year}",
                callback_data=f"{prefix}_m|{arg}|{prev_month}|{prev_year}",
            ),
        ],
        [InlineKeyboardButton("Chọn tháng", callback_data=f"{prefix}_g|{arg}|{today.year}")],
    ]
    if allow_custom_period:
        buttons.append([InlineKeyboardButton("Kỳ tùy chọn", callback_data=f"{prefix}_c|{arg}")])
    buttons.append([InlineKeyboardButton("Hủy", callback_data=f"{prefix}_x")])
    return InlineKeyboardMarkup(buttons)


def build_month_grid_keyboard(prefix: str, arg: str, year: int) -> InlineKeyboardMarkup:
    """
    [< 2025] [ 2026 ] [2027 >]
    [T1][T2][T3][T4] ... [T9][T10][T11][T12]
    [Quay lại] [Hủy]
    """
    this_year = datetime.date.today().year
    min_year, max_year = this_year - HR_YEAR_SPAN, this_year + HR_YEAR_SPAN
    year = max(min_year, min(year, max_year))

    year_row = []
    if year > min_year:
        year_row.append(InlineKeyboardButton(f"< {year - 1}", callback_data=f"{prefix}_g|{arg}|{year - 1}"))
    year_row.append(InlineKeyboardButton(f"{year}", callback_data=f"{prefix}_noop"))
    if year < max_year:
        year_row.append(InlineKeyboardButton(f"{year + 1} >", callback_data=f"{prefix}_g|{arg}|{year + 1}"))

    buttons = [year_row]
    for row_start in range(1, 13, 4):
        buttons.append([
            InlineKeyboardButton(f"T{m}", callback_data=f"{prefix}_m|{arg}|{m}|{year}")
            for m in range(row_start, row_start + 4)
        ])
    buttons.append([
        InlineKeyboardButton("Quay lại", callback_data=f"{prefix}_q|{arg}"),
        InlineKeyboardButton("Hủy", callback_data=f"{prefix}_x"),
    ])
    return InlineKeyboardMarkup(buttons)


def build_months_count_keyboard(prefix: str, arg: str) -> InlineKeyboardMarkup:
    """[3 tháng][6 tháng] / [12 tháng][24 tháng] / [Hủy] — dùng cho xem công việc."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("3 tháng", callback_data=f"{prefix}_n|{arg}|3"),
            InlineKeyboardButton("6 tháng", callback_data=f"{prefix}_n|{arg}|6"),
        ],
        [
            InlineKeyboardButton("12 tháng", callback_data=f"{prefix}_n|{arg}|12"),
            InlineKeyboardButton("24 tháng", callback_data=f"{prefix}_n|{arg}|24"),
        ],
        [InlineKeyboardButton("Hủy", callback_data=f"{prefix}_x")],
    ])


# ══════════════════════════════════════════════════════════════
# Hỗ trợ handler
# ══════════════════════════════════════════════════════════════

async def safe_edit(callback_query, text: str, reply_markup=None) -> None:
    """edit_text nhưng bỏ qua MESSAGE_NOT_MODIFIED (bấm lại đúng nút đang chọn)."""
    from pyrogram.errors import MessageNotModified
    try:
        await callback_query.message.edit_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
    except MessageNotModified:
        pass


async def load_project_employees(callback_query, db, only_active: bool = True):
    """
    (danh sách nhân viên, diagnostic) cho một callback.
    Trả (None, None) và đã báo người dùng khi dự án chưa có nhân viên nào.
    """
    diagnostic = project_employees_diagnostic(
        db, callback_query.message.chat.id, only_active=only_active
    )
    if not diagnostic["matched"]:
        await callback_query.answer(
            "ℹ️ Không có nhân viên nào thuộc dự án này.", show_alert=True
        )
        return None, None
    return diagnostic["matched"], diagnostic


def month_header(title: str, arg: str) -> str:
    """Phần chữ của màn chọn thời gian."""
    lines = [f"<b>{title}</b>", ""]
    if arg and arg != NO_ARG:
        lines.append(f"Nhân viên: <code>{arg}</code>")
        lines.append("")
    lines.append("Chọn kỳ:")
    return "\n".join(lines)


async def open_month_menu(
    message,
    prefix: str,
    title: str,
    arg: str = NO_ARG,
    allow_custom_period: bool = False,
) -> None:
    """Điểm vào của các lệnh không cần chọn nhân viên: mở thẳng màn chọn thời gian."""
    await message.reply_text(
        month_header(title, arg),
        reply_markup=build_month_quick_keyboard(prefix, arg, allow_custom_period),
        parse_mode=ParseMode.HTML,
    )


def build_employee_menu(
    db,
    chat_id,
    prefix: str,
    title: str,
    hint: str = "Chọn nhân viên:",
    extra_rows: list | None = None,
    only_active: bool = True,
    empty_text: str = "ℹ️ Chưa có nhân viên nào thuộc dự án này.",
) -> tuple[str, InlineKeyboardMarkup | None]:
    """
    Dựng nội dung màn danh sách nhân viên ở trang đầu.

    Hàm thuần, không await: người gọi lấy kết quả rồi ĐÓNG SESSION trước khi gọi
    Telegram, tránh giữ connection xuyên qua lệnh gọi mạng (xem app/db/session.py).
    """
    diagnostic = project_employees_diagnostic(db, chat_id, only_active=only_active)
    employees = diagnostic["matched"]

    if not employees:
        warnings = build_diagnostic_lines(diagnostic)
        return "\n".join([empty_text, *warnings]) if warnings else empty_text, None

    return (
        build_employee_header(employees, None, title, hint, diagnostic),
        build_employee_keyboard(employees, 0, prefix, extra_rows=extra_rows),
    )
