from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from bot.utils.bot import bot
from bot.utils.utils import check_command_target, require_user_type, require_group_role, require_project_name
from bot.utils.enums import UserType
from bot.utils.logger import LogInfo, LogError, LogType
from app.db.session import SessionLocal
import uuid

# --- Rosca: Create User ---
@bot.on_message(filters.command(["hui_tao_nguoi_choi", "rosca_create_user"]) | filters.regex(r"^@\w+\s+/(hui_tao_nguoi_choi|rosca_create_user)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def rosca_create_user_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["hui_tao_nguoi_choi", "rosca_create_user"])
    if args is None: return

    lines = message.text.strip().split("\n")
    if len(lines) < 2:
        form_template = """<b>FORM TẠO NGƯỜI CHƠI / CHỦ HỤI</b>
Vui lòng sao chép form dưới đây, điền thông tin và gửi lại:

<pre>/hui_tao_nguoi_choi
Mã ID: 
Họ và Tên: 
Username Telegram (không bắt buộc): 
Số Điện Thoại: 
Số CCCD: 
Vai Trò (Owner/Player): Player
</pre>

<i>Lưu ý: Mã ID là bắt buộc (VD: NC01, CH01). Vai trò mặc định là Player (Người chơi). Username điền định dạng @username hoặc bỏ trống.</i>"""
        await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        return

    # Parse Form
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    user_id = data.get("Mã ID", "")
    full_name = data.get("Họ và Tên", "")
    username = data.get("Username Telegram (không bắt buộc)", "").replace("@", "")
    phone_number = data.get("Số Điện Thoại", "")
    cccd = data.get("Số CCCD", "")
    role = data.get("Vai Trò (Owner/Player)", "Player").capitalize()

    if not user_id:
        await message.reply_text("⚠️ <b>Mã ID</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    if not full_name:
        await message.reply_text("⚠️ <b>Họ và Tên</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    if role not in ["Owner", "Player"]:
        await message.reply_text("⚠️ <b>Vai Trò</b> chỉ được phép là <b>Owner</b> hoặc <b>Player</b>.", parse_mode=ParseMode.HTML)
        return

    db = SessionLocal()
    try:
        from app.models.rosca import UserRosca

        # Check duplicate by ID
        existing_id = db.query(UserRosca).filter(UserRosca.id == user_id).first()
        if existing_id:
            await message.reply_text(f"⚠️ Mã ID <b>{user_id}</b> đã tồn tại trong hệ thống.", parse_mode=ParseMode.HTML)
            return

        # Check duplicate by phone number or CCCD if provided
        if phone_number:
            existing = db.query(UserRosca).filter(UserRosca.phone_number == phone_number).first()
            if existing:
                await message.reply_text(f"⚠️ Người chơi với số điện thoại <b>{phone_number}</b> đã tồn tại trong hệ thống.", parse_mode=ParseMode.HTML)
                return
                
        if cccd:
            existing = db.query(UserRosca).filter(UserRosca.cccd == cccd).first()
            if existing:
                await message.reply_text(f"⚠️ Người chơi với CCCD <b>{cccd}</b> đã tồn tại trong hệ thống.", parse_mode=ParseMode.HTML)
                return

        new_user = UserRosca(
            id=user_id,
            full_name=full_name,
            username=username if username else None,
            phone_number=phone_number if phone_number else None,
            cccd=cccd if cccd else None,
            role=role,
            status="Active"
        )
        db.add(new_user)
        db.commit()

        await message.reply_text(f"✅ Đã tạo hồ sơ <b>{full_name}</b> (Vai trò: {role}) thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[RoscaCreateUser] Created {role} {full_name} by {message.from_user.id}", LogType.SYSTEM_STATUS)
    except Exception as e:
        db.rollback()
        LogError(f"Error in rosca_create_user_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình lưu thông tin.")
    finally:
        db.close()

# --- Rosca: Update User ---
@bot.on_message(filters.command(["hui_cap_nhat_nguoi_choi", "rosca_update_user"]) | filters.regex(r"^@\w+\s+/(hui_cap_nhat_nguoi_choi|rosca_update_user)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def rosca_update_user_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["hui_cap_nhat_nguoi_choi", "rosca_update_user"])
    if args is None: return

    lines = message.text.strip().split("\n")
    if len(lines) < 2:
        if len(args) < 2:
            await message.reply_text("⚠️ Vui lòng cung cấp Mã ID của người chơi cần cập nhật.\nVí dụ: <code>/hui_cap_nhat_nguoi_choi NC01</code>", parse_mode=ParseMode.HTML)
            return
            
        user_id = args[1]
        db = SessionLocal()
        try:
            from app.models.rosca import UserRosca
            user = db.query(UserRosca).filter(UserRosca.id == user_id).first()
            if not user:
                await message.reply_text(f"⚠️ Không tìm thấy người chơi có Mã ID: <b>{user_id}</b>", parse_mode=ParseMode.HTML)
                return
                
            form_template = f"""<b>FORM CẬP NHẬT NGƯỜI CHƠI / CHỦ HỤI</b>
Vui lòng sao chép form dưới đây, chỉnh sửa thông tin và gửi lại:

<pre>/hui_cap_nhat_nguoi_choi {user_id}
Họ và Tên: {user.full_name or ''}
Username Telegram (không bắt buộc): {user.username or ''}
Số Điện Thoại: {user.phone_number or ''}
Số CCCD: {user.cccd or ''}
Vai Trò (Owner/Player): {user.role or 'Player'}
</pre>
"""
            await message.reply_text(form_template, parse_mode=ParseMode.HTML)
        except Exception as e:
            LogError(f"Error checking user in rosca_update_user: {e}", LogType.SYSTEM_STATUS)
            await message.reply_text("❌ Có lỗi xảy ra trong quá trình truy xuất thông tin.")
        finally:
            db.close()
        return

    # Parse Form
    if len(args) < 2:
        await message.reply_text("⚠️ Lệnh cập nhật không hợp lệ, thiếu Mã ID.", parse_mode=ParseMode.HTML)
        return
        
    user_id = args[1]
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    full_name = data.get("Họ và Tên", "")
    username = data.get("Username Telegram (không bắt buộc)", "").replace("@", "")
    phone_number = data.get("Số Điện Thoại", "")
    cccd = data.get("Số CCCD", "")
    role = data.get("Vai Trò (Owner/Player)", "Player").capitalize()

    if not full_name:
        await message.reply_text("⚠️ <b>Họ và Tên</b> là bắt buộc.", parse_mode=ParseMode.HTML)
        return

    if role not in ["Owner", "Player"]:
        await message.reply_text("⚠️ <b>Vai Trò</b> chỉ được phép là <b>Owner</b> hoặc <b>Player</b>.", parse_mode=ParseMode.HTML)
        return

    db = SessionLocal()
    try:
        from app.models.rosca import UserRosca
        user = db.query(UserRosca).filter(UserRosca.id == user_id).first()
        if not user:
            await message.reply_text(f"⚠️ Không tìm thấy người chơi có Mã ID: <b>{user_id}</b>", parse_mode=ParseMode.HTML)
            return

        # Check duplicate by phone number or CCCD if provided and changed
        if phone_number and phone_number != user.phone_number:
            existing = db.query(UserRosca).filter(UserRosca.phone_number == phone_number).first()
            if existing:
                await message.reply_text(f"⚠️ Số điện thoại <b>{phone_number}</b> đã được sử dụng bởi người khác.", parse_mode=ParseMode.HTML)
                return
                
        if cccd and cccd != user.cccd:
            existing = db.query(UserRosca).filter(UserRosca.cccd == cccd).first()
            if existing:
                await message.reply_text(f"⚠️ CCCD <b>{cccd}</b> đã được sử dụng bởi người khác.", parse_mode=ParseMode.HTML)
                return

        user.full_name = full_name
        user.username = username if username else None
        user.phone_number = phone_number if phone_number else None
        user.cccd = cccd if cccd else None
        user.role = role
        
        db.commit()

        await message.reply_text(f"✅ Đã cập nhật hồ sơ <b>{full_name}</b> (Vai trò: {role}) thành công!", parse_mode=ParseMode.HTML)
        LogInfo(f"[RoscaUpdateUser] Updated user {user_id} ({full_name}) by {message.from_user.id}", LogType.SYSTEM_STATUS)
    except Exception as e:
        db.rollback()
        LogError(f"Error in rosca_update_user_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình lưu thông tin.")
    finally:
        db.close()


# --- Rosca: Delete User ---
@bot.on_message(filters.command(["hui_xoa_nguoi_choi", "rosca_delete_user"]) | filters.regex(r"^@\w+\s+/(hui_xoa_nguoi_choi|rosca_delete_user)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_group_role("main")
async def rosca_delete_user_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["hui_xoa_nguoi_choi", "rosca_delete_user"])
    if args is None: return

    if len(args) < 2:
        await message.reply_text("⚠️ Vui lòng cung cấp Mã ID của người chơi cần xóa.\nVí dụ: <code>/hui_xoa_nguoi_choi NC01</code>", parse_mode=ParseMode.HTML)
        return
        
    user_id = args[1]
    db = SessionLocal()
    try:
        from app.models.rosca import UserRosca
        user = db.query(UserRosca).filter(UserRosca.id == user_id).first()
        if not user:
            await message.reply_text(f"⚠️ Không tìm thấy người chơi có Mã ID: <b>{user_id}</b>", parse_mode=ParseMode.HTML)
            return

        text = (
            f"<b>XÁC NHẬN XÓA NGƯỜI CHƠI / CHỦ HỤI</b>\n\n"
            f"- Mã ID: <b>{user.id}</b>\n"
            f"- Họ và Tên: <b>{user.full_name}</b>\n"
            f"- Vai trò: <b>{user.role}</b>\n"
            f"- SĐT: <b>{user.phone_number or 'N/A'}</b>\n\n"
            f"Bạn có chắc chắn muốn xóa hồ sơ này không?"
        )

        buttons = [
            [
                InlineKeyboardButton("Xác nhận", callback_data=f"rosca_deluser_confirm_{user.id}"),
                InlineKeyboardButton("Hủy", callback_data="rosca_deluser_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception as e:
        LogError(f"Error in rosca_delete_user_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra trong quá trình truy xuất thông tin.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rosca_deluser_confirm_(.+)$"))
async def rosca_delete_user_confirm_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.matches[0].group(1)
    db = SessionLocal()
    try:
        from app.models.rosca import UserRosca
        
        user = db.query(UserRosca).filter(UserRosca.id == user_id).first()
        if not user:
            await callback_query.message.edit_text("⚠️ Hồ sơ không tồn tại hoặc đã bị xóa.")
            return

        full_name = user.full_name
        db.delete(user)
        db.commit()

        await callback_query.message.edit_text(f"✅ Đã xóa thành công hồ sơ <b>{full_name}</b> (Mã ID: {user_id}).", parse_mode=ParseMode.HTML)
        LogInfo(f"[RoscaDeleteUser] User {user_id} ({full_name}) was deleted by {callback_query.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in rosca_deluser_confirm callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi xác nhận xóa.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^rosca_deluser_cancel$"))
async def rosca_delete_user_cancel_callback(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("❌ Đã hủy thao tác xóa hồ sơ.")

