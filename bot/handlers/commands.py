import datetime
import asyncio
import re
from bot.utils.logger import LogType, LogInfo, LogError
from pyrogram import filters
from pyrogram.types import Message
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

        # Tìm project của nhóm này
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
                    BotCommand("other_create_smartphone", "Tạo điện thoại mới"),
                    BotCommand("other_tao_dien_thoai", "Tạo điện thoại mới"),
                    BotCommand("other_update_smartphone", "Cập nhật điện thoại"),
                    BotCommand("other_cap_nhat_dien_thoai", "Cập nhật điện thoại"),
                    BotCommand("other_delete_smartphone", "Xóa điện thoại"),
                    BotCommand("other_xoa_dien_thoai", "Xóa điện thoại"),
                    BotCommand("other_create_laptop", "Tạo laptop mới"),
                    BotCommand("other_tao_laptop", "Tạo laptop mới"),
                    BotCommand("other_update_laptop", "Cập nhật laptop"),
                    BotCommand("other_cap_nhat_laptop", "Cập nhật laptop"),
                    BotCommand("other_delete_laptop", "Xóa laptop"),
                    BotCommand("other_xoa_laptop", "Xóa laptop"),
                    BotCommand("other_create_sim", "Tạo SIM mới"),
                    BotCommand("other_tao_sim", "Tạo SIM mới"),
                    BotCommand("other_update_sim", "Cập nhật SIM"),
                    BotCommand("other_cap_nhat_sim", "Cập nhật SIM"),
                    BotCommand("other_delete_sim", "Xóa SIM"),
                    BotCommand("other_xoa_sim", "Xóa SIM"),
                    BotCommand("other_create_app", "Tạo ứng dụng mới"),
                    BotCommand("other_tao_app", "Tạo ứng dụng mới"),
                    BotCommand("other_update_app", "Cập nhật ứng dụng"),
                    BotCommand("other_cap_nhat_app", "Cập nhật ứng dụng"),
                    BotCommand("other_delete_app", "Xóa ứng dụng"),
                    BotCommand("other_xoa_app", "Xóa ứng dụng"),
                    BotCommand("other_receive_device", "Nhận thiết bị"),
                    BotCommand("other_nhan_thiet_bi", "Nhận thiết bị"),
                    BotCommand("other_return_device", "Trả thiết bị"),
                    BotCommand("other_tra_thiet_bi", "Trả thiết bị"),
                    BotCommand("other_check_device", "Kiểm tra thiết bị"),
                    BotCommand("other_check_log_device", "Xem lịch sử thiết bị"),
                    BotCommand("other_lich_su_thiet_bi", "Xem lịch sử thiết bị"),
                    BotCommand("other_list_device", "Danh sách thiết bị"),
                    BotCommand("other_danh_sach_thiet_bi", "Danh sách thiết bị"),
                    BotCommand("other_sync_app", "Đồng bộ ứng dụng vào thiết bị"),
                ]

            elif custom_title == "main_vehicle":
                label = "Other (Vehicle)"
                commands_to_set = [
                    BotCommand("other_create_vehicle", "Tạo xe mới"),
                    BotCommand("other_tao_xe", "Tạo xe mới"),
                    BotCommand("other_update_vehicle", "Cập nhật thông tin xe"),
                    BotCommand("other_cap_nhat_xe", "Cập nhật thông tin xe"),
                    BotCommand("other_delete_vehicle", "Xóa xe"),
                    BotCommand("other_xoa_xe", "Xóa xe"),
                    BotCommand("other_receive_vehicle", "Nhận xe"),
                    BotCommand("other_nhan_xe", "Nhận xe"),
                    BotCommand("other_return_vehicle", "Trả xe"),
                    BotCommand("other_tra_xe", "Trả xe"),
                    BotCommand("other_check_log_vehicle", "Xem lịch sử xe"),
                    BotCommand("other_lich_su_xe", "Xem lịch sử xe"),
                ]

        # ===================== CREDIT =====================
        elif "credit" in project_name:
            if role == "main":
                label = "Credit (Main)"
                commands_to_set = [
                    BotCommand("credit_create_customer", "Tạo khách hàng"),
                    BotCommand("credit_tao_khach_hang", "Tạo khách hàng"),
                    BotCommand("credit_update_customer", "Cập nhật khách hàng"),
                    BotCommand("credit_cap_nhat_khach_hang", "Cập nhật khách hàng"),
                    BotCommand("credit_check_customer", "Xem thông tin khách hàng"),
                    BotCommand("credit_xem_khach_hang", "Xem thông tin khách hàng"),
                    BotCommand("credit_create_contract", "Tạo hợp đồng"),
                    BotCommand("credit_tao_hop_dong", "Tạo hợp đồng"),
                    BotCommand("credit_update_contract", "Cập nhật hợp đồng"),
                    BotCommand("credit_cap_nhat_hop_dong", "Cập nhật hợp đồng"),
                    BotCommand("credit_check_contract", "Xem hợp đồng"),
                    BotCommand("credit_xem_hop_dong", "Xem hợp đồng"),
                    BotCommand("credit_cancel_contract", "Hủy hợp đồng"),
                    BotCommand("credit_huy_hop_dong", "Hủy hợp đồng"),
                    BotCommand("credit_extend_contract", "Gia hạn hợp đồng"),
                    BotCommand("credit_gia_han_hop_dong", "Gia hạn hợp đồng"),
                    BotCommand("credit_list_contract", "Danh sách hợp đồng"),
                    BotCommand("credit_danh_sach_hop_dong", "Danh sách hợp đồng"),
                    BotCommand("credit_payment_confirmed", "Xác nhận thanh toán"),
                    BotCommand("credit_xac_nhan_thanh_toan", "Xác nhận thanh toán"),
                    # BotCommand("credit_paid_interest", "Thanh toán lãi"),
                    # BotCommand("credit_thanh_toan_lai", "Thanh toán lãi"),
                    BotCommand("credit_bad_debt", "Xác nhận nợ xấu"),
                    BotCommand("credit_xac_nhan_no_xau", "Xác nhận nợ xấu"),
                    BotCommand("credit_cashflow_report", "Báo cáo dòng tiền"),
                    BotCommand("credit_bao_cao_dong_tien", "Báo cáo dòng tiền"),
                    BotCommand("credit_revenue", "Doanh thu"),
                    BotCommand("credit_doanh_thu", "Doanh thu"),
                ]
            else:
                label = "Credit (Member)"
                commands_to_set = [
                    BotCommand("credit_check_customer", "Xem thông tin khách hàng"),
                    BotCommand("credit_xem_khach_hang", "Xem thông tin khách hàng"),
                    BotCommand("credit_check_contract", "Xem hợp đồng"),
                    BotCommand("credit_xem_hop_dong", "Xem hợp đồng"),
                    BotCommand("credit_check_debt", "Xem công nợ"),
                    BotCommand("credit_xem_cong_no", "Xem công nợ"),
                ]

        # ===================== RENTAL =====================
        elif "rental" in project_name:
            if role == "main":
                label = "Rental (Main)"
                commands_to_set = [
                    BotCommand("rental_create_customer", "Tạo khách hàng"),
                    BotCommand("rental_tao_khach_hang", "Tạo khách hàng"),
                    BotCommand("rental_check_customer", "Kiểm tra khách hàng"),
                    BotCommand("rental_kiem_tra_khach_hang", "Kiểm tra khách hàng"),
                    BotCommand("rental_create_contract", "Tạo hợp đồng"),
                    BotCommand("rental_tao_hop_dong", "Tạo hợp đồng"),
                    BotCommand("rental_update_contract", "Cập nhật hợp đồng"),
                    BotCommand("rental_cap_nhat_hop_dong", "Cập nhật hợp đồng"),
                    BotCommand("rental_check_contract", "Xem hợp đồng"),
                    BotCommand("rental_kiem_tra_hop_dong", "Xem hợp đồng"),
                    BotCommand("rental_extend_contract", "Gia hạn hợp đồng"),
                    BotCommand("rental_gia_han_hop_dong", "Gia hạn hợp đồng"),
                    BotCommand("rental_cancel_contract", "Hủy hợp đồng"),
                    BotCommand("rental_huy_hop_dong", "Hủy hợp đồng"),
                    BotCommand("rental_list_contract", "Danh sách hợp đồng"),
                    BotCommand("rental_danh_sach_hop_dong", "Danh sách hợp đồng"),
                    BotCommand("rental_payment_confirmed", "Xác nhận thanh toán"),
                    BotCommand("rental_xac_nhan_thanh_toan", "Xác nhận thanh toán"),
                    BotCommand("rental_bad_debt", "Xác nhận nợ xấu"),
                    BotCommand("rental_xac_nhan_no_xau", "Xác nhận nợ xấu"),
                    BotCommand("rental_check_debt", "Xem công nợ"),
                    BotCommand("rental_xem_cong_no", "Xem công nợ"),
                    BotCommand("rental_revenue", "Doanh thu"),
                    BotCommand("rental_doanh_thu", "Doanh thu"),
                    BotCommand("rental_cashflow_report", "Báo cáo dòng tiền"),
                    BotCommand("rental_bao_cao_dong_tien", "Báo cáo dòng tiền"),
                ]
            else:
                label = "Rental (Member)"
                commands_to_set = [
                    BotCommand("rental_check_customer", "Kiểm tra khách hàng"),
                    BotCommand("rental_kiem_tra_khach_hang", "Kiểm tra khách hàng"),
                    BotCommand("rental_check_contract", "Xem hợp đồng"),
                    BotCommand("rental_kiem_tra_hop_dong", "Xem hợp đồng"),
                    BotCommand("rental_check_debt", "Xem công nợ"),
                    BotCommand("rental_xem_cong_no", "Xem công nợ"),
                ]

        # ===================== TIẾN NGA =====================
        elif "tiến nga" in project_name or "tien nga" in project_name:
            if custom_title == "super_main":
                label = "Tiến Nga (Tổng Hợp)"
            if custom_title in ("super_main", "main_hr"):
                if custom_title != "super_main": label = "Tiến Nga (Quản Lý)"
                commands_to_set.extend([
                    BotCommand("tien_nga_tao_nhan_vien", "Thêm nhân viên"),
                    BotCommand("tien_nga_cap_nhat_nhan_vien", "Cập nhật nhân viên"),
                    BotCommand("tien_nga_xoa_nhan_vien", "Xóa nhân viên"),
                    BotCommand("tien_nga_giao_viec", "Giao việc"),
                    BotCommand("tien_nga_xuat_luong", "Xuất bảng lương"),
                    BotCommand("tien_nga_tao_lai_bang_cham_cong", "Tạo lại báo cáo chấm công"),
                    BotCommand("tien_nga_xem_cong_viec", "Xem công việc của nhân viên"),      
                    BotCommand("tien_nga_xuat_danh_sach_luong", "Xuất bảng lương Excel"),
                    BotCommand("tien_nga_danh_sach_nhan_vien", "Xuất DS nhân viên Excel"),
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
                    ## Thu mua
                    BotCommand("tien_nga_thu_mua_hang_ngay", "Nhập mua mủ hàng ngày"),
                    BotCommand("tien_nga_xuat_bao_cao_thu_mua", "Xuất báo cáo mua mủ KH"),
                    ## Báo cáo
                    BotCommand("tien_nga_truy_xuat_thong_tin", "Truy xuất thông tin báo cáo"),
                    BotCommand("tien_nga_bieu_do_thu_mua", "Biểu đồ thu mua mủ"),
                    BotCommand("tien_nga_bao_cao_da_thanh_toan", "Báo cáo đã thanh toán"),
                    BotCommand("tien_nga_xuat_bao_cao_tong_hop", "Báo cáo tổng hợp Excel"),
                    BotCommand("tien_nga_bao_cao_luu_so", "Báo cáo lưu sổ"),
                    ## Điểm thu mua nguyên liệu
                    BotCommand("tien_nga_thu_mua_nguyen_lieu", "Nhập thu mua nguyên liệu"),
                    BotCommand("tien_nga_xuat_kho", "Xuất kho nguyên liệu")

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
                ])

            if custom_title == "main_harvest":
                label = "Tiến Nga (Thu Hoạch)"
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

            if custom_title == "member_inventory":
                label = "Tiến Nga (Kho)"

            if custom_title == "member_product":
                label = "Tiến Nga (Sản Phẩm)"

            if custom_title == "member_harvest":
                label = "Tiến Nga (Thu Hoạch)"

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
