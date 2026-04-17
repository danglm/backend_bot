import difflib
import string
import random
import uuid
from typing import Optional, List
from functools import wraps
from pyrogram.types import Message
from pyrogram.types import CallbackQuery

async def send_reply(update, text, parse_mode=None):
    if isinstance(update, CallbackQuery):
        # Convert HTML to basic alert string or just show plain text
        import re as r
        clean_text = r.sub('<[^<]+>', '', text)
        await update.answer(clean_text, show_alert=True)
    else:
        from pyrogram.enums import ParseMode
        await update.reply_text(text, parse_mode=parse_mode or ParseMode.HTML)

def get_chat_id(update):
    if isinstance(update, CallbackQuery):
        return str(update.message.chat.id)
    return str(update.chat.id)

def get_user(update):
    return update.from_user

from app.db.session import SessionLocal
from bot.utils.enums import UserType
from bot.utils.logger import LogType
from pyrogram.enums import ParseMode

def fmt_money(val):
    if val is None: return "0 VNĐ"
    try:
        return f"{int(val):,} VNĐ".replace(",", ".")
    except:
        return str(val)

def fmt_vn(val):
    if val is None: return "0 VNĐ"
    try:
        return f"{int(val):,} VNĐ".replace(",", ".")
    except:
        return str(val)

def fmt_num(val):
    if val is None: return "0"
    try:
        if float(val) == int(val):
            return f"{int(val):,}".replace(",", ".")
        return f"{float(val):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

def fmt_weight(val):
    try:
        return f"{val:,.1f} Kg".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,0 Kg"

def get_best_match(word: str, candidates: List[str], threshold: float = 0.70) -> Optional[str]:
    """
    Finds the best matching string from a list of candidates using difflib.
    Returns the best match if its similarity ratio is >= threshold, else None.
    """
    if not word or not candidates:
        return None
        
    best_match = None
    best_ratio = 0.0
    
    for candidate in candidates:
        ratio = difflib.SequenceMatcher(None, word.lower(), candidate.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate
            
    if best_ratio >= threshold and best_match:
        return best_match
    return None

def  require_user_type(*allowed_types):
    """
    Decorator to check if the user has a permitted role in TelegramProjectMember table.
    Looks up by chat_id + username to find member_status, then maps to UserType.
    """
    # Map UserType flags to TelegramProjectMember.member_status values
    TYPE_TO_STATUS = {
        UserType.OWNER: "OWNER",
        UserType.ADMIN: "ADMINISTRATOR",
        UserType.MEMBER: "MEMBER",
    }

    def decorator(func):
        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            if not get_user(message):
                return
                
            db = SessionLocal()
            try:
                from app.models.telegram import TelegramProjectMember

                chat_id = str(get_chat_id(message))
                username = get_user(message).username
                user_id = str(get_user(message).id)

                # Find member in current group by username or user_id
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

                if not member:
                    await send_reply(message, "⚠️ Bạn chưa được đồng bộ vào nhóm này. Vui lòng yêu cầu Admin chạy lệnh /syncchat.", parse_mode=ParseMode.HTML)
                    return

                # Check if member_status matches any allowed type
                authorized = False
                for allowed_flag in allowed_types:
                    expected_status = TYPE_TO_STATUS.get(allowed_flag)
                    if expected_status and member.member_status == expected_status:
                        authorized = True
                        break
                
                if authorized:
                    return await func(client, message, *args, **kwargs)
                else:
                    roles_str = ", ".join([f"<b>{t.name if hasattr(t, 'name') else str(t)}</b>" for t in allowed_types])
                    await send_reply(message, f"⚠️ Bạn không có quyền thực hiện lệnh này. (Yêu cầu quyền: {roles_str})", parse_mode=ParseMode.HTML)
                    return
            except Exception as e:
                from bot.utils.logger import LogError
                LogError(f"Error in require_user_type decorator: {e}", LogType.SYSTEM_STATUS)
                await send_reply(message, "❌ Có lỗi xảy ra khi kiểm tra quyền hạn.")
                return
            finally:
                db.close()
        return wrapper
    return decorator


def require_group_type(*allowed_types):
    """
    Decorator to check if the command is sent from a permitted group type.
    Uses TelegramProjectMember.role column ('main' or 'member').
    Maps legacy GroupType values to role values for backward compatibility.
    """
    # Map GroupType enum values to TelegramProjectMember.role values
    TYPE_TO_ROLE = {
        "super_group": "main",
        "management_group": "main",
        "member_group": "member",
        "customer_group": "member",
    }

    def decorator(func):
        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            chat_id = str(get_chat_id(message))
            db = SessionLocal()
            try:
                from app.models.telegram import TelegramProjectMember
                
                # Convert allowed types to role values
                allowed_roles = set()
                for t in allowed_types:
                    val = t.value if hasattr(t, 'value') else str(t)
                    role = TYPE_TO_ROLE.get(val, val)
                    allowed_roles.add(role)
                
                # Find any member in this chat with a matching role
                member = db.query(TelegramProjectMember).filter(
                    TelegramProjectMember.chat_id == chat_id,
                    TelegramProjectMember.role.in_(allowed_roles)
                ).first()
                
                if member:
                    return await func(client, message, *args, **kwargs)
                else:
                    roles_str = ", ".join([f"<b>{r}</b>" for r in allowed_roles])
                    await send_reply(message, f"⚠️ Lệnh này chỉ dành cho các nhóm: {roles_str}", parse_mode=ParseMode.HTML)
                    return
            except Exception as e:
                from bot.utils.logger import LogError
                LogError(f"Error in require_group_type decorator: {e}", LogType.SYSTEM_STATUS)
                await send_reply(message, "❌ Có lỗi xảy ra khi kiểm tra loại nhóm.")
                return
            finally:
                db.close()
        return wrapper
    return decorator

def require_project_name(*project_keywords):
    """
    Decorator to check if the current chat belongs to a project whose name
    matches any of the given keywords (case-insensitive contains).
    Uses TelegramProjectMember to find the project, then Projects to check the name.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            chat_id = str(get_chat_id(message))
            db = SessionLocal()
            try:
                from app.models.telegram import TelegramProjectMember
                from app.models.business import Projects

                # Find which project this chat belongs to
                project_member = db.query(TelegramProjectMember).filter(
                    TelegramProjectMember.chat_id == chat_id
                ).first()

                if not project_member:
                    await send_reply(message, "⚠️ Nhóm này chưa được đồng bộ vào dự án nào. Vui lòng sử dụng lệnh /syncchat trước.", parse_mode=ParseMode.HTML)
                    return

                project = db.query(Projects).filter(Projects.id == project_member.project_id).first()
                if not project:
                    await send_reply(message, "⚠️ Không tìm thấy thông tin dự án.", parse_mode=ParseMode.HTML)
                    return

                project_name_lower = (project.project_name or "").lower()
                matched = any(kw.lower() in project_name_lower for kw in project_keywords)

                if matched:
                    return await func(client, message, *args, **kwargs)
                else:
                    kw_str = ", ".join([f"<b>{kw}</b>" for kw in project_keywords])
                    await send_reply(message, f"⚠️ Lệnh này chỉ dành cho dự án: {kw_str}. Dự án hiện tại: <b>{project.project_name}</b>", parse_mode=ParseMode.HTML)
                    return
            except Exception as e:
                from bot.utils.logger import LogError
                LogError(f"Error in require_project_name decorator: {e}", LogType.SYSTEM_STATUS)
                await send_reply(message, "❌ Có lỗi xảy ra khi kiểm tra dự án.")
                return
            finally:
                db.close()
        return wrapper
    return decorator

def require_group_role(*allowed_roles):
    """
    Decorator to check if the current chat has a specific role (e.g. 'main', 'member')
    in TelegramProjectMember table. Supports both Message and CallbackQuery.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(client, update, *args, **kwargs):
            is_callback = hasattr(update, "message") and update.message is not None
            message = update.message if is_callback else update
            chat_id = str(get_chat_id(message))
            
            db = SessionLocal()
            try:
                from app.models.telegram import TelegramProjectMember

                group_member = db.query(TelegramProjectMember).filter(
                    TelegramProjectMember.chat_id == chat_id,
                    TelegramProjectMember.role.in_(allowed_roles)
                ).first()

                if group_member:
                    return await func(client, update, *args, **kwargs)
                else:
                    roles_str = ", ".join([f"<b>{r.upper()}</b>" for r in allowed_roles])
                    text = f"⚠️ Lệnh này chỉ được phép sử dụng trong nhóm: {roles_str} của dự án."
                    if is_callback:
                        await update.answer(text, show_alert=True)
                    else:
                        await send_reply(message, text, parse_mode=ParseMode.HTML)
                    return
            except Exception as e:
                from bot.utils.logger import LogError
                LogError(f"Error in require_group_role decorator: {e}", LogType.SYSTEM_STATUS)
                if is_callback:
                    await update.answer("❌ Có lỗi xảy ra khi kiểm tra vai trò nhóm.", show_alert=True)
                else:
                    await send_reply(message, "❌ Có lỗi xảy ra khi kiểm tra vai trò nhóm.")
                return
            finally:
                db.close()
        return wrapper
    return decorator

def require_custom_title(*allowed_titles):
    """
    Decorator to check if the current chat has a specific custom_title (e.g. CustomTitle.MAIN_DEVICE)
    in TelegramProjectMember table. Used for Other project sub-groups.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(client, update, *args, **kwargs):
            is_callback = hasattr(update, "message") and update.message is not None
            message = update.message if is_callback else update
            chat_id = str(get_chat_id(message))
            
            # Convert allowed_titles to strings in case Enum is passed
            str_titles = [t.value if hasattr(t, 'value') else str(t) for t in allowed_titles]
            
            db = SessionLocal()
            try:
                from app.models.telegram import TelegramProjectMember

                group_member = db.query(TelegramProjectMember).filter(
                    TelegramProjectMember.chat_id == chat_id,
                    TelegramProjectMember.custom_title.in_(str_titles)
                ).first()

                if group_member:
                    return await func(client, update, *args, **kwargs)
                else:
                    titles_str = ", ".join([f"<b>{t}</b>" for t in str_titles])
                    text = f"⚠️ Lệnh này chỉ được phép sử dụng trong nhóm có custom title: {titles_str}."
                    if is_callback:
                        await update.answer(text, show_alert=True)
                    else:
                        await send_reply(message, text, parse_mode=ParseMode.HTML)
                    return
            except Exception as e:
                from bot.utils.logger import LogError
                LogError(f"Error in require_custom_title decorator: {e}", LogType.SYSTEM_STATUS)
                if is_callback:
                    await update.answer("❌ Có lỗi xảy ra khi kiểm tra custom title nhóm.", show_alert=True)
                else:
                    await send_reply(message, "❌ Có lỗi xảy ra khi kiểm tra custom title nhóm.")
                return
            finally:
                db.close()
        return wrapper
    return decorator

def generate_payment_code(length: int = 6) -> str:
    """
    Generate a random payment code with the following requirements:
    - 6 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character (@#$%&*!)
    """
    if length < 4:
        raise ValueError("Length must be at least 4 to include all required character types.")
        
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    # Define a set of special characters. Standard string.punctuation might be too many.
    special_chars = "@#$%&*!"
    special = random.choice(special_chars)
    
    remaining_length = length - 4
    all_chars = string.ascii_letters + string.digits + special_chars
    remaining = [random.choice(all_chars) for _ in range(remaining_length)]
    
    # Corrected: string.ascii_letters + string.digits + special_chars already includes everything.
    # Joining all parts and shuffling.
    code_list = list(upper + lower + digit + special) + remaining
    random.shuffle(code_list)
    return "".join(code_list)


async def check_command_target(client, text: str, cmd) -> list:
    """
    Check if the command is targeted to this bot.
    Support both: `/cmd` and `@bot_username /cmd`
    cmd can be a single string or a list of strings (aliases).
    Return list args if valid, otherwise return None.
    """
    if not text: return None
    parts = text.split()
    if not parts: return None
    
    # Support single string or list of command aliases
    cmds = cmd if isinstance(cmd, (list, tuple)) else [cmd]
    
    me = await client.get_me()
    my_username = me.username.lower() if me.username else ""
    
    # Pre-process the command part to remove optional trailing colon
    cmd_part = parts[0].rstrip(":")
    
    # Case 1: Starts with @something
    if cmd_part.startswith("@"):
        if len(parts) > 1:
            potential_cmd_part = parts[1].rstrip(":")
            for c in cmds:
                if potential_cmd_part == f"/{c}" or potential_cmd_part.startswith(f"/{c}@"):
                    mentioned = cmd_part[1:].lower()
                    if mentioned == my_username:
                        return parts[1:]
        return None
    
    # Case 2: Starts with /cmd or /cmd@bot
    for c in cmds:
        if cmd_part == f"/{c}" or cmd_part.startswith(f"/{c}@"):
            if "@" in cmd_part:
                p_mention = cmd_part.split("@")[1].lower()
                if p_mention != my_username:
                    continue
            return parts
        
    return None

import pyrogram.filters as filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from bot.utils.bot import bot
from pyrogram.enums import ParseMode

from bot.utils.enums import CustomTitle

@bot.on_message(filters.command(["list_employee", "list_customer"]) | filters.regex(r"^@\w+\s+/(list_employee|list_customer)\b"))
@require_user_type(UserType.OWNER, UserType.ADMIN)
@require_custom_title(CustomTitle.SUPER_MAIN, "main", CustomTitle.MAIN_HR)
async def list_employee_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, ["list_employee", "list_customer"])
    if args is None: return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Công ty Tiến Nga", callback_data="cb_listemp_TN")],
        [InlineKeyboardButton("Công ty GgoMoonSin", callback_data="cb_listemp_G")],
        [InlineKeyboardButton("Công ty Minh Khuê", callback_data="cb_listemp_MK")],
        [InlineKeyboardButton("Hủy", callback_data="cb_listemp_cancel")]
    ])
    
    await message.reply_text(
        "<b>DANH SÁCH NHÂN VIÊN THEO CÔNG TY</b>\n\n"
        "Vui lòng chọn công ty để xem danh sách nhân sự:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@bot.on_callback_query(filters.regex(r"^cb_listemp_"))
async def list_employee_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    
    if data == "cb_listemp_cancel":
        await callback_query.message.delete()
        return

    company_prefix = data.split("_")[-1]
    company_name = ""
    if company_prefix == "TN":
        company_name = "Công ty Tiến Nga"
    elif company_prefix == "G":
        company_name = "Công ty GgoMoonSin"
    elif company_prefix == "MK":
        company_name = "Công ty Minh Khuê"
    else:
        await callback_query.answer("Lựa chọn không hợp lệ.", show_alert=True)
        return

    await callback_query.message.edit_text(f"⏳ <i>Đang truy xuất danh sách nhân viên {company_name}...</i>", parse_mode=ParseMode.HTML)

    db = SessionLocal()
    try:
        from app.models.employee import Employee
        
        # Lọc nhân viên có id bắt đầu bằng prefix (ví dụ: 'TN', 'G', 'MK')
        employees = db.query(Employee).filter(Employee.id.like(f"{company_prefix}%")).all()
        
        if not employees:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Quay lại", callback_data="cb_listemp_back")]])
            await callback_query.message.edit_text(f"🏢 <b>{company_name}</b>\n\n<i>Chưa có nhân viên nào trong danh sách.</i>", parse_mode=ParseMode.HTML, reply_markup=kb)
            return

        # Build list string
        lines = [f"<b>DANH SÁCH NHÂN VIÊN {company_name.upper()}</b>", f"Tổng cộng: <b>{len(employees)}</b> nhân sự\n"]
        
        # Sort by ID (optional, but looks cleaner)
        employees = sorted(employees, key=lambda x: str(x.id))

        for idx, emp in enumerate(employees, 1):
            full_name = f"{emp.last_name or ''} {emp.first_name or ''}".strip()
            if not full_name: full_name = "Chưa cập nhật tên"
            position = emp.position or "Nhân viên"
            lines.append(f"{idx}. <b>{emp.id}</b> - {full_name} - {position}")
            
        # Due to Telegram message length limits (4096 chars), we truncate if too long
        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:4000] + "\n\n<i>... (Danh sách còn dài, bị ẩn bớt do giới hạn hiển thị).</i>"
            
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Quay lại", callback_data="cb_listemp_back")]])
        await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    except Exception as e:
        from bot.utils.logger import LogError, LogType
        LogError(f"Error listing employees: {e}", LogType.SYSTEM_STATUS)
        await callback_query.message.edit_text("❌ Có lỗi xảy ra khi lấy danh sách.", parse_mode=ParseMode.HTML)
    finally:
        db.close()

@bot.on_callback_query(filters.regex(r"^cb_listemp_back$"))
async def list_employee_back_callback(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Công ty Tiến Nga", callback_data="cb_listemp_TN")],
        [InlineKeyboardButton("Công ty GgoMoonSin", callback_data="cb_listemp_G")],
        [InlineKeyboardButton("Công ty Minh Khuê", callback_data="cb_listemp_MK")],
        [InlineKeyboardButton("Hủy", callback_data="cb_listemp_cancel")]
    ])
    await callback_query.message.edit_text(
        "<b>DANH SÁCH NHÂN VIÊN THEO CÔNG TY</b>\n\n"
        "Vui lòng chọn công ty để xem danh sách nhân sự:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
