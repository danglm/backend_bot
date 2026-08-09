"""
Hàm thuần cho luồng nút bấm phân hệ Đối Tác (Tiến Nga).

Chỉ chứa truy vấn + dựng bàn phím + dựng text. TUYỆT ĐỐI KHÔNG đặt
@bot.on_callback_query ở đây: module này được import lười trong thân hàm nên
decorator sẽ không bao giờ đăng ký lúc bot khởi động. Mọi callback nằm ở
bot/handlers/partner_menu.py.

Cũng không import bot.handlers.tien_nga ở đây — chiều ngược lại đã có, thêm
chiều này là vòng lặp import.

BỐN LOẠI ĐỐI TƯỢNG CÔNG NỢ
    dt  Đối tác     Partners.partner_id      (DT001…)
    kh  Khách hàng  Customers.hoursehold_id  (X034, LT146, P102… KHÔNG phải "KH")
    nv  Nhân sự     Employee.id              (lọc theo dự án, xem project_employees)
    hd  Hộ dân      Households.household_code (HCM_LT151, HD_SR_001… KHÔNG phải "HD")

Mã thật KHÔNG theo tiền tố mà code cũ giả định, nên nơi nào cần biết "mã này
thuộc loại nào" thì phải tra bảng chứ đừng dùng startswith — xem
docs/plan_nang_cap_ui_lenh_doi_tac.md §1.3 B1.

CALLBACK_DATA (giới hạn 64 byte của Telegram)
    {p}_p|<page>|<sel>        phân trang danh sách đối tác
    {p}_s|<code>|<page>       chọn 1 đối tác
    {p}_k|<kind>              chọn loại đối tượng
    {p}_kp|<kind>|<page>      phân trang theo loại
    {p}_ks|<kind>|<code>      chọn đối tượng theo loại
    {p}_cp|<cp_id>|<page>     danh sách khách hàng của 1 điểm thu mua
    {p}_b                     quay lại màn trước
    {p}_noop                  nút đếm trang
    {p}_x                     hủy
"""

from dataclasses import dataclass

from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# clamp_page / build_nav_row không dính gì tới nhân sự, chỉ mang tên hr_ vì ra
# đời cùng đợt nâng cấp UI nhân sự — tái sử dụng thay vì chép lại.
from bot.utils.hr_picker import build_nav_row, clamp_page
from bot.utils.logger import LogError, LogType

PARTNER_PAGE_SIZE = 10

# Trạng thái coi như đã ngừng hoạt động (cột status của cả 4 bảng dùng chung
# bộ giá trị này; status NULL được coi là ACTIVE).
INACTIVE_STATUSES = {"DELETED", "INACTIVE"}

# telegram_group là chuỗi tự do, không unique, và trong DB thật có 90 khách hàng
# để nguyên chuỗi placeholder "Chưa có". Nếu không lọc thì một nhóm trùng tên sẽ
# đọc được công nợ của cả 90 người đó.
PLACEHOLDER_GROUPS = {"", "-", "—", "n/a", "na", "chưa có", "chua co", "none", "null"}


# ══════════════════════════════════════════════════════════════
# Chuẩn hóa 4 loại đối tượng về một kiểu
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EntityRow:
    """Một đối tượng công nợ, đã tách khỏi ORM để dùng được sau khi đóng session."""
    kind: str
    code: str
    name: str
    debt: float
    status: str

    @property
    def label(self) -> str:
        return f"{self.code} - {self.name}"


ENTITY_LABELS = {"dt": "Đối tác", "kh": "Khách hàng", "nv": "Nhân sự", "hd": "Hộ dân"}

# Thứ tự này cũng là thứ tự tra bảng khi phải suy loại từ một mã gõ tay.
# Giữ đúng thứ tự mà thanh_toan_cong_no đang chạy production (tien_nga.py:12260).
ENTITY_ORDER = ("dt", "hd", "kh", "nv")


def _is_active(row) -> bool:
    return (getattr(row, "status", None) or "ACTIVE").upper() not in INACTIVE_STATUSES


def _employee_name(emp) -> str:
    name = f"{emp.last_name or ''} {emp.first_name or ''}".strip()
    return name or emp.id


def _to_row(kind: str, obj) -> EntityRow:
    """Đổi một bản ghi ORM thành EntityRow."""
    if kind == "dt":
        code, name = obj.partner_id, obj.partner_name
    elif kind == "kh":
        code, name = obj.hoursehold_id, obj.fullname
    elif kind == "nv":
        code, name = obj.id, _employee_name(obj)
    elif kind == "hd":
        code, name = obj.household_code, obj.fullname
    else:
        raise ValueError(f"kind không hợp lệ: {kind}")

    code = (code or "").strip()

    return EntityRow(
        kind=kind,
        code=code,
        # Rơi về mã khi thiếu tên, để text thanh toán / công nợ không hiện "—".
        name=(name or "").strip() or code or "—",
        debt=float(getattr(obj, "total_debt", 0) or 0),
        status=(getattr(obj, "status", None) or "ACTIVE"),
    )


def _model_of(kind: str):
    from app.models.business import Customers, Households, Partners
    from app.models.employee import Employee

    return {"dt": Partners, "kh": Customers, "nv": Employee, "hd": Households}[kind]


def _code_column(kind: str):
    model = _model_of(kind)
    return {
        "dt": lambda: model.partner_id,
        "kh": lambda: model.hoursehold_id,
        "nv": lambda: model.id,
        "hd": lambda: model.household_code,
    }[kind]()


# ══════════════════════════════════════════════════════════════
# Truy vấn
# ══════════════════════════════════════════════════════════════

def fetch_entities(db, kind: str, chat_id=None, only_active: bool = True) -> list[EntityRow]:
    """
    Danh sách đối tượng của một loại, đã sắp theo mã.

    Bản ghi thiếu mã bị loại: nút không có callback_data sẽ làm Pyrogram ném lỗi.

    kind="nv" bắt buộc có chat_id — bảng Employee dùng chung nhiều dự án, không
    lọc thì lệnh Tiến Nga sẽ liệt kê nhân sự Ggomoosin. Xem hr_picker.
    """
    if kind == "nv":
        from bot.utils.hr_picker import project_employees

        if chat_id is None:
            return []
        rows = project_employees(db, chat_id, only_active=only_active)
    else:
        model = _model_of(kind)
        rows = db.query(model).order_by(_code_column(kind)).all()
        if only_active:
            rows = [r for r in rows if _is_active(r)]

    entities = [_to_row(kind, r) for r in rows]
    entities = [e for e in entities if e.code]
    entities.sort(key=lambda e: e.code)
    return entities


def fetch_entity(db, kind: str, code: str) -> EntityRow | None:
    """Một đối tượng theo mã. Không lọc trạng thái — dùng để mở lại bản ghi đã khóa."""
    code = (code or "").strip()
    if not code:
        return None

    obj = db.query(_model_of(kind)).filter(_code_column(kind) == code).first()
    return _to_row(kind, obj) if obj else None


def find_entity_any_kind(db, code: str, chat_id=None) -> EntityRow | None:
    """
    Tra một mã gõ tay trên cả 4 bảng theo ENTITY_ORDER.

    Thay cho chuỗi startswith("DT"/"KH"/"NV"/"HD") ở tien_nga.py:10412 và
    12260 — khảo sát DB thật cho thấy chỉ "DT" là khớp, ba tiền tố còn lại
    khớp 0/557, 0/7 và 1/13. Đã kiểm chứng không mã nào trùng giữa 2 bảng nên
    thứ tự tra không gây khớp nhầm.

    chat_id dùng để chặn nhân sự dự án khác: bảng Employee là bảng dùng chung,
    thiếu bước này thì gõ tay mã G003 trong nhóm Tiến Nga sẽ đọc được nhân sự
    Ggomoosin — đường nút bấm đã lọc rồi, đường gõ tay cũng phải lọc.
    """
    for kind in ENTITY_ORDER:
        row = fetch_entity(db, kind, code)
        if not row:
            continue
        if kind == "nv" and not employee_in_scope(db, chat_id, code):
            return None
        return row
    return None


def employee_in_scope(db, chat_id, emp_id: str) -> bool:
    """Nhân viên này có thuộc dự án của nhóm đang gõ lệnh không?"""
    if chat_id is None:
        return False
    from bot.utils.hr_picker import employee_in_project

    return bool(employee_in_project(db, chat_id, emp_id))


def resolve_group_entities(db, chat_id) -> list[EntityRow]:
    """
    Các đối tượng công nợ gắn với nhóm Telegram này, tra trên cả 4 bảng.

    Dùng cho 2 lệnh member: nhóm member chỉ được xem dữ liệu của chính mình,
    nên đây là nguồn sự thật duy nhất về "nhóm này sở hữu những gì" — mọi
    handler callback của lệnh member phải gọi lại hàm này để đối chiếu thay vì
    tin vào code trong callback_data.

    Trả [] khi nhóm chưa map, hoặc khi group_name là chuỗi placeholder.
    """
    from app.models.telegram import TelegramProjectMember

    member = db.query(TelegramProjectMember).filter(
        TelegramProjectMember.chat_id == str(chat_id)
    ).first()
    if not member or not member.group_name:
        return []

    group_name = member.group_name.strip()
    if group_name.lower() in PLACEHOLDER_GROUPS:
        return []

    found = []
    for kind in ENTITY_ORDER:
        model = _model_of(kind)
        for obj in db.query(model).filter(model.telegram_group == group_name).all():
            row = _to_row(kind, obj)
            if not row.code:
                continue
            # Luật dự án cho nhân sự là "khớp nhóm VÀ đúng tiền tố mã"; khớp
            # nhóm không thôi là chưa đủ, vì Employee là bảng dùng chung. Mọi
            # đường khác tới Employee trong module này đều áp luật đủ hai vế.
            if kind == "nv" and not employee_in_scope(db, chat_id, row.code):
                continue
            found.append(row)
    return found


def owns_entity(db, chat_id, kind: str, code: str) -> EntityRow | None:
    """Đối tượng này có thuộc nhóm đang bấm không? None nghĩa là không được phép xem."""
    for row in resolve_group_entities(db, chat_id):
        if row.kind == kind and row.code == code:
            return row
    return None


def collection_points(db) -> list:
    """10 điểm thu mua, để lọc bớt 552 khách hàng trước khi hiện danh sách."""
    from app.models.business import CollectionPoint

    return db.query(CollectionPoint).order_by(CollectionPoint.collection_name).all()


def customers_of_point(db, cp_id, only_active: bool = True) -> list[EntityRow]:
    """Khách hàng thuộc một điểm thu mua."""
    from app.models.business import Customers

    rows = db.query(Customers).filter(
        Customers.collection_point_id == cp_id
    ).order_by(Customers.hoursehold_id).all()
    if only_active:
        rows = [r for r in rows if _is_active(r)]

    entities = [_to_row("kh", r) for r in rows]
    return [e for e in entities if e.code]


# ══════════════════════════════════════════════════════════════
# Định dạng tiền
# ══════════════════════════════════════════════════════════════

def fmt_money(val) -> str:
    """1250000 -> '1.250.000 VNĐ'."""
    return f"{int(val or 0):,} VNĐ".replace(",", ".")


def fmt_debt(val) -> str:
    """
    Công nợ kèm chiều: dương là mình đang nợ họ, âm là họ đang nợ mình.
    Gộp ba bản sao chép rời ở tien_nga.py:9802, 10409 và 10729.
    """
    val = val or 0
    if val > 0:
        return f"{fmt_money(val)} (nợ)"
    if val < 0:
        return f"{fmt_money(abs(val))} (dư)"
    return "0 đ"


# ══════════════════════════════════════════════════════════════
# Bàn phím
# ══════════════════════════════════════════════════════════════

def build_kind_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """Màn 1 của luồng công nợ: chọn loại đối tượng."""
    rows = [
        [InlineKeyboardButton(ENTITY_LABELS[kind], callback_data=f"{prefix}_k|{kind}")]
        for kind in ENTITY_ORDER
    ]
    rows.append([InlineKeyboardButton("Hủy", callback_data=f"{prefix}_x")])
    return InlineKeyboardMarkup(rows)


def build_entity_keyboard(
    entities,
    page: int,
    prefix: str,
    item_cb,
    selected_code: str | None = None,
    nav_suffix: str = "",
    nav_cb=None,
    extra_rows: list | None = None,
    back_cb: str | None = None,
) -> InlineKeyboardMarkup:
    """
    Danh sách đối tượng dạng nút, 10 nút/trang.

    item_cb: (entity, page) -> callback_data cho từng nút. Truyền vào thay vì
    cố định chuỗi, vì luồng đối tác dùng "{p}_s|<code>|<page>" còn luồng công
    nợ dùng "{p}_ks|<kind>|<code>".

    nav_cb: (page) -> callback_data cho nút Trước/Sau. Bỏ trống thì dùng dạng
    mặc định "{prefix}_p|<page>{nav_suffix}" của hr_picker.build_nav_row.
    Luồng công nợ BẮT BUỘC truyền nav_cb: ở đó đuôi có lúc là mã loại
    (dt/kh/nv/hd) có lúc là UUID điểm thu mua, hai regex sẽ chồng lấn nhau nếu
    cùng dùng verb "_p".

    selected_code: khác None thì bật ô tick ✅/⬜ trên từng nút.
    """
    page, total_pages = clamp_page(len(entities), page, PARTNER_PAGE_SIZE)
    start = page * PARTNER_PAGE_SIZE
    page_entities = entities[start:min(start + PARTNER_PAGE_SIZE, len(entities))]

    buttons = []
    for entity in page_entities:
        label = entity.label
        if selected_code is not None:
            label = f"{'✅' if entity.code == selected_code else '⬜'} {label}"
        buttons.append([InlineKeyboardButton(label, callback_data=item_cb(entity, page))])

    if nav_cb is None:
        nav_row = build_nav_row(prefix, page, total_pages, suffix=nav_suffix)
    else:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("<< Trước", callback_data=nav_cb(page - 1)))
        nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data=f"{prefix}_noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("Sau >>", callback_data=nav_cb(page + 1)))
        nav_row = nav_row if len(nav_row) > 1 else []

    if nav_row:
        buttons.append(nav_row)

    if extra_rows:
        buttons.extend(extra_rows)

    tail = []
    if back_cb:
        tail.append(InlineKeyboardButton("Quay lại", callback_data=back_cb))
    tail.append(InlineKeyboardButton("Hủy", callback_data=f"{prefix}_x"))
    buttons.append(tail)

    return InlineKeyboardMarkup(buttons)


def build_collection_point_keyboard(points, prefix: str, back_cb: str | None = None) -> InlineKeyboardMarkup:
    """Màn lọc điểm thu mua — chỉ dùng cho kind="kh" (552 khách hàng = 56 trang)."""
    buttons = [
        [InlineKeyboardButton(
            cp.collection_name or str(cp.id),
            callback_data=f"{prefix}_cp|{cp.id}|0",
        )]
        for cp in points
    ]
    tail = []
    if back_cb:
        tail.append(InlineKeyboardButton("Quay lại", callback_data=back_cb))
    tail.append(InlineKeyboardButton("Hủy", callback_data=f"{prefix}_x"))
    buttons.append(tail)
    return InlineKeyboardMarkup(buttons)


def build_entity_header(
    entities,
    selected: EntityRow | None,
    title: str,
    hint: str = "Chọn đối tác:",
    type_hint_command: str | None = None,
) -> str:
    """
    Phần chữ phía trên bàn phím danh sách.

    type_hint_command: tên lệnh để in gợi ý gõ mã trực tiếp. Bắt buộc dùng cho
    danh sách khách hàng vì picker ở đó vẫn dài (điểm Gia An có 231 người).
    """
    lines = [f"<b>{title}</b> (Tổng: <b>{len(entities)}</b>)\n"]
    if selected:
        lines.append(f"<b>Đã chọn:</b> {selected.name} (<code>{selected.code}</code>)")
        lines.append(f"<b>Công nợ:</b> {fmt_debt(selected.debt)}\n")
    lines.append(hint)
    if type_hint_command and entities:
        lines.append(
            f"\n<i>Hoặc gõ trực tiếp: <code>{type_hint_command} {entities[0].code}</code></i>"
        )
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# Text và form của Đối tác
# ══════════════════════════════════════════════════════════════

def build_partner_detail_text(partner) -> str:
    """Thông tin chi tiết 1 đối tác (nhận bản ghi ORM Partners)."""
    return (
        f"<b>THÔNG TIN ĐỐI TÁC</b>\n\n"
        f"<b>Mã Đối Tác:</b> <code>{partner.partner_id}</code>\n"
        f"<b>Tên Đối Tác:</b> {partner.partner_name or '—'}\n"
        f"<b>Công Nợ:</b> <code>{fmt_debt(partner.total_debt)}</code>\n"
        f"<b>Username TG:</b> {partner.username or '—'}\n"
        f"<b>Nhóm Telegram:</b> {partner.telegram_group or '—'}\n"
        f"<b>Ngân Hàng:</b> {partner.bank_name or '—'}\n"
        f"<b>Số TK:</b> <code>{partner.bank_account or '—'}</code>\n"
        f"<b>Trạng Thái:</b> {partner.status or 'ACTIVE'}"
    )


def build_partner_create_form() -> str:
    """Form tạo đối tác — giữ nguyên từng dòng như tn_dt_form cũ (tien_nga.py:9610)."""
    return (
        "<b>FORM TẠO ĐỐI TÁC</b>\n\n"
        "Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:\n\n"
        "<pre>/tien_nga_create_partner\n"
        "Mã Đối Tác: \n"
        "Tên Đối Tác: \n"
        "Công Nợ: 0\n"
        "Username TG: \n"
        "Nhóm Telegram: \n"
        "Ngân Hàng: \n"
        "Số TK: </pre>\n\n"
        "<i>Ghi chú: Mã đối tác nên viết liền không dấu (VD: DT001).</i>"
    )


def build_partner_update_form(partner) -> str:
    """Form cập nhật đã điền sẵn dữ liệu hiện tại (khuôn tien_nga.py:9799)."""
    return (
        f"<b>FORM CẬP NHẬT ĐỐI TÁC</b>\n\n"
        f"Vui lòng sao chép form dưới đây, sửa thông tin và gửi lại:\n\n"
        f"<pre>/tien_nga_update_partner\n"
        f"Mã Đối Tác: {partner.partner_id}\n"
        f"Tên Đối Tác: {partner.partner_name or ''}\n"
        f"Công Nợ: {int(partner.total_debt or 0)}\n"
        f"Username TG: {partner.username or ''}\n"
        f"Nhóm Telegram: {partner.telegram_group or ''}\n"
        f"Ngân Hàng: {partner.bank_name or ''}\n"
        f"Số TK: {partner.bank_account or ''}\n"
        f"Trạng Thái: {partner.status or 'ACTIVE'}</pre>"
    )


def build_delete_confirm_text(partner) -> str:
    """Màn xác nhận xóa — lệnh cũ xóa mềm ngay lập tức, không hỏi gì."""
    text = (
        f"<b>XÁC NHẬN XÓA ĐỐI TÁC</b>\n\n"
        f"<b>Mã Đối Tác:</b> <code>{partner.partner_id}</code>\n"
        f"<b>Tên:</b> {partner.partner_name or '—'}\n"
        f"<b>Công Nợ:</b> <code>{fmt_debt(partner.total_debt)}</code>\n\n"
    )
    if (partner.total_debt or 0) != 0:
        text += "⚠️ <b>Đối tác này còn công nợ khác 0.</b>\n"
    text += (
        "<i>Đối tác sẽ chuyển trạng thái DELETED và biến mất khỏi mọi danh sách "
        "cũng như luồng giao dịch. Bạn có chắc chắn muốn xóa?</i>"
    )
    return text


def build_delete_confirm_keyboard(prefix: str, partner_id: str, back_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Xác nhận xóa", callback_data=f"{prefix}_ok|{partner_id}"),
        InlineKeyboardButton("Quay lại", callback_data=back_cb),
        InlineKeyboardButton("Hủy", callback_data=f"{prefix}_x"),
    ]])


def build_payment_form(entity: EntityRow) -> str:
    """
    Màn cuối của thanh_toan_cong_no: mã đã điền sẵn, người dùng chỉ gõ số tiền.

    Lệnh gốc nhận tham số theo khoảng trắng trên một dòng (tien_nga.py:12228)
    nên form ở đây là một dòng lệnh, không phải form nhiều dòng như tạo/sửa.
    """
    return (
        f"<b>THANH TOÁN CÔNG NỢ — {ENTITY_LABELS[entity.kind].upper()}</b>\n\n"
        f"<b>Mã:</b> <code>{entity.code}</code>\n"
        f"<b>Tên:</b> {entity.name}\n"
        f"<b>Công Nợ Hiện Tại:</b> <code>{fmt_debt(entity.debt)}</code>\n\n"
        f"Sao chép dòng dưới, thay <b>[Số Tiền]</b> rồi gửi lại:\n\n"
        f"<pre>/tien_nga_thanh_toan_cong_no {entity.code} [Số Tiền]</pre>"
    )


def build_debt_text(entity: EntityRow) -> str:
    """Kết quả của kiem_tra_cong_no cho cả 4 loại (khuôn tien_nga.py:10415)."""
    return (
        f"<b>THÔNG TIN CÔNG NỢ {ENTITY_LABELS[entity.kind].upper()}</b>\n\n"
        f"<b>Mã:</b> <code>{entity.code}</code>\n"
        f"<b>Tên:</b> {entity.name}\n"
        f"<b>Công Nợ:</b> <code>{fmt_debt(entity.debt)}</code>\n"
        f"<b>Trạng Thái:</b> {entity.status}"
    )


# ══════════════════════════════════════════════════════════════
# Vẽ lại màn hình
# ══════════════════════════════════════════════════════════════

async def screen_edit(callback_query, text: str, markup=None) -> None:
    """
    Thay nội dung tin nhắn đang hiển thị bằng màn hình mới.

    Sao từ _tn_screen_edit (tien_nga.py:1721) thay vì import, để module này
    không phụ thuộc ngược vào bot.handlers.tien_nga.
    """
    try:
        await callback_query.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except FloodWait as e:
        # Pyrogram đã tự ngủ-và-thử-lại với mọi FloodWait <= sleep_threshold (xem bot.py).
        # Tới đây là Telegram chặn dài hơn thế -> báo bằng toast (SetBotCallbackAnswer là
        # API khác, không dính giới hạn của EditMessage) thay vì để lỗi nổ lên decorator.
        LogError(f"FloodWait {e.value}s khi vẽ lại màn hình nút bấm đối tác.", LogType.SYSTEM_STATUS)
        try:
            await callback_query.answer(
                f"⏳ Telegram đang giới hạn tốc độ. Vui lòng bấm lại sau {e.value} giây.",
                show_alert=True,
            )
        except Exception:
            pass
        return
    except Exception as e:
        # Bấm lại đúng nút của màn hình đang hiển thị -> Telegram trả MESSAGE_NOT_MODIFIED
        if "MESSAGE_NOT_MODIFIED" not in str(e):
            raise
    try:
        await callback_query.answer()
    except Exception:
        pass
