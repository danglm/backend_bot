import datetime
import asyncio
import re
from bot.utils.logger import LogType, LogInfo, LogError
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from bot.utils.bot import bot
from bot.utils.db_logger import log_member_activity
from bot.utils.enums import UserType
from bot.utils.states import request_tracker
from bot.utils.utils import get_best_match, require_user_type, require_group_role, check_command_target
from app.db.session import SessionLocal
from app.models.finance import Attendance
from app.crud.attendance import get_attendance
from app.models.task import Task

@bot.on_message(filters.command(["cancel_task"]) | filters.regex(r"^@\w+\s+/cancel_task\b"))
@require_group_role("main")
async def cancel_task_handler(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ Bạn cần <b>Reply</b> vào tin nhắn thông báo thành công của bot để hủy công việc này.", parse_mode=ParseMode.HTML)
        return
        
    reply_text = message.reply_to_message.text
    if not reply_text:
        return
        
    code_match = re.search(r"\[TaskCode:\s*(-?\d+)_(\d+)\]", reply_text)
    if not code_match:
        await message.reply_text("⚠️ Không tìm thấy mã công việc hợp lệ trong tin nhắn đã Reply.")
        return
        
    chat_id = int(code_match.group(1))
    message_id = int(code_match.group(2))
    
    try:
        # Edit or Delete the task message in the member group
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="❌ <b>CÔNG VIỆC NÀY ĐÃ BỊ HỦY BỞI QUẢN LÝ</b>",
            parse_mode=ParseMode.HTML
        )
        
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.group_chat_id == str(chat_id), Task.message_id == message_id).first()
            if task:
                task.status = "CANCELLED"
                db.commit()
        finally:
            db.close()
            
        await message.reply_text("✅ Đã hủy công việc thành công!")
    except Exception as e:
        db.rollback()
        from bot.utils.logger import LogError
        LogError(f"Error cancelling task in group {chat_id}, msg {message_id}: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Không thể hủy công việc này (có thể đã bị xóa trước đó).")

# @bot.on_message(filters.new_chat_members)
# async def welcome_new_member_handler(client, message: Message) -> None:
#     """
#     Handler to welcome new members joining the group.
#     """
#     db = SessionLocal()
#     try:
#         for new_member in message.new_chat_members:
#             if new_member.is_self:
#                 continue
                
#             name = new_member.first_name
#             if new_member.last_name:
#                 name += f" {new_member.last_name}"
#             username = new_member.username

#             # # DB Logic: Sync with TelegramAccount and UserGroup
#             # if username:
#             #     account = db.query(TelegramAccount).filter(TelegramAccount.username == username).first()
#             #     if not account:
#             #         # Auto-create TelegramAccount if not exists (using Telegram ID as user_id placeholder)
#             #         account = TelegramAccount(
#             #             user_id=str(new_member.id),
#             #             username=username,
#             #             user_type=0
#             #         )
#             #         db.add(account)
#             #         db.commit()
#             #         db.refresh(account)
                
#             #     # Check and Add to UserGroup
#             #     existing_ug = db.query(UserGroup).filter(
#             #         UserGroup.account_id == account.id,
#             #         UserGroup.chat_id == str(message.chat.id)
#             #     ).first()
#             #     if not existing_ug:
#             #         new_ug = UserGroup(
#             #             account_id=account.id,
#             #             chat_id=str(message.chat.id),
#             #             join_day=datetime.datetime.now()
#             #         )
#             #         db.add(new_ug)
#             #         db.commit()

#             # welcome_text = (
#             #     f"🎉Công ty ABC xin Kính Chào Quý Nhân Viên <b>{name}</b> \n"
#             #     f"✌️Chào mừng Quý Nhân Viên đã tham gia nhóm : <b>{message.chat.title}</b> \n\n"
#             #     f"🌟Chức năng nhóm: \n"
#             #     f"- Vận hành: \n"
#             #     f"+ Check in và Check out. \n"
#             #     f"+ Đăng ký nghỉ phép. \n"
#             #     f"+ Đăng ký nhận và trả xe, thiết bị. \n"
#             #     f"- Tài chính: \n"
#             #     f"+ Chấm công và tính lương \n"
#             #     f"+ Hỗ trợ thanh toán, chuyển tiền. \n\n"
#             #     f"CẢM ƠN SỰ HỢP TÁC CỦA QUÝ NHÂN VIÊN!"
#             # )
#             # LogInfo(f"User {name} joined group {message.chat.title} and updated in DB", LogType.MEMBER_LOG)
#             # log_member_activity(message.chat.id, message.chat.title, new_member.id, name, "JOIN")
            
#             # --- Cross-group notification for Project Member/Main ---
#             from app.models.telegram import TelegramProjectMember
#             member_group = db.query(TelegramProjectMember).filter(
#                 TelegramProjectMember.chat_id == str(message.chat.id),
#                 TelegramProjectMember.role == "member"
#             ).first()
#             if member_group:
#                 main_group = db.query(TelegramProjectMember).filter(
#                     TelegramProjectMember.project_id == member_group.project_id,
#                     TelegramProjectMember.role == "main"
#                 ).first()
#                 if main_group:
#                     notify_text = (
#                         f"🔔 <b>THÔNG BÁO NHÂN SỰ:</b>\n"
#                         f"Tài khoản <b>{name}</b> (@{username or 'N/A'}) vừa tham gia vào nhóm Member <b>{message.chat.title}</b>."
#                     )
#                     try:
#                         await client.send_message(
#                             chat_id=int(main_group.chat_id),
#                             text=notify_text,
#                             parse_mode=ParseMode.HTML
#                         )
#                     except Exception as ex:
#                         LogError(f"Failed to notify main group {main_group.chat_id}: {ex}", LogType.MEMBER_LOG)
#             # ---------------------------------------------------------
            
#             # await message.reply_text(welcome_text, parse_mode=ParseMode.HTML)
#     except Exception as e:
#         db.rollback()
#         LogError(f"Error in welcome_new_member_handler: {e}", LogType.SYSTEM_STATUS)
#     finally:
#         db.close()

@bot.on_message(filters.command("ping") | filters.regex(r"^@\w+\s+/ping\b"))
@require_group_role("main")
async def command_ping_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, "ping")
    if args is None: return
    
    await message.reply_text("🏓 <b>Pong!</b>\n\nLệnh này chỉ có thể được sử dụng trong nhóm <b>Super Group</b> hoặc <b>Management Group</b>.", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("clearchat") | filters.regex(r"^@\w+\s+/clearchat\b"))
@require_user_type(UserType.ADMIN, UserType.OWNER)
async def clearchat_handler(bot, message: Message) -> None:
    """
    Command to clear recent messages (48h limit).
    """
    if message.chat.type.name == "PRIVATE":
        await message.reply_text("⚠️ Lệnh này chỉ dùng trong nhóm!")
        return

    # Parse count
    command_text = message.text or message.caption or ""
    parts = command_text.split()
    count = 100
    if len(parts) > 1:
        try:
            count = int(parts[1])
        except ValueError:
            pass
    count = min(max(1, count), 1000)

    try:
        from pyrogram.enums import ChatMemberStatus
        member_info = await bot.get_chat_member(message.chat.id, "me")
        is_admin = member_info.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        can_delete = member_info.privileges.can_delete_messages if member_info.privileges else False

        if not is_admin or not can_delete:
            await message.reply_text("❌ Bot cần quyền Admin với 'Xóa tin nhắn' để thực hiện lệnh này!")
            return

        # Range-based deletion (48h limit)
        start_id = message.id
        message_ids = list(range(start_id, max(0, start_id - (count + 1)), -1))
        
        deleted_count = 0
        for i in range(0, len(message_ids), 100):
            chunk = message_ids[i:i + 100]
            try:
                # Try chunk first
                await bot.delete_messages(message.chat.id, chunk)
                deleted_count += len(chunk)
            except Exception as chunk_err:
                LogInfo(f"ClearChat Chunk Error: {chunk_err}. Trying individual deletion...", LogType.SYSTEM_STATUS)
                # Fallback to individual to see what exactly fails
                for msg_id in chunk:
                    try:
                        await bot.delete_messages(message.chat.id, msg_id)
                        deleted_count += 1
                    except Exception as single_err:
                        # Log the first few failures to avoid spam but give info
                        if deleted_count < 1:
                           LogError(f"ClearChat Detail: Message {msg_id} failed: {single_err}", LogType.SYSTEM_STATUS)
                        continue
        
        if deleted_count > 0:
            status_text = f"✅ <b>Hệ thống:</b> Đã dọn dẹp {deleted_count} tin nhắn gần đây."
        else:
            status_text = "⚠️ <b>Hệ thống:</b> Không thể xóa tin nhắn.\nLưu ý: Bot chỉ xóa được tin nhắn trong vòng 48h."

        status = await bot.send_message(message.chat.id, status_text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(5)
        await status.delete()

    except Exception as e:
        LogError(f"Error in clearchat_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")

@bot.on_message(filters.left_chat_member)
async def left_chat_member_handler(client, message: Message) -> None:
    """
    Handler to track and notify when a member voluntarily leaves the group or is removed.
    """
    left_member = message.left_chat_member
    
    if left_member.is_self:
        return
        
    name = left_member.first_name
    if left_member.last_name:
        name += f" {left_member.last_name}"
        
    db = SessionLocal()
    try:
        # --- Cross-group notification for Project Member/Main ---
        from app.models.telegram import TelegramProjectMember
        member_group = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == str(message.chat.id),
            TelegramProjectMember.role == "member"
        ).first()
        if member_group:
            main_group = db.query(TelegramProjectMember).filter(
                TelegramProjectMember.project_id == member_group.project_id,
                TelegramProjectMember.role == "main"
            ).first()
            if main_group:
                username = left_member.username
                notify_text = (
                    f"⚠️ <b>THÔNG BÁO NHÂN SỰ:</b>\n"
                    f"Tài khoản <b>{name}</b> (@{username or 'N/A'}) vừa rời khỏi nhóm Member <b>{message.chat.title}</b>."
                )
                try:
                    await client.send_message(
                        chat_id=int(main_group.chat_id),
                        text=notify_text,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as ex:
                    LogError(f"Failed to notify main group {main_group.chat_id}: {ex}", LogType.MEMBER_LOG)
        # ---------------------------------------------------------
    except Exception as e:
         LogError(f"Error in left_chat_member_handler: {e}", LogType.SYSTEM_STATUS)
    finally:
         db.close()

@bot.on_message(filters.command(["accepted", "confirmed", "denied"]))
async def approval_reply_handler(client, message: Message) -> None:
    """Handle approval/denial via group replies."""
    if not message.reply_to_message:
        return

    replied_msg = message.reply_to_message
    content = replied_msg.text or ""
    
    if "ĐƠN XIN NGHỈ PHÉP" not in content and "YÊU CẦU CẬP NHẬT CHẤM CÔNG" not in content and "YÊU CẦU ĐĂNG KÝ TĂNG CA" not in content:
        return

    # Extract designated approver from original message
    approver_match = re.search(r"Người duyệt:\s*(?:<b>)?(.*?)(?:</b>)?(?:\n|$)", content)
    if not approver_match:
        return
        
    designated_approver = approver_match.group(1).strip()
    if designated_approver.startswith("@"):
        designated_approver = designated_approver[1:]
        
    sender_username = message.from_user.username
    
    if sender_username != designated_approver:
        await message.reply_text(f"⚠️ Chỉ người duyệt được chỉ định (<b>@{designated_approver}</b>) mới có quyền thực hiện lệnh này.", parse_mode=ParseMode.HTML)
        return

    command = message.command[0].lower()
    requester_match = re.search(r"Người (?:nghỉ|yêu cầu):\s*(?:<b>)?(.*?)(?:</b>)?(?:\n|$)", content)
    requester_name = requester_match.group(1).strip() if requester_match else "Nhân viên"

    if command in ["accepted", "confirmed"]:
        status_text = "✅ <b>ĐÃ CHẤP THUẬN</b>"
        color_msg = "đã được chấp thuận"
    else:
        status_text = "❌ <b>BỊ TỪ CHỐI</b>"
        color_msg = "đã bị từ chối"

    response = (
        f"{status_text}\n\n"
        f"Yêu cầu của <b>{requester_name}</b> {color_msg} bởi <b>@{sender_username}</b>."
    )

    # Automated Leave Balance Deduction
    if command in ["accepted", "confirmed"] and "ĐƠN XIN NGHỈ PHÉP" in content:
        leave_type_match = re.search(r"Loại nghỉ:\s*(?:<b>)?(.*?)(?:</b>)?(?:\n|$)", content)
        dates_match = re.search(r"Thời gian:\s*(?:<code>)?(.*?)(?:</code>)?(?:\n|$)", content)
        requester_user_match = re.search(r"Người nghỉ:.*?\(\s*(?:<b>)?@([^\s<]+)(?:</b>)?\s*\)", content)
        
        if leave_type_match and dates_match and requester_user_match:
            l_type = leave_type_match.group(1).strip()
            l_dates = dates_match.group(1).strip()
            l_username = requester_user_match.group(1).strip()
            
            if l_type == "Nghỉ phép năm" or get_best_match(l_type, ["Nghỉ phép năm"], threshold=0.7):
                db = SessionLocal()
                try:
                    # Calculate days
                    num_days = 0
                    if " - " in l_dates:
                        start_str, end_str = l_dates.split(" - ")
                        start_dt = datetime.datetime.strptime(start_str.strip(), "%d/%m/%Y")
                        end_dt = datetime.datetime.strptime(end_str.strip(), "%d/%m/%Y")
                        num_days = (end_dt - start_dt).days + 1
                    else:
                        # Single day
                        num_days = 1
                        
                    if num_days > 0:
                        from app.models.employee import Employee
                        employee = db.query(Employee).filter(Employee.username == l_username).first()
                        if employee:
                            old_balance = employee.leave_balance or 0
                            new_balance = old_balance - num_days
                            if new_balance < 0:
                                response += (
                                    f"\n\n⚠️ <b>Không thể trừ phép năm!</b>"
                                    f"\nSố ngày phép còn lại: <code>{old_balance}</code>"
                                    f"\nSố ngày xin nghỉ: <code>{num_days}</code>"
                                    f"\n<i>Nhân viên không đủ phép năm. Vui lòng chuyển sang loại nghỉ khác (nghỉ không lương, ...).</i>"
                                )
                            else:
                                employee.leave_balance = new_balance
                                db.commit()
                                response += f"\n\n💡 <b>Số ngày nghỉ phép năm còn lại:</b> <code>{new_balance}</code>"
                            
                                # --- Record in Attendance table ---
                                try:
                                    start_dt_parsed = datetime.datetime.strptime(l_dates.split(" - ")[0].strip() if " - " in l_dates else l_dates.strip(), "%d/%m/%Y")
                                    days_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
                                    
                                    for i in range(num_days):
                                        current_date = start_dt_parsed + datetime.timedelta(days=i)
                                        d, m, y = current_date.day, current_date.month, current_date.year
                                        d_str = days_vn[current_date.weekday()]
                                        
                                        existing_att = db.query(Attendance).filter(
                                            Attendance.employee_id == employee.id,
                                            Attendance.year == y,
                                            Attendance.month == m,
                                            Attendance.day == d,
                                        ).first()
                                        if existing_att:
                                            existing_att.error = l_type
                                            db.add(existing_att)
                                        else:
                                            new_att = Attendance(
                                                employee_id=employee.id,
                                                year=y,
                                                month=m,
                                                day=d,
                                                date_str=d_str,
                                                error=l_type
                                            )
                                            db.add(new_att)
                                    db.commit()
                                except Exception as att_err:
                                    db.rollback()
                                    LogError(f"Error recording attendance for leave: {att_err}", LogType.SYSTEM_STATUS)
                                # ----------------------------------
                except Exception as e:
                    LogError(f"Error updating leave balance: {e}", LogType.SYSTEM_STATUS)
                finally:
                    db.close()
    
    # Automated Overtime Recording
    if command in ["accepted", "confirmed"] and "YÊU CẦU ĐĂNG KÝ TĂNG CA" in content:
        d_match = re.search(r"Ngày:\s*(?:<code>)?(.*?)(?:</code>)?(?:\n|$)", content)
        t_match = re.search(r"Thời gian:\s*(?:<b>)?(.*?)(?:</b>)?(?:\n|$)", content)
        u_match = re.search(r"Người yêu cầu:.*?\(\s*(?:<b>)?@([^\s<]+)(?:</b>)?\s*\)", content)

        if d_match and t_match and u_match:
            ot_date_str = d_match.group(1).strip()
            ot_time_range = t_match.group(1).strip()
            ot_username = u_match.group(1).strip()

            db = SessionLocal()
            try:
                from app.models.employee import Employee
                # Parse date
                ot_date = None
                if "/" in ot_date_str:
                    d_parts = ot_date_str.split("/")
                    try:
                        if len(d_parts[0]) == 4: # yyyy/mm/dd
                            ot_date = datetime.datetime.strptime(ot_date_str, "%Y/%m/%d")
                        else: # dd/mm/yyyy
                            ot_date = datetime.datetime.strptime(ot_date_str, "%d/%m/%Y")
                    except Exception as e:
                        LogError(f"Date parse error in OT recording: {e}", LogType.SYSTEM_STATUS)

                # Parse time range (TimeA - TimeB)
                if ot_date and "-" in ot_time_range:
                    time_parts = ot_time_range.split("-")
                    if len(time_parts) == 2:
                        s_t_str = time_parts[0].strip()
                        e_t_str = time_parts[1].strip()
                        
                        try:
                            start_t = datetime.datetime.strptime(s_t_str, "%H:%M").time()
                            end_t = datetime.datetime.strptime(e_t_str, "%H:%M").time()
                            
                            start_dt = datetime.datetime.combine(ot_date.date(), start_t)
                            end_dt = datetime.datetime.combine(ot_date.date(), end_t)
                            
                            if end_dt < start_dt:
                                end_dt += datetime.timedelta(days=1)

                            employee = db.query(Employee).filter(Employee.telegram_username == ot_username).first()
                            if employee:
                                s_id = employee.id
                                y, m, d = ot_date.year, ot_date.month, ot_date.day
                                days_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
                                ds_vn = days_vn[ot_date.weekday()]

                                existing_att = get_attendance(db, s_id, y, m, d)
                                if existing_att:
                                    existing_att.start_overtime = start_dt
                                    existing_att.end_overtime = end_dt
                                    db.add(existing_att)
                                else:
                                    new_att = Attendance(
                                        employee_id=s_id,
                                        year=y,
                                        month=m,
                                        day=d,
                                        date_str=ds_vn,
                                        start_overtime=start_dt,
                                        end_overtime=end_dt
                                    )
                                    db.add(new_att)
                                
                                db.commit()
                                response += f"\n\n✅ <b>Đã cập nhật giờ tăng ca vào hệ thống chấm công.</b>"
                        except Exception as e:
                            LogError(f"Time parse error in OT recording: {e}", LogType.SYSTEM_STATUS)
            except Exception as e:
                LogError(f"Error recording overtime: {e}", LogType.SYSTEM_STATUS)
            finally:
                db.close()

    # Automated Attendance Recording
    if command in ["accepted", "confirmed"] and "YÊU CẦU CẬP NHẬT CHẤM CÔNG" in content:
        d_match = re.search(r"Thời gian:\s*(?:<code>)?(.*?)(?:</code>)?(?:\n|$)", content)
        s_match = re.search(r"Ca làm:\s*(?:<b>)?(.*?)(?:</b>)?(?:\n|$)", content)
        u_match = re.search(r"Người yêu cầu:.*?\(\s*(?:<b>)?@([^\s<]+)(?:</b>)?\s*\)", content)

        if d_match and s_match and u_match:
            att_date_str = d_match.group(1).strip()
            att_shift = s_match.group(1).strip()
            att_username = u_match.group(1).strip()

            db = SessionLocal()
            try:
                # Parse date
                att_date = None
                if "/" in att_date_str:
                    d_parts = att_date_str.split("/")
                    try:
                        if len(d_parts[0]) == 4: # yyyy/mm/dd
                            att_date = datetime.datetime.strptime(att_date_str, "%Y/%m/%d")
                        else: # dd/mm/yyyy
                            att_date = datetime.datetime.strptime(att_date_str, "%d/%m/%Y")
                    except Exception as e:
                        LogError(f"Date parse error in Attendance recording: {e}", LogType.SYSTEM_STATUS)

                # Parse time range (TimeA - TimeB)
                if att_date and "-" in att_shift:
                    time_parts = att_shift.split("-")
                    if len(time_parts) == 2:
                        s_t_str = time_parts[0].strip()
                        e_t_str = time_parts[1].strip()
                        
                        try:
                            start_t = datetime.datetime.strptime(s_t_str, "%H:%M").time()
                            end_t = datetime.datetime.strptime(e_t_str, "%H:%M").time()
                            
                            start_dt = datetime.datetime.combine(att_date.date(), start_t)
                            end_dt = datetime.datetime.combine(att_date.date(), end_t)
                            
                            if end_dt < start_dt:
                                end_dt += datetime.timedelta(days=1)

                            from app.models.employee import Employee
                            emp = db.query(Employee).filter(Employee.username == att_username).first()
                            if emp:
                                s_id = emp.id
                                y, m, d = att_date.year, att_date.month, att_date.day
                                days_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
                                ds_vn = days_vn[att_date.weekday()]

                                existing_att = get_attendance(db, s_id, y, m, d)
                                if existing_att:
                                    existing_att.check_in_time = start_dt
                                    existing_att.check_out_time = end_dt
                                    db.add(existing_att)
                                else:
                                    new_att = Attendance(
                                        employee_id=s_id,
                                        year=y,
                                        month=m,
                                        day=d,
                                        date_str=ds_vn,
                                        check_in_time=start_dt,
                                        check_out_time=end_dt
                                    )
                                    db.add(new_att)
                                
                                db.commit()
                                response += f"\n\n<b>Đã cập nhật dữ liệu chấm công.</b>"
                        except Exception as e:
                            LogError(f"Time parse error in Attendance recording: {e}", LogType.SYSTEM_STATUS)
            except Exception as e:
                LogError(f"Error recording attendance update: {e}", LogType.SYSTEM_STATUS)
            finally:
                db.close()
    
    await replied_msg.reply_text(response, parse_mode=ParseMode.HTML)

@bot.on_deleted_messages()
async def deleted_messages_handler(client, messages: list[Message]) -> None:
    """Detect when a user deletes their request message and delete the linked summary."""
    for msg in messages:
        if not msg or not msg.chat:
            continue
        summary_id = request_tracker.get_summary_id(msg.chat.id, msg.id)
        if summary_id:
            try:
                await client.delete_messages(chat_id=msg.chat.id, message_ids=[summary_id])
                request_tracker.clear(msg.chat.id, msg.id)
                LogInfo(f"Auto-deleted summary message {summary_id} because source request {msg.id} was deleted.", LogType.SYSTEM_STATUS)
            except Exception as e:
                LogError(f"Failed to auto-delete linked summary {summary_id}: {e}", LogType.SYSTEM_STATUS)

@bot.on_message(filters.command(["register_bot_command", "dang_ky_lenh"]) | filters.regex(r"^@\w+\s+/(register_bot_command|dang_ky_lenh)\b"))
async def register_bot_command_handler(client, message: Message) -> None:
    chat_id = str(message.chat.id)
    db = SessionLocal()
    try:
        from pyrogram.types import BotCommand, BotCommandScopeChat
        from app.models.telegram import TelegramProjectMember
        from app.models.business import Projects

        # Tìm project của nhóm này (ưu tiên record có custom_title)
        project_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id,
            TelegramProjectMember.custom_title.isnot(None)
        ).first()
        if not project_member:
            project_member = db.query(TelegramProjectMember).filter(
                TelegramProjectMember.chat_id == chat_id
            ).first()

        if not project_member:
            await message.reply_text(
                "⚠️ Nhóm này chưa được đồng bộ vào dự án nào.\n"
                "Vui lòng sử dụng lệnh <code>/syncchat</code> trước.",
                parse_mode=ParseMode.HTML
            )
            return

        project = db.query(Projects).filter(Projects.id == project_member.project_id).first()
        if not project:
            await message.reply_text("⚠️ Không tìm thấy thông tin dự án.", parse_mode=ParseMode.HTML)
            return

        project_name = (project.project_name or "").lower()
        role = project_member.role or ""
        custom_title = project_member.custom_title or ""
        commands_to_set = []
        label = ""

        # ===================== OTHER =====================
        if "other" in project_name:
            if custom_title == "main_device":
                label = "Other (Device)"
                commands_to_set = [
                    BotCommand("other_tao_dien_thoai", "Tạo điện thoại mới"),
                    BotCommand("other_cap_nhat_dien_thoai", "Cập nhật điện thoại"),
                    BotCommand("other_xoa_dien_thoai", "Xóa điện thoại"),
                    BotCommand("other_tao_laptop", "Tạo laptop mới"),
                    BotCommand("other_cap_nhat_laptop", "Cập nhật laptop"),
                    BotCommand("other_xoa_laptop", "Xóa laptop"),
                    BotCommand("other_tao_sim", "Tạo SIM mới"),
                    BotCommand("other_cap_nhat_sim", "Cập nhật SIM"),
                    BotCommand("other_xoa_sim", "Xóa SIM"),
                    BotCommand("other_tao_app", "Tạo ứng dụng mới"),
                    BotCommand("other_cap_nhat_app", "Cập nhật ứng dụng"),
                    BotCommand("other_xoa_app", "Xóa ứng dụng"),
                    BotCommand("other_nhan_thiet_bi", "Nhận thiết bị"),
                    BotCommand("other_tra_thiet_bi", "Trả thiết bị"),
                    BotCommand("other_tra_cuu_thiet_bi", "Kiểm tra thiết bị"),
                    BotCommand("other_lich_su_thiet_bi", "Xem lịch sử thiết bị"),
                    BotCommand("other_danh_sach_thiet_bi", "Danh sách thiết bị"),
                    BotCommand("other_dong_bo_ung_dung", "Đồng bộ ứng dụng vào thiết bị"),
                    BotCommand("other_tao_giay_to", "Tạo giấy tờ mới"),
                    BotCommand("other_them_lich_hen", "Thêm lịch hẹn nhắc nhở"),
                    BotCommand("other_cap_nhat_giay_to", "Cập nhật giấy tờ"),
                    BotCommand("other_cap_nhat_lich_hen", "Cập nhật lịch hẹn"),
                    BotCommand("other_xoa_giay_to", "Xóa/Lưu trữ giấy tờ"),
                    BotCommand("other_xoa_lich_hen", "Xóa/Tắt lịch hẹn"),
                    BotCommand("other_danh_sach_giay_to", "Danh sách giấy tờ & lịch hẹn"),
                ]

            elif custom_title == "main_vehicle":
                label = "Other (Vehicle)"
                commands_to_set = [
                    BotCommand("other_tao_xe", "Tạo xe mới"),
                    BotCommand("other_cap_nhat_xe", "Cập nhật thông tin xe"),
                    BotCommand("other_xoa_xe", "Xóa xe"),
                    BotCommand("other_nhan_xe", "Nhận xe"),
                    BotCommand("other_tra_xe", "Trả xe"),
                    BotCommand("other_lich_su_xe", "Xem lịch sử xe"),
                ]

        # ===================== CREDIT =====================
        elif "credit" in project_name:
            if role == "main":
                label = "Credit (Main)"
                commands_to_set = [
                    BotCommand("credit_tao_khach_hang", "Tạo khách hàng"),
                    BotCommand("credit_cap_nhat_khach_hang", "Cập nhật khách hàng"),
                    BotCommand("credit_xem_khach_hang", "Xem thông tin khách hàng"),
                    BotCommand("credit_tao_hop_dong", "Tạo hợp đồng"),
                    BotCommand("credit_cap_nhat_hop_dong", "Cập nhật hợp đồng"),
                    BotCommand("credit_xem_hop_dong", "Xem hợp đồng"),
                    BotCommand("credit_huy_hop_dong", "Hủy hợp đồng"),
                    BotCommand("credit_gia_han_hop_dong", "Gia hạn hợp đồng"),
                    BotCommand("credit_danh_sach_hop_dong", "Danh sách hợp đồng"),
                    BotCommand("credit_xac_nhan_thanh_toan", "Xác nhận thanh toán"),
                    BotCommand("credit_xac_nhan_no_xau", "Xác nhận nợ xấu"),
                    BotCommand("credit_bao_cao_dong_tien", "Báo cáo dòng tiền"),
                    BotCommand("credit_doanh_thu", "Doanh thu"),
                ]
            else:
                label = "Credit (Member)"
                commands_to_set = [
                    BotCommand("credit_xem_khach_hang", "Xem thông tin khách hàng"),
                    BotCommand("credit_xem_hop_dong", "Xem hợp đồng"),
                    BotCommand("credit_xem_cong_no", "Xem công nợ"),
                ]

        # ===================== RENTAL =====================
        elif "rental" in project_name:
            if role == "main":
                label = "Rental (Main)"
                commands_to_set = [
                    BotCommand("rental_tao_khach_hang", "Tạo khách hàng"),
                    BotCommand("rental_kiem_tra_khach_hang", "Kiểm tra khách hàng"),
                    BotCommand("rental_tao_hop_dong", "Tạo hợp đồng"),
                    BotCommand("rental_cap_nhat_hop_dong", "Cập nhật hợp đồng"),
                    BotCommand("rental_kiem_tra_hop_dong", "Xem hợp đồng"),
                    BotCommand("rental_gia_han_hop_dong", "Gia hạn hợp đồng"),
                    BotCommand("rental_huy_hop_dong", "Hủy hợp đồng"),
                    BotCommand("rental_danh_sach_hop_dong", "Danh sách hợp đồng"),
                    BotCommand("rental_xac_nhan_thanh_toan", "Xác nhận thanh toán"),
                    BotCommand("rental_xac_nhan_no_xau", "Xác nhận nợ xấu"),
                    BotCommand("rental_xem_cong_no", "Xem công nợ"),
                    BotCommand("rental_doanh_thu", "Doanh thu"),
                    BotCommand("rental_bao_cao_dong_tien", "Báo cáo dòng tiền"),
                ]
            else:
                label = "Rental (Member)"
                commands_to_set = [
                    BotCommand("rental_kiem_tra_khach_hang", "Kiểm tra khách hàng"),
                    BotCommand("rental_kiem_tra_hop_dong", "Xem hợp đồng"),
                    BotCommand("rental_xem_cong_no", "Xem công nợ"),
                ]

        # ===================== TIẾN NGA =====================
        elif "tiến nga" in project_name or "tien nga" in project_name:
            if custom_title == "super_main":
                label = "Tiến Nga (Tổng Hợp)"

            # Lệnh chung cho tất cả nhóm main
            if custom_title and custom_title.startswith("main_") or custom_title == "super_main":
                commands_to_set.extend([
                    BotCommand("tien_nga_ds_nhom_member", "DS nhóm member"),
                    BotCommand("send_message", "Gửi thông báo"),
                ])
            if custom_title in ("super_main", "main_hr"):
                if custom_title != "super_main": label = "Tiến Nga (Quản Lý)"
                commands_to_set.extend([
                    BotCommand("tien_nga_tao_nhan_vien", "Thêm nhân viên"),
                    BotCommand("tien_nga_cap_nhat_nhan_vien", "Cập nhật nhân viên"),
                    BotCommand("tien_nga_xoa_nhan_vien", "Xóa nhân viên"),
                    BotCommand("tien_nga_giao_viec", "Giao việc"),
                    BotCommand("tien_nga_xuat_luong", "Xuất bảng lương"),
                    BotCommand("tien_nga_tao_lai_bang_cham_cong", "Tạo lại báo cáo chấm công"),
                    BotCommand("tien_nga_danh_sach_cong_viec", "Xem công việc của nhân viên"),      
                    BotCommand("tien_nga_xuat_danh_sach_luong", "Xuất bảng lương Excel"),
                    BotCommand("tien_nga_danh_sach_nhan_vien", "Xuất DS nhân viên Excel"),
                    BotCommand("tien_nga_danh_sach_cham_cong", "Xuất DS chấm công"),
                ])
            if custom_title in ("super_main", "main_supplier"):
                if custom_title != "super_main": label = "Tiến Nga (Nhà Cung Cấp)"
                commands_to_set.extend([
                    ## Khách hàng
                    BotCommand("tien_nga_tao_khach_hang", "Tạo khách hàng"),
                    BotCommand("tien_nga_kiem_tra_khach_hang", "Xem thông tin khách hàng"),
                    BotCommand("tien_nga_cap_nhat_khach_hang", "Cập nhật khách hàng"),
                    BotCommand("tien_nga_xoa_khach_hang", "Xóa khách hàng"),
                    BotCommand("tien_nga_ds_khach_hang", "Xuất DS khách hàng Excel"),
                    ## Điểm thu mua mủ
                    BotCommand("tien_nga_tao_diem_thu_mua", "Tạo điểm thu mua"),
                    BotCommand("tien_nga_danh_sach_diem_thu_mua", "Danh sách điểm thu mua"),
                    BotCommand("tien_nga_cap_nhat_diem_thu_mua", "Cập nhật điểm thu mua"),
                    ## Thu mua
                    BotCommand("tien_nga_thu_mua_hang_ngay", "Nhập mua mủ hàng ngày"),
                    BotCommand("tien_nga_kiem_soat_hao_hut", "Kiểm soát hao hụt"),
                    BotCommand("tien_nga_kiem_tra_hao_hut", "Kiểm tra hao hụt"),
                    BotCommand("tien_nga_thong_ke_hao_hut", "Thống kê hao hụt Excel"),
                    BotCommand("tien_nga_xuat_bao_cao_thu_mua", "Xuất báo cáo mua mủ KH"),
                    ## Báo cáo
                    BotCommand("tien_nga_truy_xuat_tt_thu_mua", "Truy xuất TT thu mua"),
                    BotCommand("tien_nga_bieu_do_thu_mua", "Biểu đồ thu mua mủ"),
                    BotCommand("tien_nga_bao_cao_da_thanh_toan", "Báo cáo đã thanh toán"),
                    BotCommand("tien_nga_xuat_bao_cao_tong_hop", "Báo cáo tổng hợp Excel"),
                    BotCommand("tien_nga_bao_cao_luu_so", "Báo cáo lưu sổ"),
                    BotCommand("tien_nga_thong_ke_cong_no", "Thống kê công nợ"),
                    ## Điểm thu mua nguyên liệu
                    BotCommand("tien_nga_thu_mua_nguyen_lieu", "Nhập thu mua nguyên liệu"),
                    BotCommand("tien_nga_xuat_kho", "Xuất kho nguyên liệu"),
                    ## Ứng tiền
                    BotCommand("tien_nga_ung_tien", "Ứng tiền"),
                    BotCommand("tien_nga_khau_tru_tien_ung", "Khấu trừ tiền ứng"),

                ])

            if custom_title in ("super_main", "main_partner"):
                if custom_title != "super_main": label = "Tiến Nga (Đối Tác)"
                commands_to_set.extend([
                    BotCommand("tien_nga_tao_doi_tac", "Tạo đối tác"),
                    BotCommand("tien_nga_cap_nhat_doi_tac", "Cập nhật đối tác"),
                    BotCommand("tien_nga_xoa_doi_tac", "Xóa đối tác"),
                    BotCommand("tien_nga_ds_doi_tac", "Danh sách đối tác"),
                    BotCommand("tien_nga_giao_dich_doi_tac", "Giao dịch đối tác"),
                    BotCommand("tien_nga_kiem_tra_giao_dich", "Kiểm tra giao dịch ĐT"),
                    BotCommand("tien_nga_kiem_tra_cong_no", "Kiểm tra công nợ"),
                    BotCommand("tien_nga_thanh_toan_cong_no", "Thanh toán công nợ"),
                    BotCommand("tien_nga_yeu_cau_thu_chi", "Yêu cầu thu/chi"),
                    BotCommand("tien_nga_bao_cao_doi_tac", "Báo cáo tổng hợp đối tác"),
                ])

            if custom_title == "main_sales":
                label = "Tiến Nga (Kinh Doanh)"

            if custom_title == "main_shareholder":
                label = "Tiến Nga (Cổ Đông)"
                commands_to_set.extend([
                    BotCommand("tien_nga_kiem_tra_quy_dau_tu", "Kiểm tra Quỹ Đầu Tư"),
                    BotCommand("tien_nga_tao_co_dong", "Tạo cổ đông quỹ"),
                    BotCommand("tien_nga_chia_co_tuc", "Chia cổ tức quỹ"),
                    BotCommand("tien_nga_thanh_toan_co_dong", "Thanh toán quỹ cổ đông"),
                    BotCommand("tien_nga_lich_su_gd", "Lịch sử GD cổ đông"),
                    BotCommand("tien_nga_tao_dau_tu", "Tạo khoản đầu tư"),
                ])

            if custom_title in ("super_main", "main_finance"):
                if custom_title != "super_main": label = "Tiến Nga (Tài Chính)"
                commands_to_set.extend([
                    ## Cổ đông
                    BotCommand("tien_nga_kiem_tra_quy_dau_tu", "Kiểm tra Quỹ Đầu Tư"),
                    BotCommand("tien_nga_tao_co_dong", "Tạo cổ đông quỹ"),
                    BotCommand("tien_nga_chia_co_tuc", "Chia cổ tức quỹ"),
                    BotCommand("tien_nga_thanh_toan_co_dong", "Thanh toán quỹ cổ đông"),
                    BotCommand("tien_nga_lich_su_gd", "Lịch sử GD cổ đông"),
                    BotCommand("tien_nga_tao_dau_tu", "Tạo khoản đầu tư"),
                    ## Giao dịch
                    BotCommand("tien_nga_xn_thanh_toan_cong_no", "Xác nhận thanh toán công nợ"),
                    BotCommand("tien_nga_thanh_toan_cong_no", "Thanh toán công nợ"),
                    BotCommand("tien_nga_yeu_cau_thu_chi", "Yêu cầu thu/chi"),
                    BotCommand("tien_nga_xuat_bao_cao_thu_chi", "Xuất báo cáo thu chi Excel"),
                    BotCommand("tien_nga_xuat_bc_tong_hop", "Báo cáo tổng hợp tài chính"),
                    BotCommand("tien_nga_ung_tien", "Ứng tiền"),
                    BotCommand("tien_nga_khau_tru_tien_ung", "Khấu trừ tiền ứng"),
                    BotCommand("confirm_payment", "Duyệt phiếu chi"),
                    BotCommand("deny_payment", "Huỷ phiếu chi"),
                ])

            if custom_title in ("super_main", "main_inventory"):
                if custom_title != "super_main": label = "Tiến Nga (Kho)"
                commands_to_set.extend([
                    BotCommand("tien_nga_tao_kho", "Tạo kho"),
                    BotCommand("tien_nga_danh_sach_kho", "Danh sách kho"),
                    BotCommand("tien_nga_kiem_tra_kho", "Kiểm tra kho"),
                    BotCommand("tien_nga_cap_nhat_ton_kho", "Cập nhật tồn kho"),
                    BotCommand("tien_nga_thu_mua_nguyen_lieu", "Thu mua nguyên liệu"),
                    BotCommand("tien_nga_xuat_kho", "Xuất kho"),
                ])

            if custom_title in ("super_main", "main_product"):
                if custom_title != "super_main": label = "Tiến Nga (Sản Phẩm)"
                commands_to_set.extend([
                    BotCommand("tien_nga_tao_kho", "Tạo kho"),
                    BotCommand("tien_nga_danh_sach_kho", "Danh sách kho"),
                    BotCommand("tien_nga_kiem_tra_kho", "Kiểm tra kho"),
                    BotCommand("tien_nga_cap_nhat_ton_kho", "Cập nhật tồn kho"),
                    BotCommand("tien_nga_giao_dich_san_pham", "Giao dịch sản phẩm"),
                    BotCommand("tien_nga_xuat_bao_cao_san_pham", "Xuất báo cáo sản phẩm"),
                    BotCommand("tien_nga_kiem_tra_hao_hut", "Kiểm tra hao hụt"),
                ])


            ## Member
            if custom_title == "member_hr":
                label = "Tiến Nga (Nhân Viên)"
                commands_to_set.extend([
                    BotCommand("tien_nga_cham_cong", "Chấm công vào ca"),
                    BotCommand("tien_nga_tan_ca", "Tan ca / Kết thúc ca"),
                    BotCommand("tien_nga_xin_nghi_phep", "Xin nghỉ phép"),
                    BotCommand("tien_nga_dang_ky_tang_ca", "Đăng ký tăng ca"),
                    BotCommand("tien_nga_xem_cham_cong", "Xem chấm công"),
                    BotCommand("tien_nga_xem_nghi_phep", "Xem danh sách nghỉ phép"),
                    BotCommand("tien_nga_xem_cong_viec", "Xem công việc được giao"),
                    BotCommand("tien_nga_cap_nhat_cong", "Yêu cầu cập nhật chấm công"),
                ])
            if custom_title == "member_shareholder":
                label = "Tiến Nga (Cổ Đông)"
                commands_to_set.extend([
                    BotCommand("tien_nga_kiem_tra_quy_dau_tu", "Kiểm tra Quỹ Đầu Tư"),
                    BotCommand("tien_nga_lich_su_gd", "Lịch sử GD cổ đông"),
                ])

            if custom_title == "member_finance":
                label = "Tiến Nga (Tài Chính)"

            if custom_title == "member_partner":
                label = "Tiến Nga (Đối Tác)"
                commands_to_set.extend([
                    BotCommand("tien_nga_kiem_tra_giao_dich", "Kiểm tra giao dịch"),
                    BotCommand("tien_nga_kiem_tra_cong_no", "Kiểm tra công nợ"),
                    BotCommand("tien_nga_doi_tac_thanh_toan", "Yêu cầu thanh toán"),
                ])

            if custom_title == "member_inventory":
                label = "Tiến Nga (Kho)"

            if custom_title == "member_product":
                label = "Tiến Nga (Sản Phẩm)"

            if custom_title == "member_supplier":
                label = "Tiến Nga (Nhà Cung Cấp)"
                commands_to_set.extend([
                    BotCommand("tien_nga_kiem_tra_khach_hang", "Kiểm tra thông tin khách hàng"),
                    BotCommand("tien_nga_xuat_bao_cao_thu_mua", "Xuất báo cáo thu mua")
                ])

        # ===================== THU HOẠCH =====================
        elif "thu hoạch" in project_name:
            if custom_title in ("main_harvest",):
                label = "Thu Hoạch"
                commands_to_set = [
                    ## Đất & Hộ dân
                    BotCommand("tien_nga_tao_dat_trong_trot", "Tạo đất trồng trọt"),
                    BotCommand("tien_nga_cap_nhat_dat_trong_trot", "Cập nhật đất trồng trọt"),
                    BotCommand("tien_nga_xoa_dat_trong_trot", "Xóa đất trồng trọt"),
                    BotCommand("tien_nga_ds_dat_trong_trot", "DS đất trồng trọt"),
                    BotCommand("tien_nga_kt_dat_trong_trot", "KT đất trồng trọt"),
                    BotCommand("tien_nga_tao_ho_dan", "Tạo hộ dân"),
                    BotCommand("tien_nga_cap_nhat_ho_dan", "Cập nhật hộ dân"),
                    BotCommand("tien_nga_xoa_ho_dan", "Xóa hộ dân"),
                    BotCommand("tien_nga_ds_ho_dan", "DS hộ dân"),
                    ## Cao su
                    BotCommand("tien_nga_kiem_tra_thu_hoach", "Kiểm tra thu hoạch"),
                    BotCommand("tien_nga_so_sanh_thu_hoach", "So sánh thu hoạch"),
                    BotCommand("tien_nga_kt_thu_hoach_hang_ngay", "KT thu hoạch hàng ngày"),
                    BotCommand("tien_nga_cay_cao_su", "Quản lý cây cao su"),
                    BotCommand("tien_nga_kt_cay_cao_su", "Kiểm tra cây cao su"),
                    ## Sầu riêng
                    BotCommand("tien_nga_cay_sau_rieng", "Quản lý cây sầu riêng"),
                    BotCommand("tien_nga_kt_cay_sau_rieng", "Kiểm tra cây sầu riêng"),
                    BotCommand("tien_nga_thu_hoach_sau_rieng", "Thu hoạch sầu riêng"),
                    BotCommand("tien_nga_kt_thu_hoach_sr", "KT thu hoạch sầu riêng"),
                    ## Tài chính thu hoạch
                    BotCommand("tien_nga_yeu_cau_thu_chi", "Yêu cầu thu/chi"),
                    BotCommand("tien_nga_thanh_toan_cong_no", "Thanh toán công nợ"),
                    BotCommand("tien_nga_them_vat_tu", "Thêm chi phí vật tư"),
                    BotCommand("tien_nga_kt_vat_tu", "Báo cáo chi phí vật tư"),
                    BotCommand("tien_nga_xoa_vat_tu", "Xóa chi phí vật tư"),
                ]
            elif custom_title in ("member_harvest",):
                label = "Thu Hoạch (Member)"
                commands_to_set = [
                    BotCommand("tien_nga_thu_hoach_hang_ngay", "Thu hoạch cao su hàng ngày"),
                    BotCommand("tien_nga_thu_hoach_sr_hang_ngay", "Thu hoạch SR hàng ngày"),
                    BotCommand("tien_nga_kiem_tra_ho_dan", "Kiểm tra hộ dân"),
                ]

        # ===================== HỤI =====================
        elif "hụi" in project_name.lower() or "hui" in project_name.lower():
            if role == "main":
                label = "Hụi (Quản Lý)"
                commands_to_set = [
                    BotCommand("hui_tao_nguoi_choi", "Tạo người chơi"),
                    BotCommand("hui_cap_nhat_nguoi_choi", "Cập nhật người chơi"),
                    BotCommand("hui_xoa_nguoi_choi", "Xóa người chơi"),
                    BotCommand("hui_tao_day_hui", "Tạo dây hụi"),
                    BotCommand("hui_cap_nhat_day_hui", "Cập nhật dây hụi"),
                    BotCommand("hui_xoa_day_hui", "Xóa dây hụi"),
                    BotCommand("hui_tao_chan_hui", "Tạo chân hụi"),
                    BotCommand("hui_cap_nhat_chan_hui", "Cập nhật chân hụi"),
                    BotCommand("hui_xoa_chan_hui", "Xóa chân hụi"),
                    BotCommand("hui_kiem_tra_chan_hui", "Kiểm tra chân hụi"),
                    BotCommand("hui_kiem_tra_dong_hui", "Kiểm tra đóng hụi"),
                    BotCommand("hui_thong_ke_hui", "Thống kê hụi"),
                    BotCommand("hui_rut_day_hui", "Rút dây hụi/hốt hụi"),
                    BotCommand("hui_tinh_lai_gia_lap", "Tính lãi giả lập"),
                ]
            else:
                label = "Hụi (Người Chơi)"
                commands_to_set = [
                    BotCommand("hui_kiem_tra_chan_hui", "Kiểm tra chân hụi"),
                    BotCommand("hui_kiem_tra_dong_hui", "Kiểm tra đóng hụi"),
                    BotCommand("hui_thong_ke_hui", "Thống kê hụi"),
                    BotCommand("hui_dong_tien_chan_hui", "Đóng tiền chân hụi"),
                    BotCommand("hui_rut_day_hui", "Rút dây hụi/hốt hụi"),
                    BotCommand("hui_tinh_lai_gia_lap", "Tính lãi giả lập"),
                ]

        # ===================== GGOMOONSIN =====================
        elif "ggomoonsin" in project_name.lower():
            if custom_title == "super_main":
                label = "GGoMoonSin (Tổng Hợp)"

            # Lệnh chung cho tất cả nhóm main
            if custom_title and custom_title.startswith("main_") or custom_title == "super_main":
                commands_to_set.extend([
                    BotCommand("send_message", "Gửi thông báo"),
                ])
            if custom_title in ("super_main", "main_hr"):
                if custom_title != "super_main": label = "GGoMoonSin (Quản Lý)"
                commands_to_set.extend([
                    BotCommand("ggomoonsin_tao_nhan_vien", "Thêm nhân viên"),
                    BotCommand("ggomoonsin_cap_nhat_nhan_vien", "Cập nhật nhân viên"),
                    BotCommand("ggomoonsin_xoa_nhan_vien", "Xóa nhân viên"),
                    BotCommand("ggomoonsin_giao_viec", "Giao việc"),
                    BotCommand("ggomoonsin_xuat_luong", "Xuất bảng lương"),
                    BotCommand("ggomoonsin_tao_lai_cham_cong", "Tạo lại báo cáo chấm công"),
                    BotCommand("ggomoonsin_danh_sach_cong_viec", "Xem công việc của nhân viên"),
                    BotCommand("ggomoonsin_xuat_danh_sach_luong", "Xuất bảng lương Excel"),
                    BotCommand("ggomoonsin_danh_sach_nhan_vien", "Xuất DS nhân viên Excel"),
                    BotCommand("ggomoonsin_danh_sach_cham_cong", "Xuất DS chấm công"),
                ])
            ## Member
            if custom_title == "member_hr":
                label = "GGoMoonSin (Nhân Viên)"
                commands_to_set.extend([
                    BotCommand("ggomoonsin_cham_cong", "Chấm công vào ca"),
                    BotCommand("ggomoonsin_tan_ca", "Tan ca / Kết thúc ca"),
                    BotCommand("ggomoonsin_xin_nghi_phep", "Xin nghỉ phép"),
                    BotCommand("ggomoonsin_dang_ky_tang_ca", "Đăng ký tăng ca"),
                    BotCommand("ggomoonsin_xem_cham_cong", "Xem chấm công"),
                    BotCommand("ggomoonsin_xem_nghi_phep", "Xem danh sách nghỉ phép"),
                    BotCommand("ggomoonsin_xem_cong_viec", "Xem công việc được giao"),
                    BotCommand("ggomoonsin_cap_nhat_cong", "Yêu cầu cập nhật chấm công"),
                ])

        if not commands_to_set:
            await message.reply_text(
                f"⚠️ Không tìm thấy danh sách lệnh cho dự án <b>{project.project_name}</b> "
                f"(role: {role}, custom_title: {custom_title or 'N/A'}).",
                parse_mode=ParseMode.HTML
            )
            return

        await bot.set_bot_commands(
            commands_to_set,
            scope=BotCommandScopeChat(chat_id=int(chat_id))
        )

        await message.reply_text(
            f"✅ Đã đăng ký <b>{len(commands_to_set)}</b> gợi ý lệnh cho nhóm này!\n\n"
            f"<b>Dự án:</b> {project.project_name}\n"
            f"<b>Loại:</b> {label}\n\n"
            f"💡 Nhấn <b>/</b> trong ô chat để xem danh sách lệnh.",
            parse_mode=ParseMode.HTML
        )
        LogInfo(f"[RegisterBotCommand] Registered {len(commands_to_set)} commands for {label} in group {chat_id} by @{message.from_user.username or message.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        LogError(f"Error in register_bot_command_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# =========================================================================================
# LỆNH: /list_all_group  /danh_sach_nhom
# =========================================================================================

_LAG_PAGE_SIZE = 10  # Số nhóm hiển thị mỗi trang


@bot.on_message(filters.command(["list_all_group", "danh_sach_nhom"]) | filters.regex(r"^@\w+\s+/(list_all_group|danh_sach_nhom)\b"))
async def list_all_group_handler(client, message: Message) -> None:
    """
    /list_all_group (/danh_sach_nhom) — Chỉ hoạt động trong nhóm Chat_ID_Main.
    Hiển thị danh sách các dự án để chọn, sau đó hiển thị các nhóm thuộc dự án đó.
    """
    from bot.core.config import settings as bot_settings
    from bot.utils.utils import check_command_target

    args = await check_command_target(client, message.text, ["list_all_group", "danh_sach_nhom"])
    if args is None:
        return

    # Kiểm tra Chat_ID_Main
    chat_id_main = bot_settings.CHAT_ID_MAIN
    if not chat_id_main or str(message.chat.id) != chat_id_main:
        await message.reply_text(
            "⚠️ Lệnh này chỉ được sử dụng trong nhóm <b>Main</b> đã được cấu hình.",
            parse_mode=ParseMode.HTML
        )
        return

    db = SessionLocal()
    try:
        from app.models.business import Projects
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        projects = db.query(Projects).order_by(Projects.project_name).all()

        if not projects:
            await message.reply_text("⚠️ Chưa có dự án nào trong hệ thống.", parse_mode=ParseMode.HTML)
            return

        buttons = []
        for p in projects:
            p_id_short = str(p.id).replace("-", "")[:24]  # Rút gọn UUID cho callback_data
            buttons.append([InlineKeyboardButton(f"{p.project_name}", callback_data=f"lag_proj_{p_id_short}_0")])
        buttons.append([InlineKeyboardButton("Hủy", callback_data="lag_cancel")])

        keyboard = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            "<b>DANH SÁCH NHÓM THEO DỰ ÁN</b>\n\n"
            "Vui lòng chọn dự án để xem danh sách các nhóm:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        LogError(f"Error in list_all_group_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


def _build_lag_group_page(project_name, groups_data, page, page_size, total_pages, project_id_short):
    """Build text + inline keyboard for a page of groups within a project."""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    start = page * page_size
    end = start + page_size
    page_groups = groups_data[start:end]
    total = len(groups_data)

    text = (
        f"<b>DANH SÁCH NHÓM — {project_name}</b>\n"
        f"<i>Tổng: {total} nhóm · Trang {page + 1}/{total_pages}</i>\n"
        f"{'━' * 30}\n\n"
    )

    for idx, g in enumerate(page_groups, start=start + 1):
        group_name = g["group_name"] or "N/A"
        role = (g["role"] or "—").upper()
        member_count = g["member_count"]
        owners = g["owners"] or "—"
        admins = g["admins"] or "—"

        text += (
            f"<b>{idx}. {group_name}</b>\n"
            f"Role: <code>{role}</code>\n"
            f"Thành viên: <b>{member_count}</b>\n"
            f"Owner: {owners}\n"
            f"Admin: {admins}\n\n"
        )

    # Truncate if too long
    if len(text) > 3900:
        text = text[:3850] + "\n\n<i>... (nội dung bị cắt do giới hạn hiển thị)</i>"

    # Build navigation buttons
    nav_buttons = []
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("Trước", callback_data=f"lag_proj_{project_id_short}_{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="lag_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Sau", callback_data=f"lag_proj_{project_id_short}_{page + 1}"))
    if nav_row:
        nav_buttons.append(nav_row)

    nav_buttons.append([InlineKeyboardButton("Quay lại", callback_data="lag_back")])
    nav_buttons.append([InlineKeyboardButton("Đóng", callback_data="lag_cancel")])

    markup = InlineKeyboardMarkup(nav_buttons)
    return text, markup


def _query_groups_for_project(db, project_id):
    """Query all groups in a project, compute member count, owners, admins per group."""
    from app.models.telegram import TelegramProjectMember
    from sqlalchemy import func

    # Get distinct groups in this project
    group_rows = db.query(
        TelegramProjectMember.chat_id,
        TelegramProjectMember.group_name,
        TelegramProjectMember.role,
    ).filter(
        TelegramProjectMember.project_id == project_id
    ).distinct(
        TelegramProjectMember.chat_id
    ).all()

    # Build a set of unique chat_ids
    seen_chat_ids = set()
    unique_groups = []
    for row in group_rows:
        if row.chat_id not in seen_chat_ids:
            seen_chat_ids.add(row.chat_id)
            unique_groups.append(row)

    groups_data = []
    for row in unique_groups:
        chat_id = row.chat_id

        # Count members
        member_count = db.query(func.count(TelegramProjectMember.id)).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.chat_id == chat_id
        ).scalar() or 0

        # Get owners
        owners_q = db.query(TelegramProjectMember.full_name, TelegramProjectMember.user_name).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.chat_id == chat_id,
            TelegramProjectMember.member_status == "OWNER"
        ).all()
        owners_list = []
        for o in owners_q:
            name = o.full_name or o.user_name or "N/A"
            if o.user_name:
                name += f" (@{o.user_name})"
            owners_list.append(name)
        owners_str = ", ".join(owners_list) if owners_list else "—"

        # Get admins
        admins_q = db.query(TelegramProjectMember.full_name, TelegramProjectMember.user_name).filter(
            TelegramProjectMember.project_id == project_id,
            TelegramProjectMember.chat_id == chat_id,
            TelegramProjectMember.member_status == "ADMINISTRATOR"
        ).all()
        admins_list = []
        for a in admins_q:
            name = a.full_name or a.user_name or "N/A"
            if a.user_name:
                name += f" (@{a.user_name})"
            admins_list.append(name)
        admins_str = ", ".join(admins_list) if admins_list else "—"

        groups_data.append({
            "chat_id": chat_id,
            "group_name": row.group_name,
            "role": row.role,
            "member_count": member_count,
            "owners": owners_str,
            "admins": admins_str,
        })

    # Sort: main groups first, then by group name
    groups_data.sort(key=lambda g: (0 if g["role"] == "main" else 1, g["group_name"] or ""))
    return groups_data


@bot.on_callback_query(filters.regex(r"^lag_proj_([a-f0-9]+)_(\d+)$"))
async def lag_project_callback(client, callback_query):
    """Callback khi chọn dự án hoặc chuyển trang."""
    from pyrogram.types import CallbackQuery
    project_id_short = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))

    from app.models.business import Projects

    db = SessionLocal()
    try:
        # Tìm project bằng prefix UUID
        projects = db.query(Projects).all()
        project = None
        for p in projects:
            if str(p.id).replace("-", "").startswith(project_id_short):
                project = p
                break

        if not project:
            await callback_query.answer("⚠️ Không tìm thấy dự án.", show_alert=True)
            return

        # Query groups
        groups_data = _query_groups_for_project(db, project.id)

        if not groups_data:
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Quay lại", callback_data="lag_back")],
                [InlineKeyboardButton("Đóng", callback_data="lag_cancel")]
            ])
            await callback_query.message.edit_text(
                f"<b>DANH SÁCH NHÓM — {project.project_name}</b>\n\n"
                f"<i>Chưa có nhóm nào trong dự án này.</i>",
                reply_markup=kb,
                parse_mode=ParseMode.HTML
            )
            await callback_query.answer()
            return

        total = len(groups_data)
        total_pages = max(1, (total + _LAG_PAGE_SIZE - 1) // _LAG_PAGE_SIZE)

        if page < 0 or page >= total_pages:
            page = 0

        text, markup = _build_lag_group_page(project.project_name, groups_data, page, _LAG_PAGE_SIZE, total_pages, project_id_short)
        await callback_query.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        await callback_query.answer()

    except Exception as e:
        LogError(f"Error in lag_project_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^lag_back$"))
async def lag_back_callback(client, callback_query):
    """Quay lại danh sách dự án."""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from app.models.business import Projects

    db = SessionLocal()
    try:
        projects = db.query(Projects).order_by(Projects.project_name).all()

        buttons = []
        for p in projects:
            p_id_short = str(p.id).replace("-", "")[:24]
            buttons.append([InlineKeyboardButton(f"{p.project_name}", callback_data=f"lag_proj_{p_id_short}_0")])
        buttons.append([InlineKeyboardButton("Hủy", callback_data="lag_cancel")])

        keyboard = InlineKeyboardMarkup(buttons)
        await callback_query.message.edit_text(
            "<b>DANH SÁCH NHÓM THEO DỰ ÁN</b>\n\n"
            "Vui lòng chọn dự án để xem danh sách các nhóm:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer()

    except Exception as e:
        LogError(f"Error in lag_back_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^lag_cancel$"))
async def lag_cancel_callback(client, callback_query):
    """Hủy / Đóng tin nhắn."""
    await callback_query.message.delete()


@bot.on_callback_query(filters.regex(r"^lag_noop$"))
async def lag_noop_callback(client, callback_query):
    """No-op callback cho nút hiển thị số trang."""
    await callback_query.answer()


# =========================================================================================
# LỆNH: /create_project  /tao_du_an
# =========================================================================================

@bot.on_message(filters.command(["create_project", "tao_du_an"]) & ~filters.regex(r"\n"))
async def create_project_handler(client, message: Message) -> None:
    """
    /create_project (/tao_du_an) — Chỉ hoạt động trong nhóm Chat_ID_Main.
    Hiển thị form để người dùng điền tên dự án.
    """
    from bot.core.config import settings as bot_settings
    from bot.utils.utils import check_command_target

    args = await check_command_target(client, message.text, ["create_project", "tao_du_an"])
    if args is None:
        return

    # Kiểm tra Chat_ID_Main
    chat_id_main = bot_settings.CHAT_ID_MAIN
    if not chat_id_main or str(message.chat.id) != chat_id_main:
        await message.reply_text(
            "⚠️ Lệnh này chỉ được sử dụng trong nhóm <b>Main</b> đã được cấu hình.",
            parse_mode=ParseMode.HTML
        )
        return

    form_text = (
        "<b>TẠO DỰ ÁN MỚI</b>\n\n"
        "Sao chép form dưới đây, điền thông tin và gửi lại:\n\n"
        "<pre>/tao_du_an\n"
        "Tên Dự Án: </pre>"
    )
    await message.reply_text(form_text, parse_mode=ParseMode.HTML)


@bot.on_message(filters.regex(r"^/(create_project|tao_du_an)\n") & filters.group)
async def create_project_form_handler(client, message: Message) -> None:
    """Xử lý form tạo dự án khi người dùng gửi multi-line."""
    from bot.core.config import settings as bot_settings
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    # Kiểm tra Chat_ID_Main
    chat_id_main = bot_settings.CHAT_ID_MAIN
    if not chat_id_main or str(message.chat.id) != chat_id_main:
        return

    lines = message.text.strip().split("\n")
    if len(lines) < 2:
        await message.reply_text(
            "⚠️ Form không hợp lệ. Vui lòng điền đầy đủ thông tin.",
            parse_mode=ParseMode.HTML
        )
        return

    # Parse form data
    data = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()

    project_name = data.get("Tên Dự Án", data.get("Ten Du An", "")).strip()

    if not project_name:
        await message.reply_text(
            "⚠️ <b>Tên Dự Án</b> là bắt buộc. Vui lòng điền tên dự án.",
            parse_mode=ParseMode.HTML
        )
        return

    # Kiểm tra trùng tên
    db = SessionLocal()
    try:
        from app.models.business import Projects

        existing = db.query(Projects).filter(
            Projects.project_name.ilike(project_name)
        ).first()

        if existing:
            await message.reply_text(
                f"⚠️ Dự án với tên <b>{project_name}</b> đã tồn tại trong hệ thống.",
                parse_mode=ParseMode.HTML
            )
            return

        # Hiển thị xác nhận
        # Encode tên dự án vào callback_data (giới hạn 64 bytes)
        # Dùng message_id để lưu context thay vì encode tên dài
        import hashlib
        name_hash = hashlib.md5(project_name.encode()).hexdigest()[:12]

        # Lưu tạm tên dự án vào dict in-memory
        _pending_projects[name_hash] = project_name

        confirm_text = (
            "<b>XÁC NHẬN TẠO DỰ ÁN</b>\n"
            f"{'━' * 20}\n\n"
            f"<b>Tên Dự Án:</b> {project_name}\n\n"
            f"Bạn có chắc chắn muốn tạo dự án này?"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Xác nhận", callback_data=f"cp_confirm_{name_hash}"),
                InlineKeyboardButton("Hủy", callback_data="cp_cancel")
            ]
        ])

        await message.reply_text(confirm_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    except Exception as e:
        LogError(f"Error in create_project_form_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


# In-memory dict để lưu tạm tên dự án chờ xác nhận
_pending_projects = {}


@bot.on_callback_query(filters.regex(r"^cp_confirm_([a-f0-9]+)$"))
async def cp_confirm_callback(client, callback_query):
    """Xác nhận tạo dự án."""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    import uuid as uuid_lib

    name_hash = callback_query.matches[0].group(1)
    project_name = _pending_projects.pop(name_hash, None)

    if not project_name:
        await callback_query.answer("⚠️ Phiên tạo dự án đã hết hạn. Vui lòng thực hiện lại.", show_alert=True)
        return

    db = SessionLocal()
    try:
        from app.models.business import Projects

        # Kiểm tra trùng lần nữa
        existing = db.query(Projects).filter(
            Projects.project_name.ilike(project_name)
        ).first()

        if existing:
            await callback_query.message.edit_text(
                f"⚠️ Dự án <b>{project_name}</b> đã tồn tại.",
                parse_mode=ParseMode.HTML
            )
            await callback_query.answer()
            return

        new_project = Projects(
            id=uuid_lib.uuid4(),
            project_name=project_name
        )
        db.add(new_project)
        db.commit()

        await callback_query.message.edit_text(
            f"✅ <b>TẠO DỰ ÁN THÀNH CÔNG!</b>\n"
            f"{'━' * 20}\n\n"
            f"<b>Tên Dự Án:</b> {project_name}\n"
            f"<b>ID:</b> <code>{new_project.id}</code>\n\n"
            f"<i>Dự án đã được lưu vào hệ thống.</i>",
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer("Tạo dự án thành công!")
        LogInfo(f"[CreateProject] Created project '{project_name}' by @{callback_query.from_user.username or callback_query.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in cp_confirm_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi tạo dự án.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^cp_cancel$"))
async def cp_cancel_callback(client, callback_query):
    """Hủy tạo dự án."""
    await callback_query.message.edit_text(
        "❌ Đã hủy tạo dự án.",
        parse_mode=ParseMode.HTML
    )
    await callback_query.answer()


# =========================================================================================
# LỆNH: /delete_project  /xoa_du_an
# =========================================================================================

@bot.on_message(filters.command(["delete_project", "xoa_du_an"]) | filters.regex(r"^@\w+\s+/(delete_project|xoa_du_an)\b"))
async def delete_project_handler(client, message: Message) -> None:
    """
    /delete_project (/xoa_du_an) — Chỉ hoạt động trong nhóm Chat_ID_Main.
    Hiển thị danh sách các dự án để chọn xóa.
    """
    from bot.core.config import settings as bot_settings
    from bot.utils.utils import check_command_target

    args = await check_command_target(client, message.text, ["delete_project", "xoa_du_an"])
    if args is None:
        return

    # Kiểm tra Chat_ID_Main
    chat_id_main = bot_settings.CHAT_ID_MAIN
    if not chat_id_main or str(message.chat.id) != chat_id_main:
        await message.reply_text(
            "⚠️ Lệnh này chỉ được sử dụng trong nhóm <b>Main</b> đã được cấu hình.",
            parse_mode=ParseMode.HTML
        )
        return

    db = SessionLocal()
    try:
        from app.models.business import Projects
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        projects = db.query(Projects).order_by(Projects.project_name).all()

        if not projects:
            await message.reply_text("⚠️ Chưa có dự án nào trong hệ thống.", parse_mode=ParseMode.HTML)
            return

        buttons = []
        for p in projects:
            p_id_short = str(p.id).replace("-", "")[:24]
            buttons.append([InlineKeyboardButton(f"{p.project_name}", callback_data=f"dp_sel_{p_id_short}")])
        buttons.append([InlineKeyboardButton("Hủy", callback_data="dp_cancel")])

        keyboard = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            "<b>XÓA DỰ ÁN</b>\n\n"
            "⚠️ <i>Lưu ý: Việc xóa Dự án có thể ảnh hưởng tới nhiều dữ liệu trong Database. "
            "Hãy kiểm tra kỹ dữ liệu trước khi xóa Dự án.</i>\n\n"
            "Vui lòng chọn dự án cần xóa:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        LogError(f"Error in delete_project_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^dp_sel_([a-f0-9]+)$"))
async def dp_select_callback(client, callback_query):
    """Chọn dự án để xóa → hiển thị xác nhận."""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from app.models.business import Projects

    project_id_short = callback_query.matches[0].group(1)

    db = SessionLocal()
    try:
        projects = db.query(Projects).all()
        project = None
        for p in projects:
            if str(p.id).replace("-", "").startswith(project_id_short):
                project = p
                break

        if not project:
            await callback_query.answer("⚠️ Không tìm thấy dự án.", show_alert=True)
            return

        # Đếm số nhóm liên quan
        from app.models.telegram import TelegramProjectMember
        from sqlalchemy import func
        group_count = db.query(func.count(func.distinct(TelegramProjectMember.chat_id))).filter(
            TelegramProjectMember.project_id == project.id
        ).scalar() or 0

        member_count = db.query(func.count(TelegramProjectMember.id)).filter(
            TelegramProjectMember.project_id == project.id
        ).scalar() or 0

        confirm_text = (
            "<b>XÁC NHẬN XÓA DỰ ÁN</b>\n"
            f"{'━' * 20}\n\n"
            f"<b>Tên Dự Án:</b> {project.project_name}\n"
            f"<b>ID:</b> <code>{project.id}</code>\n"
            f"<b>Số nhóm liên quan:</b> {group_count}\n"
            f"<b>Số thành viên liên quan:</b> {member_count}\n\n"
            f"⚠️ <b>Lưu ý:</b> Việc xóa Dự án có thể ảnh hưởng tới nhiều dữ liệu "
            f"trong Database. Hãy kiểm tra kỹ dữ liệu trước khi xóa Dự án.\n\n"
            f"Bạn có chắc chắn muốn xóa dự án <b>{project.project_name}</b>?"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Xác nhận xóa", callback_data=f"dp_confirm_{project_id_short}"),
                InlineKeyboardButton("Hủy", callback_data="dp_cancel")
            ]
        ])

        await callback_query.message.edit_text(confirm_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await callback_query.answer()

    except Exception as e:
        LogError(f"Error in dp_select_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^dp_confirm_([a-f0-9]+)$"))
async def dp_confirm_callback(client, callback_query):
    """Xác nhận xóa dự án."""
    from app.models.business import Projects

    project_id_short = callback_query.matches[0].group(1)

    db = SessionLocal()
    try:
        projects = db.query(Projects).all()
        project = None
        for p in projects:
            if str(p.id).replace("-", "").startswith(project_id_short):
                project = p
                break

        if not project:
            await callback_query.answer("⚠️ Không tìm thấy dự án.", show_alert=True)
            return

        project_name = project.project_name
        project_id = str(project.id)

        db.delete(project)
        db.commit()

        await callback_query.message.edit_text(
            f"✅ <b>ĐÃ XÓA DỰ ÁN THÀNH CÔNG!</b>\n"
            f"{'━' * 20}\n\n"
            f"<b>Tên Dự Án:</b> {project_name}\n"
            f"<b>ID:</b> <code>{project_id}</code>\n\n"
            f"<i>Dự án đã được xóa khỏi hệ thống.</i>",
            parse_mode=ParseMode.HTML
        )
        await callback_query.answer("Xóa dự án thành công!")
        LogInfo(f"[DeleteProject] Deleted project '{project_name}' (ID: {project_id}) by @{callback_query.from_user.username or callback_query.from_user.id}", LogType.SYSTEM_STATUS)

    except Exception as e:
        db.rollback()
        LogError(f"Error in dp_confirm_callback: {e}", LogType.SYSTEM_STATUS)
        await callback_query.answer("❌ Có lỗi xảy ra khi xóa dự án.", show_alert=True)
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^dp_cancel$"))
async def dp_cancel_callback(client, callback_query):
    """Hủy xóa dự án."""
    await callback_query.message.edit_text(
        "❌ Đã hủy xóa dự án.",
        parse_mode=ParseMode.HTML
    )
    await callback_query.answer()


@bot.on_message(filters.command("kick_user") | filters.regex(r"^@\w+\s+/kick_user\b"))
async def kick_user_handler(client, message: Message) -> None:
    args = await check_command_target(client, message.text, "kick_user")
    if args is None: return

    from app.core.config import settings
    main_chat_id = settings.IMP_Config.Chat_ID_Main

    if str(message.chat.id) != str(main_chat_id):
        await message.reply_text("⚠️ Lệnh này chỉ được phép thực hiện trong nhóm main.", parse_mode=ParseMode.HTML)
        return

    # Check if admin/owner
    try:
        from pyrogram.enums import ChatMemberStatus
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("⚠️ Chỉ Admin hoặc Owner mới được sử dụng lệnh này.", parse_mode=ParseMode.HTML)
            return
    except Exception as e:
        LogError(f"Error checking admin status for /kick_user: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Không thể xác thực quyền của bạn.")
        return

    if len(args) < 2:
        await message.reply_text("⚠️ Cú pháp không hợp lệ. Vui lòng sử dụng: <code>/kick_user [username]</code>", parse_mode=ParseMode.HTML)
        return

    target_username = args[1]
    if target_username.startswith("@"):
        target_username = target_username[1:]

    try:
        user = await client.get_users(target_username)
        target_user_id = str(user.id)
        target_display = f"@{user.username}" if user.username else f"{user.first_name}"
    except Exception as e:
        target_user_id = target_username
        target_display = f"@{target_username}"

    db = SessionLocal()
    try:
        from app.models.business import Projects
        projects = db.query(Projects).all()
        
        buttons = []
        buttons.append([InlineKeyboardButton("Tất cả các nhóm trong các dự án", callback_data=f"ku_all_{target_user_id}")])
        
        for p in projects:
            p_id_short = str(p.id).replace("-", "")[:8]
            buttons.append([InlineKeyboardButton(p.project_name, callback_data=f"ku_p_{p_id_short}_{target_user_id}")])
            
        buttons.append([InlineKeyboardButton("Hủy", callback_data="ku_cancel")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            f"<b>XÓA NGƯỜI DÙNG</b>\n\nBạn muốn xóa <b>{target_display}</b> khỏi dự án nào?",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LogError(f"Error in kick_user_handler: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Có lỗi xảy ra khi lấy danh sách dự án.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ku_all_(.+)$"))
async def kick_user_all_callback(client, callback_query):
    target_user_id = callback_query.matches[0].group(1)
    target_uid = int(target_user_id) if target_user_id.isdigit() else target_user_id
    
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from pyrogram.enums import ChatMemberStatus
        groups = db.query(TelegramProjectMember.chat_id, TelegramProjectMember.group_name).distinct().all()
        
        await callback_query.message.edit_text(f"⏳ Đang kiểm tra thông tin thành viên trên {len(groups)} nhóm...")
        
        kickable_chats = []
        admin_chats = []
        last_ex = None
        
        for chat_id_val, group_name in groups:
            chat_id = int(chat_id_val)
            try:
                member = await client.get_chat_member(chat_id, target_uid)
                chat_title = group_name if group_name else str(chat_id)
                
                if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    admin_chats.append(chat_title)
                else:
                    kickable_chats.append(chat_title)
            except Exception as ex:
                last_ex = ex
                from pyrogram.errors import UserNotParticipant
                if not isinstance(ex, UserNotParticipant):
                    LogError(f"Error checking member {target_uid} in chat {chat_id}: {ex}", LogType.SYSTEM_STATUS)
                
        if not kickable_chats and not admin_chats:
            await callback_query.message.edit_text("⚠️ Người dùng này hiện không có mặt trong bất kỳ nhóm nào trên hệ thống.", parse_mode=ParseMode.HTML)
            return
            
        text = "<b>THÔNG TIN NHÓM ĐÃ THAM GIA:</b>\n\n"
        if kickable_chats:
            text += "✅ <b>Có thể xóa khỏi các nhóm sau:</b>\n"
            for t in kickable_chats:
                text += f"- {t}\n"
            text += "\n"
        if admin_chats:
            text += "❌ <b>Không thể xóa (vì là Admin/Owner):</b>\n"
            for t in admin_chats:
                text += f"- {t}\n"
            text += "\n"
            
        if not kickable_chats:
            text += "⚠️ <i>Thành viên này không có nhóm nào có thể bị xóa.</i>"
            await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML)
            return
            
        text += "❓ Bạn có chắc chắn muốn xóa thành viên này khỏi các nhóm hợp lệ không?"
        
        buttons = [
            [InlineKeyboardButton("Xác nhận", callback_data=f"ku_c_a_{target_user_id}")],
            [InlineKeyboardButton("Hủy", callback_data="ku_cancel")]
        ]
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)
    except Exception as e:
        LogError(f"Error in kick_user_all: {e}", LogType.SYSTEM_STATUS)
        await callback_query.message.edit_text("❌ Có lỗi xảy ra trong quá trình kiểm tra.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ku_c_a_(.+)$"))
async def kick_user_all_confirm(client, callback_query):
    target_user_id = callback_query.matches[0].group(1)
    target_uid = int(target_user_id) if target_user_id.isdigit() else target_user_id
    
    db = SessionLocal()
    try:
        from app.models.telegram import TelegramProjectMember
        from pyrogram.enums import ChatMemberStatus
        groups = db.query(TelegramProjectMember.chat_id).distinct().all()
        
        await callback_query.message.edit_text("⏳ Đang tiến hành xóa người dùng...")
        
        kicked_count = 0
        for (chat_id_val,) in groups:
            chat_id = int(chat_id_val)
            try:
                member = await client.get_chat_member(chat_id, target_uid)
                if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    await client.ban_chat_member(chat_id, target_uid)
                    await client.unban_chat_member(chat_id, target_uid)
                    kicked_count += 1
                    await asyncio.sleep(5)
            except Exception as ex:
                from pyrogram.errors import UserNotParticipant
                if not isinstance(ex, UserNotParticipant):
                    LogError(f"Error kicking member {target_uid} in chat {chat_id}: {ex}", LogType.SYSTEM_STATUS)
                
        await callback_query.message.edit_text(
            f"✅ <b>HOÀN TẤT!</b>\n\nĐã xóa người dùng khỏi <b>{kicked_count}</b> nhóm.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LogError(f"Error in kick_user_all_confirm: {e}", LogType.SYSTEM_STATUS)
        await callback_query.message.edit_text("❌ Có lỗi xảy ra trong quá trình xóa.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ku_p_([a-f0-9]+)_(.+)$"))
async def kick_user_project_callback(client, callback_query):
    project_id_short = callback_query.matches[0].group(1)
    target_user_id = callback_query.matches[0].group(2)
    target_uid = int(target_user_id) if target_user_id.isdigit() else target_user_id
    
    db = SessionLocal()
    try:
        from app.models.business import Projects
        from app.models.telegram import TelegramProjectMember
        from pyrogram.enums import ChatMemberStatus
        
        projects = db.query(Projects).all()
        target_project = None
        for p in projects:
            if str(p.id).replace("-", "")[:8] == project_id_short:
                target_project = p
                break
                
        if not target_project:
            await callback_query.answer("⚠️ Không tìm thấy dự án.", show_alert=True)
            return
            
        groups = db.query(TelegramProjectMember.chat_id, TelegramProjectMember.group_name).filter(
            TelegramProjectMember.project_id == target_project.id
        ).distinct().all()
        
        await callback_query.message.edit_text(f"⏳ Đang kiểm tra thông tin trên {len(groups)} nhóm thuộc dự án {target_project.project_name}...")
        
        kickable_chats = []
        admin_chats = []
        last_ex = None
        
        for chat_id_val, group_name in groups:
            chat_id = int(chat_id_val)
            try:
                member = await client.get_chat_member(chat_id, target_uid)
                chat_title = group_name if group_name else str(chat_id)
                
                if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    admin_chats.append(chat_title)
                else:
                    kickable_chats.append(chat_title)
            except Exception as ex:
                last_ex = ex
                from pyrogram.errors import UserNotParticipant
                if not isinstance(ex, UserNotParticipant):
                    LogError(f"Error checking member {target_uid} in chat {chat_id}: {ex}", LogType.SYSTEM_STATUS)
                
        if not kickable_chats and not admin_chats:
            await callback_query.message.edit_text(f"⚠️ Người dùng này hiện không có mặt trong bất kỳ nhóm nào thuộc dự án {target_project.project_name}.", parse_mode=ParseMode.HTML)
            return
            
        text = f"<b>THÔNG TIN NHÓM ĐÃ THAM GIA ({target_project.project_name}):</b>\n\n"
        if kickable_chats:
            text += "✅ <b>Có thể xóa khỏi các nhóm sau:</b>\n"
            for t in kickable_chats:
                text += f"- {t}\n"
            text += "\n"
        if admin_chats:
            text += "❌ <b>Không thể xóa (vì là Admin/Owner):</b>\n"
            for t in admin_chats:
                text += f"- {t}\n"
            text += "\n"
            
        if not kickable_chats:
            text += "⚠️ <i>Thành viên này không có nhóm nào có thể bị xóa.</i>"
            await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML)
            return
            
        text += "❓ Bạn có chắc chắn muốn xóa thành viên này khỏi các nhóm hợp lệ không?"
        
        buttons = [
            [InlineKeyboardButton("Xác nhận", callback_data=f"ku_c_p_{project_id_short}_{target_user_id}")],
            [InlineKeyboardButton("Hủy", callback_data="ku_cancel")]
        ]
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)
    except Exception as e:
        LogError(f"Error in kick_user_project: {e}", LogType.SYSTEM_STATUS)
        await callback_query.message.edit_text("❌ Có lỗi xảy ra trong quá trình kiểm tra.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ku_c_p_([a-f0-9]+)_(.+)$"))
async def kick_user_project_confirm(client, callback_query):
    project_id_short = callback_query.matches[0].group(1)
    target_user_id = callback_query.matches[0].group(2)
    target_uid = int(target_user_id) if target_user_id.isdigit() else target_user_id
    
    db = SessionLocal()
    try:
        from app.models.business import Projects
        from app.models.telegram import TelegramProjectMember
        from pyrogram.enums import ChatMemberStatus
        
        projects = db.query(Projects).all()
        target_project = None
        for p in projects:
            if str(p.id).replace("-", "")[:8] == project_id_short:
                target_project = p
                break
                
        if not target_project:
            await callback_query.answer("⚠️ Không tìm thấy dự án.", show_alert=True)
            return
            
        groups = db.query(TelegramProjectMember.chat_id).filter(
            TelegramProjectMember.project_id == target_project.id
        ).distinct().all()
        
        await callback_query.message.edit_text(f"⏳ Đang tiến hành xóa người dùng trong dự án {target_project.project_name}...")
        
        kicked_count = 0
        for (chat_id_val,) in groups:
            chat_id = int(chat_id_val)
            try:
                member = await client.get_chat_member(chat_id, target_uid)
                if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    await client.ban_chat_member(chat_id, target_uid)
                    await client.unban_chat_member(chat_id, target_uid)
                    kicked_count += 1
                    await asyncio.sleep(5)
            except Exception as ex:
                from pyrogram.errors import UserNotParticipant
                if not isinstance(ex, UserNotParticipant):
                    LogError(f"Error kicking member {target_uid} in chat {chat_id}: {ex}", LogType.SYSTEM_STATUS)
                
        await callback_query.message.edit_text(
            f"✅ <b>HOÀN TẤT!</b>\n\nĐã xóa người dùng khỏi <b>{kicked_count}</b> nhóm trong dự án <b>{target_project.project_name}</b>.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LogError(f"Error in kick_user_project_confirm: {e}", LogType.SYSTEM_STATUS)
        await callback_query.message.edit_text("❌ Có lỗi xảy ra trong quá trình xóa.")
    finally:
        db.close()


@bot.on_callback_query(filters.regex(r"^ku_cancel$"))
async def kick_user_cancel_callback(client, callback_query):
    await callback_query.message.edit_text("❌ Đã hủy thao tác xóa người dùng.")
