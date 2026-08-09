"""
Menu nút bấm cho phân hệ Đối Tác (Tiến Nga).

Mọi callback của phân hệ đối tác nằm ở đây, không nằm trong
bot/utils/partner_picker.py — file đó được import lười nên decorator đặt ở đó
sẽ không bao giờ đăng ký lúc bot khởi động.

Nghiệp vụ (execute_*) vẫn ở bot/handlers/tien_nga.py và được import LƯỜI trong
thân handler: tien_nga.py cũng gọi ngược open_flow() của file này, import ở
đầu module hai chiều là vòng lặp.

BẢNG PREFIX
    tnp  tạo đối tác             tng  giao dịch đối tác
    tnu  cập nhật đối tác        tnk  kiểm tra giao dịch
    tnd  xóa đối tác             tnc  kiểm tra công nợ      (có bước chọn loại)
    tnv  danh sách đối tác       tnt  thanh toán công nợ    (có bước chọn loại)
    tnm  lệnh member — chỉ khi nhóm map ra nhiều hơn 1 đối tượng

Tiền tố cố ý KHÔNG có gạch dưới sau "tn" để không chồng lấn với các nhóm
callback sẵn có trong tien_nga.py (tn_dtm_, tn_lcp_, tn_cc_, tn_uc_, tn_dc_,
tn_dp_, tn_ptxn_, tn_selcp_, tn_ucp_) — mọi regex đều neo ^.

Pyrogram chỉ chạy handler khớp ĐẦU TIÊN, nên hai regex chồng lấn không báo lỗi
mà chỉ lặng lẽ phụ thuộc thứ tự đăng ký. tmp/test_partner_picker.py có một test
đối chiếu toàn bộ callback_data với mọi handler đã đăng ký để chặn việc đó.
"""

from dataclasses import dataclass
from functools import wraps
from typing import Callable, Optional

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.db.session import SessionLocal
from bot.utils import partner_picker as pp
from bot.utils.bot import bot
from bot.utils.enums import CustomTitle, UserType
from bot.utils.logger import LogError, LogType
from bot.utils.utils import (
    command_timeout,
    require_custom_title,
    require_group_role,
    require_project_name,
    require_user_type,
)

# Luồng công nợ đi qua 3 màn (chọn loại -> điểm thu mua -> đối tượng) nên rất dễ
# vượt 30 giây mặc định của command_timeout. Cùng con số với HR_MENU_TIMEOUT.
PARTNER_MENU_TIMEOUT = 600


# ══════════════════════════════════════════════════════════════
# Hạ tầng đăng ký handler
# ══════════════════════════════════════════════════════════════

def _guard(func):
    """Bọc try/except chung: lỗi nào cũng thành toast thay vì traceback im lặng."""
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

    return guarded


def partner_cb(pattern: str):
    """
    Callback của quản trị viên đối tác: nhóm main, custom title đối tác.
    Giữ đúng bộ quyền của các lệnh gốc trong tien_nga.py.
    """
    def decorator(func):
        return bot.on_callback_query(filters.regex(pattern))(
            require_user_type(UserType.OWNER, UserType.ADMIN)(
                require_project_name("Tiến Nga")(
                    require_group_role("main")(
                        require_custom_title(CustomTitle.SUPER_MAIN, CustomTitle.MAIN_PARTNER)(
                            command_timeout(
                                timeout_seconds=PARTNER_MENU_TIMEOUT, auto_delete_cmd=True
                            )(_guard(func))
                        )
                    )
                )
            )
        )
    return decorator


def debt_cb(pattern: str):
    """
    Như partner_cb nhưng cho 2 dự án và không đòi custom title đối tác:
    thanh_toan_cong_no vốn thuộc cả Tiến Nga lẫn Thu Hoạch, và được đăng ký cho
    main_finance / main_harvest chứ không riêng main_partner (tien_nga.py:12222).
    """
    def decorator(func):
        return bot.on_callback_query(filters.regex(pattern))(
            require_user_type(UserType.OWNER, UserType.ADMIN)(
                require_project_name("Tiến Nga", "Thu Hoạch")(
                    require_group_role("main")(
                        command_timeout(
                            timeout_seconds=PARTNER_MENU_TIMEOUT, auto_delete_cmd=True
                        )(_guard(func))
                    )
                )
            )
        )
    return decorator


def member_cb(pattern: str):
    """
    Callback của nhóm member. Không đòi custom title — giống
    rental_kiem_tra_tt_khach_hang (rental.py:1678).

    Có cả OWNER: lệnh gốc trước khi tách cho phép OWNER/ADMIN/MEMBER và không
    ràng buộc nhóm, nên bỏ OWNER ở đây là người dùng OWNER đứng trong nhóm
    member mất sạch đường dùng — lệnh main đã bị chặn bởi require_group_role.

    Quyền xem dữ liệu KHÔNG nằm ở decorator này mà ở pp.owns_entity: nhóm member
    chỉ được thấy đối tượng gắn với chính nhóm mình.
    """
    def decorator(func):
        return bot.on_callback_query(filters.regex(pattern))(
            require_user_type(UserType.OWNER, UserType.ADMIN, UserType.MEMBER)(
                require_project_name("Tiến Nga")(
                    require_group_role("member")(
                        command_timeout(
                            timeout_seconds=PARTNER_MENU_TIMEOUT, auto_delete_cmd=True
                        )(_guard(func))
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


def register_common(prefix: str, cb_factory=partner_cb) -> None:
    """Đăng ký nút đếm trang và nút Hủy cho một prefix."""

    @cb_factory(rf"^{prefix}_noop$")
    async def _noop(client, callback_query: CallbackQuery):
        await callback_query.answer()

    @cb_factory(rf"^{prefix}_x$")
    async def _cancel(client, callback_query: CallbackQuery):
        await delete_menu(callback_query)


# ══════════════════════════════════════════════════════════════
# Luồng danh sách đối tác (tnp / tnu / tnd / tnv / tng / tnk)
# ══════════════════════════════════════════════════════════════

@dataclass
class PartnerFlow:
    prefix: str
    title: str
    hint: str = "Chọn đối tác:"
    # async (client, callback_query, entity, page) -> None
    on_select: Optional[Callable] = None
    # (entity|None, page) -> list[list[InlineKeyboardButton]]
    # Nhận page để các nút thao tác mang được trang hiện tại theo, nhờ đó nút
    # "Quay lại" ở màn sau quay về đúng trang chứ không nhảy về trang 1.
    action_rows: Optional[Callable] = None
    # Hiện ô tick ✅/⬜ (chỉ luồng ở lại màn danh sách mới cần)
    show_selection: bool = False
    only_active: bool = True
    empty_text: str = "<i>ℹ️ Chưa có đối tác nào trong hệ thống.</i>"


def build_partner_menu(db, flow: PartnerFlow, page: int = 0, selected_code: str | None = None):
    """
    Dựng (text, markup) cho màn danh sách đối tác.

    Đồng bộ có chủ đích: hàm gọi lấy kết quả rồi ĐÓNG session trước khi gọi
    Telegram, để không giữ connection qua một lời gọi mạng.
    """
    entities = pp.fetch_entities(db, "dt", only_active=flow.only_active)

    if not entities:
        # Vẫn phải dựng bàn phím: luồng tnp không có đối tác nào thì đúng lúc đó
        # mới cần nút "Thêm mới đối tác" nhất. Bỏ markup là lệnh thành cụt đường.
        text = f"<b>{flow.title}</b>\n\n{flow.empty_text}"
        rows = list(flow.action_rows(None, 0)) if flow.action_rows else []
        rows.append([InlineKeyboardButton("Hủy", callback_data=f"{flow.prefix}_x")])
        return text, InlineKeyboardMarkup(rows)

    selected = next((e for e in entities if e.code == selected_code), None)
    text = pp.build_entity_header(entities, selected, flow.title, flow.hint)

    page = pp.clamp_page(len(entities), page, pp.PARTNER_PAGE_SIZE)[0]
    extra_rows = flow.action_rows(selected, page) if flow.action_rows else None
    markup = pp.build_entity_keyboard(
        entities,
        page,
        flow.prefix,
        item_cb=lambda e, p: f"{flow.prefix}_s|{e.code}|{p}",
        selected_code=selected_code if flow.show_selection else None,
        nav_suffix=f"|{selected_code or ''}",
        extra_rows=extra_rows,
    )
    return text, markup


async def render_partner_list(
    callback_query: CallbackQuery,
    flow: PartnerFlow,
    page: int,
    selected_code: str | None = None,
) -> None:
    """Vẽ lại màn danh sách. Truy vấn lại DB mỗi lần để không hiện dữ liệu cũ."""
    db = SessionLocal()
    try:
        text, markup = build_partner_menu(db, flow, page, selected_code)
    finally:
        db.close()

    await pp.screen_edit(callback_query, text, markup)


def register_partner_list(flow: PartnerFlow) -> None:
    """Đăng ký _noop, _x, _p (phân trang) và _s (chọn) cho một luồng."""
    register_common(flow.prefix)

    @partner_cb(rf"^{flow.prefix}_p\|(\d+)\|(.*)$")
    async def _paginate(client, callback_query: CallbackQuery):
        page = int(callback_query.matches[0].group(1))
        selected_code = callback_query.matches[0].group(2) or None
        await render_partner_list(callback_query, flow, page, selected_code)

    @partner_cb(rf"^{flow.prefix}_s\|([^|]+)\|(\d+)$")
    async def _select(client, callback_query: CallbackQuery):
        code = callback_query.matches[0].group(1)
        page = int(callback_query.matches[0].group(2))

        db = SessionLocal()
        try:
            entity = pp.fetch_entity(db, "dt", code)
        finally:
            db.close()

        if not entity:
            await callback_query.answer("⚠️ Không tìm thấy đối tác này.", show_alert=True)
            return

        if flow.on_select:
            await flow.on_select(client, callback_query, entity, page)
        else:
            await render_partner_list(callback_query, flow, page, code)


# ══════════════════════════════════════════════════════════════
# Thao tác dùng chung giữa các luồng
# ══════════════════════════════════════════════════════════════

async def _not_found(callback_query: CallbackQuery, partner_id: str) -> None:
    await callback_query.answer(f"⚠️ Không tìm thấy Đối tác {partner_id}.", show_alert=True)


def _load_partner(db, partner_id: str):
    """
    Lấy bản ghi Partners. ĐỒNG BỘ có chủ đích: hàm gọi phải đóng session xong
    mới được gọi Telegram, kể cả trên nhánh báo lỗi — nếu await ngay ở đây thì
    mỗi lần bấm nhầm là giữ một connection suốt một vòng gọi mạng.
    """
    from app.models.business import Partners

    return db.query(Partners).filter(Partners.partner_id == partner_id).first()


async def open_update_form(callback_query: CallbackQuery, prefix: str, partner_id: str, back_cb: str) -> None:
    """
    Biến màn hình hiện tại thành form cập nhật đã điền sẵn.

    Theo dõi qua form_tracker để form tự biến mất sau khi lệnh cập nhật chạy
    xong — cùng khoá ("tien_nga_update_partner", partner_id) mà handler lệnh
    dùng để pop (tien_nga.py:9886).
    """
    from bot.utils.states import form_tracker

    db = SessionLocal()
    try:
        partner = _load_partner(db, partner_id)
        form = pp.build_partner_update_form(partner) if partner else None
    finally:
        db.close()

    if form is None:
        await _not_found(callback_query, partner_id)
        return

    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Quay lại", callback_data=back_cb),
        InlineKeyboardButton("Hủy", callback_data=f"{prefix}_x"),
    ]])
    await pp.screen_edit(callback_query, form, markup)
    form_tracker.track(
        callback_query.message.chat.id, "tien_nga_update_partner", partner_id, callback_query.message.id
    )


async def open_delete_confirm(callback_query: CallbackQuery, prefix: str, partner_id: str, back_cb: str) -> None:
    """Màn xác nhận xóa. Lệnh gõ tay trước đây xóa mềm ngay, không hỏi gì."""
    db = SessionLocal()
    try:
        partner = _load_partner(db, partner_id)
        already_gone = bool(partner) and partner.status in ("DELETED", "INACTIVE")
        text = pp.build_delete_confirm_text(partner) if partner and not already_gone else None
    finally:
        db.close()

    if not partner:
        await _not_found(callback_query, partner_id)
        return
    if already_gone:
        await callback_query.answer(
            f"ℹ️ Đối tác {partner_id} đã ở trạng thái khóa / xóa từ trước.", show_alert=True
        )
        return

    await pp.screen_edit(callback_query, text, pp.build_delete_confirm_keyboard(prefix, partner_id, back_cb))


async def confirm_delete(client, callback_query: CallbackQuery, prefix: str, partner_id: str) -> None:
    """Xóa mềm sau khi người dùng bấm Xác nhận."""
    from bot.utils.hr_picker import hr_cb_claim, hr_cb_release

    # Chốt trước mọi await: bấm hai lần sẽ ghi DB hai lần.
    tag = f"{prefix}|del|{partner_id}"
    if not hr_cb_claim(callback_query, tag):
        await callback_query.answer("⚠️ Thao tác này đã được xử lý rồi.", show_alert=True)
        return

    from bot.handlers.tien_nga import execute_delete_partner

    try:
        await execute_delete_partner(
            client, callback_query.message, partner_id, user_id=callback_query.from_user.id
        )
    except Exception:
        hr_cb_release(callback_query, tag)
        raise

    await delete_menu(callback_query)


# ══════════════════════════════════════════════════════════════
# tnp — tạo đối tác
# ══════════════════════════════════════════════════════════════

async def _tnp_select(client, callback_query: CallbackQuery, entity, page):
    """Danh sách ở đây chỉ để tham chiếu, tránh đặt trùng mã."""
    await callback_query.answer(
        f"⚠️ Mã {entity.code} đã được dùng cho \"{entity.name}\". Hãy chọn mã khác.",
        show_alert=True,
    )


FLOW_TNP = PartnerFlow(
    prefix="tnp",
    title="TẠO ĐỐI TÁC",
    hint="Các mã dưới đây đã được dùng — bấm <b>Thêm mới đối tác</b> để mở form:",
    on_select=_tnp_select,
    action_rows=lambda _selected, _page: [
        [InlineKeyboardButton("Thêm mới đối tác", callback_data="tnp_add")]
    ],
    empty_text="<i>ℹ️ Chưa có đối tác nào. Bấm Thêm mới đối tác để tạo.</i>",
)
register_partner_list(FLOW_TNP)


@partner_cb(r"^tnp_add$")
async def _tnp_add(client, callback_query: CallbackQuery):
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("Hủy", callback_data="tnp_x")]])
    await pp.screen_edit(callback_query, pp.build_partner_create_form(), markup)


# ══════════════════════════════════════════════════════════════
# tnu — cập nhật đối tác
# ══════════════════════════════════════════════════════════════

async def _tnu_select(client, callback_query: CallbackQuery, entity, page):
    await open_update_form(callback_query, "tnu", entity.code, back_cb=f"tnu_p|{page}|")


FLOW_TNU = PartnerFlow(
    prefix="tnu",
    title="CẬP NHẬT ĐỐI TÁC",
    hint="Chọn đối tác cần cập nhật:",
    on_select=_tnu_select,
    # Phải sửa được cả đối tác đang khóa, nếu không thì không có đường mở lại.
    only_active=False,
)
register_partner_list(FLOW_TNU)


# ══════════════════════════════════════════════════════════════
# tnd — xóa đối tác
# ══════════════════════════════════════════════════════════════

async def _tnd_select(client, callback_query: CallbackQuery, entity, page):
    await open_delete_confirm(callback_query, "tnd", entity.code, back_cb=f"tnd_p|{page}|")


FLOW_TND = PartnerFlow(
    prefix="tnd",
    title="XÓA ĐỐI TÁC",
    hint="Chọn đối tác cần xóa:",
    on_select=_tnd_select,
)
register_partner_list(FLOW_TND)


@partner_cb(r"^tnd_ok\|([^|]+)$")
async def _tnd_confirm(client, callback_query: CallbackQuery):
    await confirm_delete(client, callback_query, "tnd", callback_query.matches[0].group(1))


# ══════════════════════════════════════════════════════════════
# tnv — danh sách đối tác (chọn xong hiện 4 nút thao tác)
# ══════════════════════════════════════════════════════════════

def _tnv_action_rows(selected, page):
    rows = []
    if selected:
        code = selected.code
        rows.extend([
            [InlineKeyboardButton("Thông tin chi tiết", callback_data=f"tnv_i|{code}|{page}")],
            [InlineKeyboardButton("Cập nhật thông tin", callback_data=f"tnv_u|{code}|{page}")],
            [InlineKeyboardButton("Xóa đối tác", callback_data=f"tnv_d|{code}|{page}")],
            [InlineKeyboardButton("Thực hiện giao dịch", callback_data=f"tnv_g|{code}")],
        ])
    rows.append([InlineKeyboardButton("Xuất Excel danh sách", callback_data="tnv_xls")])
    return rows


FLOW_TNV = PartnerFlow(
    prefix="tnv",
    title="DANH SÁCH ĐỐI TÁC",
    hint="Chọn đối tác để xem thao tác:",
    action_rows=_tnv_action_rows,
    show_selection=True,
)
register_partner_list(FLOW_TNV)


@partner_cb(r"^tnv_i\|([^|]+)\|(\d+)$")
async def _tnv_info(client, callback_query: CallbackQuery):
    partner_id = callback_query.matches[0].group(1)
    page = callback_query.matches[0].group(2)

    db = SessionLocal()
    try:
        partner = _load_partner(db, partner_id)
        text = pp.build_partner_detail_text(partner) if partner else None
    finally:
        db.close()

    if text is None:
        await _not_found(callback_query, partner_id)
        return

    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Quay lại", callback_data=f"tnv_p|{page}|{partner_id}"),
        InlineKeyboardButton("Hủy", callback_data="tnv_x"),
    ]])
    await pp.screen_edit(callback_query, text, markup)


@partner_cb(r"^tnv_u\|([^|]+)\|(\d+)$")
async def _tnv_update(client, callback_query: CallbackQuery):
    partner_id = callback_query.matches[0].group(1)
    page = callback_query.matches[0].group(2)
    await open_update_form(callback_query, "tnv", partner_id, back_cb=f"tnv_p|{page}|{partner_id}")


@partner_cb(r"^tnv_d\|([^|]+)\|(\d+)$")
async def _tnv_delete(client, callback_query: CallbackQuery):
    partner_id = callback_query.matches[0].group(1)
    page = callback_query.matches[0].group(2)
    await open_delete_confirm(callback_query, "tnv", partner_id, back_cb=f"tnv_p|{page}|{partner_id}")


@partner_cb(r"^tnv_ok\|([^|]+)$")
async def _tnv_confirm_delete(client, callback_query: CallbackQuery):
    await confirm_delete(client, callback_query, "tnv", callback_query.matches[0].group(1))


@partner_cb(r"^tnv_g\|([^|]+)$")
async def _tnv_transaction(client, callback_query: CallbackQuery):
    from bot.handlers.tien_nga import execute_partner_transaction_menu

    await execute_partner_transaction_menu(
        client, callback_query.message, callback_query.matches[0].group(1)
    )
    await delete_menu(callback_query)


@partner_cb(r"^tnv_xls$")
async def _tnv_excel(client, callback_query: CallbackQuery):
    from bot.handlers.tien_nga import execute_export_partner_excel

    await callback_query.answer("⏳ Đang xuất Excel…")
    await execute_export_partner_excel(client, callback_query.message)
    await delete_menu(callback_query)


# ══════════════════════════════════════════════════════════════
# tng — giao dịch đối tác
# ══════════════════════════════════════════════════════════════

async def _tng_select(client, callback_query: CallbackQuery, entity, page):
    """Chọn xong thì bàn giao cho chuỗi tn_ptxn_* sẵn có, không đụng gì tới nó."""
    from bot.handlers.tien_nga import execute_partner_transaction_menu

    await execute_partner_transaction_menu(client, callback_query.message, entity.code)
    await delete_menu(callback_query)


FLOW_TNG = PartnerFlow(
    prefix="tng",
    title="GIAO DỊCH ĐỐI TÁC",
    hint="Chọn đối tác để thực hiện giao dịch:",
    on_select=_tng_select,
)
register_partner_list(FLOW_TNG)


# ══════════════════════════════════════════════════════════════
# tnk — kiểm tra giao dịch đối tác
# ══════════════════════════════════════════════════════════════

async def _tnk_select(client, callback_query: CallbackQuery, entity, page):
    """
    Không lọc ngày ở đây: khoảng ngày vẫn đi theo đường gõ tay
    (/tien_nga_kiem_tra_giao_dich DT001 01/01/2026 31/01/2026), nên nút bấm
    luôn mở với phạm vi "Tất cả".
    """
    from bot.handlers.tien_nga import execute_check_transaction_menu

    await execute_check_transaction_menu(client, callback_query.message, entity.code)
    await delete_menu(callback_query)


FLOW_TNK = PartnerFlow(
    prefix="tnk",
    title="KIỂM TRA GIAO DỊCH ĐỐI TÁC",
    hint=(
        "Chọn đối tác để kiểm tra giao dịch:\n"
        "<i>Muốn lọc theo ngày, gõ: "
        "<code>/tien_nga_kiem_tra_giao_dich DT001 01/01/2026 31/01/2026</code></i>"
    ),
    on_select=_tnk_select,
)
register_partner_list(FLOW_TNK)


# ══════════════════════════════════════════════════════════════
# Luồng công nợ 3 màn: chọn loại -> chọn đối tượng -> kết quả
#   tnc  kiểm tra công nợ
#   tnt  thanh toán công nợ
# ══════════════════════════════════════════════════════════════

@dataclass
class DebtFlow:
    prefix: str
    title: str
    # async (client, callback_query, entity) -> None
    on_pick: Callable
    cb_factory: Callable = partner_cb


def _kind_menu(flow: DebtFlow):
    return f"<b>{flow.title}</b>\n\nChọn loại đối tượng:", pp.build_kind_keyboard(flow.prefix)


def _entity_screen(db, flow: DebtFlow, kind: str, page: int, chat_id):
    """
    (text, markup) cho màn danh sách đối tượng của một loại.

    Riêng kind="kh" trả về màn chọn Điểm Thu Mua trước: DB thật có 552 khách
    hàng đang hoạt động, tức 56 trang nếu liệt kê thẳng.
    """
    label = pp.ENTITY_LABELS[kind]
    back_cb = f"{flow.prefix}_b"

    if kind == "kh":
        points = pp.collection_points(db)
        if not points:
            return f"<b>{flow.title} — {label.upper()}</b>\n\n<i>ℹ️ Chưa có điểm thu mua nào.</i>", None
        text = (
            f"<b>{flow.title} — {label.upper()}</b>\n\n"
            f"Chọn điểm thu mua để lọc bớt danh sách:\n"
            f"<i>Hoặc gõ trực tiếp mã khách hàng, ví dụ: "
            f"<code>/tien_nga_kiem_tra_cong_no X034</code></i>"
        )
        return text, pp.build_collection_point_keyboard(points, flow.prefix, back_cb=back_cb)

    entities = pp.fetch_entities(db, kind, chat_id=chat_id)
    if not entities:
        empty = (
            "<i>ℹ️ Dự án chưa có nhân viên nào.</i>" if kind == "nv"
            else f"<i>ℹ️ Chưa có {label.lower()} nào.</i>"
        )
        return f"<b>{flow.title} — {label.upper()}</b>\n\n{empty}", None

    text = pp.build_entity_header(
        entities, None, f"{flow.title} — {label.upper()}", hint=f"Chọn {label.lower()}:"
    )
    markup = pp.build_entity_keyboard(
        entities,
        page,
        flow.prefix,
        item_cb=lambda e, _p: f"{flow.prefix}_ks|{kind}|{e.code}",
        nav_cb=lambda p: f"{flow.prefix}_kp|{kind}|{p}",
        back_cb=back_cb,
    )
    return text, markup


def register_debt_flow(flow: DebtFlow) -> None:
    """Đăng ký _noop, _x, _b, _k, _p, _cp, _ks cho một luồng công nợ."""
    register_common(flow.prefix, flow.cb_factory)

    @flow.cb_factory(rf"^{flow.prefix}_b$")
    async def _back_to_kinds(client, callback_query: CallbackQuery):
        text, markup = _kind_menu(flow)
        await pp.screen_edit(callback_query, text, markup)

    async def _show_kind(callback_query: CallbackQuery, kind: str, page: int):
        db = SessionLocal()
        try:
            text, markup = _entity_screen(db, flow, kind, page, callback_query.message.chat.id)
        finally:
            db.close()
        await pp.screen_edit(callback_query, text, markup)

    @flow.cb_factory(rf"^{flow.prefix}_k\|(dt|kh|nv|hd)$")
    async def _pick_kind(client, callback_query: CallbackQuery):
        await _show_kind(callback_query, callback_query.matches[0].group(1), 0)

    # Verb riêng "_kp" (không dùng chung "_p" với luồng đối tác): đuôi của màn
    # này là mã loại, còn màn khách hàng-theo-điểm có đuôi là UUID — dùng chung
    # một verb thì hai regex chồng lấn, và lúc đó handler nào chạy chỉ còn phụ
    # thuộc thứ tự đăng ký.
    @flow.cb_factory(rf"^{flow.prefix}_kp\|(dt|kh|nv|hd)\|(\d+)$")
    async def _paginate_kind(client, callback_query: CallbackQuery):
        kind = callback_query.matches[0].group(1)
        page = int(callback_query.matches[0].group(2))
        await _show_kind(callback_query, kind, page)

    async def _show_point(callback_query: CallbackQuery, cp_id: str, page: int):
        db = SessionLocal()
        try:
            entities = pp.customers_of_point(db, cp_id)
        finally:
            db.close()

        if not entities:
            await callback_query.answer("ℹ️ Điểm thu mua này chưa có khách hàng nào.", show_alert=True)
            return

        text = pp.build_entity_header(
            entities,
            None,
            f"{flow.title} — KHÁCH HÀNG",
            hint="Chọn khách hàng:",
            type_hint_command="/tien_nga_kiem_tra_cong_no",
        )
        markup = pp.build_entity_keyboard(
            entities,
            page,
            flow.prefix,
            item_cb=lambda e, _p: f"{flow.prefix}_ks|kh|{e.code}",
            # Phân trang quay lại chính handler _cp, không cần verb thứ hai.
            nav_cb=lambda p: f"{flow.prefix}_cp|{cp_id}|{p}",
            back_cb=f"{flow.prefix}_k|kh",
        )
        await pp.screen_edit(callback_query, text, markup)

    @flow.cb_factory(rf"^{flow.prefix}_cp\|([^|]+)\|(\d+)$")
    async def _pick_point(client, callback_query: CallbackQuery):
        await _show_point(
            callback_query,
            callback_query.matches[0].group(1),
            int(callback_query.matches[0].group(2)),
        )

    @flow.cb_factory(rf"^{flow.prefix}_ks\|(dt|kh|nv|hd)\|([^|]+)$")
    async def _pick_entity(client, callback_query: CallbackQuery):
        kind = callback_query.matches[0].group(1)
        code = callback_query.matches[0].group(2)

        db = SessionLocal()
        try:
            entity = pp.fetch_entity(db, kind, code)
            # Nhân sự đến từ nút bấm vẫn phải kiểm lại: callback_data sửa được.
            if entity and kind == "nv" and not pp.employee_in_scope(
                db, callback_query.message.chat.id, code
            ):
                entity = None
        finally:
            db.close()

        if not entity:
            await callback_query.answer("⚠️ Không tìm thấy đối tượng này.", show_alert=True)
            return

        await flow.on_pick(client, callback_query, entity)


async def _tnc_pick(client, callback_query: CallbackQuery, entity):
    from bot.handlers.tien_nga import execute_show_debt

    await execute_show_debt(
        client, callback_query.message, entity.code, kind=entity.kind,
        chat_id=callback_query.message.chat.id,
    )
    await delete_menu(callback_query)


async def _tnt_pick(client, callback_query: CallbackQuery, entity):
    """Chốt lại bằng form một dòng — lệnh gốc nhận [Mã] [Số Tiền] theo khoảng trắng."""
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Quay lại", callback_data=f"tnt_k|{entity.kind}"),
        InlineKeyboardButton("Hủy", callback_data="tnt_x"),
    ]])
    await pp.screen_edit(callback_query, pp.build_payment_form(entity), markup)


FLOW_TNC = DebtFlow(prefix="tnc", title="KIỂM TRA CÔNG NỢ", on_pick=_tnc_pick)
FLOW_TNT = DebtFlow(prefix="tnt", title="THANH TOÁN CÔNG NỢ", on_pick=_tnt_pick, cb_factory=debt_cb)
register_debt_flow(FLOW_TNC)
register_debt_flow(FLOW_TNT)

DEBT_FLOWS: dict[str, DebtFlow] = {flow.prefix: flow for flow in (FLOW_TNC, FLOW_TNT)}


# ══════════════════════════════════════════════════════════════
# tnm — lệnh member, chỉ dùng khi nhóm map ra nhiều hơn 1 đối tượng
# ══════════════════════════════════════════════════════════════

def build_member_pick_keyboard(owned) -> InlineKeyboardMarkup:
    """
    Bàn phím chọn giữa các đối tượng của CHÍNH nhóm này.

    Không phân trang: một nhóm chỉ gắn với vài đối tượng, không phải danh sách
    toàn hệ thống.
    """
    rows = [
        [InlineKeyboardButton(
            f"{pp.ENTITY_LABELS[e.kind]}: {e.label}",
            callback_data=f"tnm_s|{e.kind}|{e.code}",
        )]
        for e in owned
    ]
    rows.append([InlineKeyboardButton("Hủy", callback_data="tnm_x")])
    return InlineKeyboardMarkup(rows)


register_common("tnm", member_cb)


@member_cb(r"^tnm_s\|(dt|kh|nv|hd)\|([^|]+)$")
async def _tnm_select(client, callback_query: CallbackQuery):
    """
    Bấm chọn một đối tượng của nhóm.

    callback_data do client gửi lên nên sửa được tuỳ ý — phải hỏi lại DB xem
    nhóm này có thật sự sở hữu mã đó không, đúng vai trò _rmv_owns của Rental
    (rental.py:1719). Thiếu bước này là đối tác A đọc được công nợ đối tác B.
    """
    kind = callback_query.matches[0].group(1)
    code = callback_query.matches[0].group(2)

    db = SessionLocal()
    try:
        entity = pp.owns_entity(db, callback_query.message.chat.id, kind, code)
    finally:
        db.close()

    if not entity:
        await callback_query.answer("⚠️ Đối tượng này không thuộc nhóm của bạn.", show_alert=True)
        return

    from bot.handlers.tien_nga import execute_show_debt

    await execute_show_debt(
        client, callback_query.message, entity.code, kind=entity.kind,
        chat_id=callback_query.message.chat.id,
    )
    await delete_menu(callback_query)


# ══════════════════════════════════════════════════════════════
# Điểm vào cho các lệnh gọi sang
# ══════════════════════════════════════════════════════════════

FLOWS: dict[str, PartnerFlow] = {
    flow.prefix: flow
    for flow in (FLOW_TNP, FLOW_TNU, FLOW_TND, FLOW_TNV, FLOW_TNG, FLOW_TNK)
}


async def open_flow(message, prefix: str) -> None:
    """Mở màn danh sách đối tác của một luồng từ handler lệnh."""
    flow = FLOWS[prefix]

    db = SessionLocal()
    try:
        text, markup = build_partner_menu(db, flow)
    finally:
        db.close()

    await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def open_debt_menu(message, prefix: str) -> None:
    """Mở màn chọn loại đối tượng của luồng công nợ từ handler lệnh."""
    text, markup = _kind_menu(DEBT_FLOWS[prefix])
    await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
