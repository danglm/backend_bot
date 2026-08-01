"""
Module Data Resolvers cho hệ thống Scheduled Notification.
Mỗi module (credit, rental, rosca, general) có 1 resolver class.

Resolver chịu trách nhiệm:
1. get_pending_items() — Query DB lấy danh sách items cần thông báo
2. build_message() — Build message HTML từ item data (hoặc từ message_template)
"""
import datetime
import calendar
import json
from typing import List, Optional, Any

from sqlalchemy.orm import Session
from bot.utils.logger import LogInfo, LogError, LogWarning, LogType


# ── Helper: Render template với placeholder ──────────────────────────────────

class SafeDict(dict):
    """Dict that returns {key} for missing keys instead of raising KeyError."""
    def __missing__(self, key):
        return f"{{{key}}}"


def render_template(template: str, data: dict) -> str:
    """
    Thay placeholder trong template bằng dữ liệu thực.
    Safe fallback: nếu placeholder thiếu → giữ nguyên {placeholder}.
    """
    if not template:
        return ""
    try:
        return template.format_map(SafeDict(data))
    except Exception:
        return template


def fmt_num(val):
    """Format number: bỏ phần thập phân nếu là số nguyên."""
    if val is None:
        return 0
    return int(val) if val == int(val) else val


# ── Credit Resolver ──────────────────────────────────────────────────────────

class CreditNotifyResolver:
    """Resolve dữ liệu cho module Credit."""

    BUSINESS_TYPES = {"credit_interest", "credit_bad_debt"}

    @staticmethod
    def get_pending_items(db: Session, config, current_date: datetime.date, is_test: bool = False) -> Optional[List[dict]]:
        if config.notify_type == "credit_interest":
            return CreditNotifyResolver._get_interest_items(db, config, current_date, is_test=is_test)
        elif config.notify_type in {"credit_bad_debt", "credit_maturity"}:
            return CreditNotifyResolver._get_bad_debt_items(db, config, current_date, is_test=is_test)
        else:
            return None

    @staticmethod
    def build_message(item: Optional[dict], config, days_late: int = 0) -> str:
        """Build message HTML từ item data."""
        data = item or {}

        # Nếu admin đã viết template → dùng template override
        if config.message_template:
            return render_template(config.message_template, data)

        # Không có template → dùng message mặc định
        if config.notify_type == "credit_interest":
            return CreditNotifyResolver._build_interest_message(data)
        elif config.notify_type == "credit_bad_debt":
            return CreditNotifyResolver._build_bad_debt_message(data)
        elif config.notify_type == "credit_maturity":
            return CreditNotifyResolver._build_maturity_message(data)

        return config.message_template or "🔔 <b>THÔNG BÁO TÍN DỤNG</b> 🔔"

    @staticmethod
    def build_keyboard(item: Optional[dict], config):
        """Build InlineKeyboardMarkup cho thông báo Tín dụng (Credit)."""
        data = item or {}
        if config.notify_type == "credit_interest":
            contract_id = data.get("contract_id") or getattr(config, "reference_id", None)
            if contract_id:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                return InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Đã nhận thanh toán đủ", callback_data=f"cnt_full_pay|{contract_id}"),
                        InlineKeyboardButton("Đã nhận thanh toán", callback_data=f"cnt_pay|{contract_id}")
                    ],
                    [
                        InlineKeyboardButton("Lưu sổ", callback_data=f"cnt_remind|{contract_id}"),
                        InlineKeyboardButton("Nợ Xấu", callback_data=f"cnt_bad|{contract_id}")
                    ]
                ])
        return None

    @staticmethod
    def _get_interest_items(db: Session, config, current_date: datetime.date, is_test: bool = False) -> List[dict]:
        """Query hợp đồng Credit cần nhắc đóng lãi."""
        from app.models.credit import Credit, CreditCustomer, CreditStatus

        items = []
        query = db.query(Credit).filter(
            Credit.credit_status == CreditStatus.ACTIVE.value,
            Credit.remaining_principal > 0,
            Credit.interest_start_date != None
        )
        # Filter theo reference_id nếu có (chỉ gửi cho HĐ cụ thể)
        if config.reference_id:
            query = query.filter(Credit.contract_id == config.reference_id)
        active_contracts = query.all()

        for contract in active_contracts:
            interest_day = contract.interest_start_date.day

            # Tính due_date cho chu kỳ hiện tại
            if current_date.day >= interest_day:
                due_year, due_month = current_date.year, current_date.month
            else:
                due_year, due_month = (current_date.year, current_date.month - 1) if current_date.month > 1 else (current_date.year - 1, 12)

            try:
                due_date = datetime.date(due_year, due_month, interest_day)
            except ValueError:
                due_date = datetime.date(due_year, due_month, calendar.monthrange(due_year, due_month)[1])

            days_late = (current_date - due_date).days
            if not is_test:
                if days_late < 0 or days_late > 7:
                    continue

                # Check skip tag
                skip_tag = f"[SKIP_INTEREST: {due_month:02d}/{due_year}]"
                if contract.notes and skip_tag in contract.notes:
                    continue

            # Tính tiền lãi
            int_rate = contract.monthly_interest_rate or 0
            int_amt = contract.monthly_interest_amount or 0
            if int_amt == 0 and int_rate > 0:
                int_amt = (contract.remaining_principal * int_rate) / 100

            interest_debt = contract.interest_debt or 0
            if not is_test:
                if interest_debt <= 0 and days_late > 0:
                    continue

            customer = contract.customer
            if not customer:
                continue

            items.append({
                "customer_name": customer.customer_name or "N/A",
                "customer_id": customer.customer_id or "N/A",
                "contact_info": customer.contact_info or "N/A",
                "contract_id": contract.contract_id,
                "loan_type": contract.loan_type or "N/A",
                "initial_principal": f"{fmt_num(contract.initial_principal or 0):,}",
                "interest_amount": f"{fmt_num(int_amt):,}",
                "remaining_principal": f"{fmt_num(contract.remaining_principal):,}",
                "interest_debt": f"{fmt_num(interest_debt):,}",
                "due_date": due_date.strftime("%d/%m/%Y"),
                "interest_start_date": contract.interest_start_date.strftime("%d/%m/%Y") if contract.interest_start_date else "N/A",
                "monthly_interest_rate": int_rate,
                "days_late": days_late,
                "days_text": "Đến hạn hôm nay" if days_late == 0 else f"Trễ hạn {days_late} ngày",
                "reference_id": contract.contract_id,
                "reference_name": customer.customer_name,
                "group_name": customer.group_name,
            })

        if is_test and not items:
            real_contract = None
            if config.reference_id:
                from app.models.credit import Credit, CreditCustomer
                ref_str = str(config.reference_id).strip()
                real_contract = db.query(Credit).filter(Credit.contract_id == ref_str).first()
                if not real_contract:
                    cust = db.query(CreditCustomer).filter(CreditCustomer.customer_id == ref_str).first()
                    if cust:
                        real_contract = db.query(Credit).filter(Credit.customer_id == cust.id).first()

            if real_contract and real_contract.customer:
                c = real_contract
                cust = c.customer
                int_rate = c.monthly_interest_rate or 0
                int_amt = c.monthly_interest_amount or 0
                if int_amt == 0 and int_rate > 0:
                    int_amt = (c.remaining_principal * int_rate) / 100
                items.append({
                    "customer_name": cust.customer_name or "N/A",
                    "customer_id": cust.customer_id or "N/A",
                    "contact_info": cust.contact_info or "N/A",
                    "contract_id": c.contract_id,
                    "loan_type": c.loan_type or "N/A",
                    "initial_principal": f"{fmt_num(c.initial_principal or 0):,}",
                    "interest_amount": f"{fmt_num(int_amt):,}",
                    "remaining_principal": f"{fmt_num(c.remaining_principal):,}",
                    "interest_debt": f"{fmt_num(c.interest_debt or 0):,}",
                    "due_date": current_date.strftime("%d/%m/%Y"),
                    "interest_start_date": c.interest_start_date.strftime("%d/%m/%Y") if c.interest_start_date else "N/A",
                    "monthly_interest_rate": int_rate,
                    "days_late": 0,
                    "days_text": "Đến hạn hôm nay (Test)",
                    "reference_id": c.contract_id,
                    "reference_name": cust.customer_name,
                    "group_name": cust.group_name,
                })
            else:
                ref_code = config.reference_id or "HD_TEST001"
                ref_name = getattr(config, 'reference_name', None) or "Khách hàng Mẫu Test"
                items.append({
                    "customer_name": ref_name,
                    "customer_id": "KH_TEST001",
                    "contact_info": "0900000000",
                    "contract_id": ref_code,
                    "interest_amount": "1,000,000",
                    "remaining_principal": "50,000,000",
                    "interest_debt": "1,000,000",
                    "due_date": current_date.strftime("%d/%m/%Y"),
                    "interest_start_date": current_date.strftime("%d/%m/%Y"),
                    "monthly_interest_rate": 2.0,
                    "days_late": 0,
                    "days_text": "Đến hạn hôm nay (Test)",
                    "reference_id": ref_code,
                    "reference_name": ref_name,
                    "group_name": getattr(config, 'group_name', None) or "Nhóm Test",
                })

        return items

    @staticmethod
    def _get_bad_debt_items(db: Session, config, current_date: datetime.date, is_test: bool = False) -> List[dict]:
        """Query hợp đồng Credit quá hạn gốc (nợ xấu)."""
        from app.models.credit import Credit, CreditStatus, CreditCustomer

        items = []
        query = db.query(Credit).filter(
            Credit.credit_status == CreditStatus.ACTIVE.value,
            Credit.remaining_principal > 0,
            Credit.due_date != None,
        )
        if not is_test:
            query = query.filter(Credit.due_date < current_date - datetime.timedelta(days=7))

        if config.reference_id:
            query = query.filter(Credit.contract_id == config.reference_id)
        overdue_contracts = query.all()

        for contract in overdue_contracts:
            days_overdue = (current_date - contract.due_date).days if contract.due_date else 0
            customer = contract.customer
            if not customer:
                continue

            items.append({
                "customer_name": customer.customer_name or "N/A",
                "customer_id": customer.customer_id or "N/A",
                "contact_info": customer.contact_info or "N/A",
                "contract_id": contract.contract_id,
                "remaining_principal": f"{fmt_num(contract.remaining_principal):,}",
                "due_date": contract.due_date.strftime("%d/%m/%Y") if contract.due_date else "N/A",
                "days_late": days_overdue,
                "days_text": f"Quá hạn {days_overdue} ngày",
                "reference_id": contract.contract_id,
                "reference_name": customer.customer_name,
            })

        if is_test and not items:
            real_contract = None
            if config.reference_id:
                ref_str = str(config.reference_id).strip()
                real_contract = db.query(Credit).filter(Credit.contract_id == ref_str).first()
                if not real_contract:
                    cust = db.query(CreditCustomer).filter(CreditCustomer.customer_id == ref_str).first()
                    if cust:
                        real_contract = db.query(Credit).filter(Credit.customer_id == cust.id).first()

            if real_contract and real_contract.customer:
                c = real_contract
                cust = c.customer
                days_overdue = (current_date - c.due_date).days if c.due_date else 0
                items.append({
                    "customer_name": cust.customer_name or "N/A",
                    "customer_id": cust.customer_id or "N/A",
                    "contact_info": cust.contact_info or "N/A",
                    "contract_id": c.contract_id,
                    "remaining_principal": f"{fmt_num(c.remaining_principal):,}",
                    "due_date": c.due_date.strftime("%d/%m/%Y") if c.due_date else "N/A",
                    "days_late": days_overdue,
                    "days_text": f"Quá hạn {days_overdue} ngày (Test)",
                    "reference_id": c.contract_id,
                    "reference_name": cust.customer_name,
                })
            else:
                ref_code = config.reference_id or "HD_BAD_TEST001"
                ref_name = getattr(config, 'reference_name', None) or "Khách hàng Nợ Xấu Test"
                items.append({
                    "customer_name": ref_name,
                    "customer_id": "KH_TEST002",
                    "contact_info": "0900000000",
                    "contract_id": ref_code,
                    "remaining_principal": "100,000,000",
                    "due_date": current_date.strftime("%d/%m/%Y"),
                    "days_late": 30,
                    "days_text": "Quá hạn 30 ngày (Test)",
                    "reference_id": ref_code,
                    "reference_name": ref_name,
                })

        return items

    @staticmethod
    def _build_interest_message(data: dict) -> str:
        days_text = data.get("days_text", "")
        loan_type = data.get("loan_type", "N/A")
        initial_principal = data.get("initial_principal", "0")
        return (
            f"🔔 <b>THÔNG BÁO ĐÓNG TIỀN LÃI ({days_text})</b> 🔔\n\n"
            f"<b>Khách hàng:</b> {data.get('customer_name', 'N/A')}\n"
            f"<b>Mã Khách Hàng:</b> <code>{data.get('customer_id', 'N/A')}</code>\n"
            f"<b>Liên hệ:</b> {data.get('contact_info', 'N/A')}\n"
            f"<b>Mã Hợp Đồng:</b> <code>{data.get('contract_id', 'N/A')}</code>\n"
            f"<b>Hình thức vay:</b> {loan_type}\n"
            f"<b>Gốc ban đầu:</b> {initial_principal} VND\n"
            f"<b>Dư nợ gốc còn lại:</b> {data.get('remaining_principal', '0')} VND\n"
            f"<b>Lãi suất/tháng:</b> {data.get('monthly_interest_rate', '0')}%\n"
            f"<b>Tiền lãi hàng tháng:</b> {data.get('interest_amount', '0')} VND\n"
            f"<b>Nợ lãi tích lũy:</b> <b>{data.get('interest_debt', '0')} VND</b>\n"
            f"{'━' * 15}\n"
            f"<i>Quý khách vui lòng thanh toán đúng hạn. Cảm ơn Quý Khách Hàng!</i>"
        )

    @staticmethod
    def _build_bad_debt_message(data: dict) -> str:
        return (
            f"🔔 <b>CẢNH BÁO NỢ XẤU ({data.get('days_text', '')})</b> 🔔\n\n"
            f"<b>Khách hàng:</b> {data.get('customer_name', 'N/A')}\n"
            f"<b>Mã Khách Hàng:</b> <code>{data.get('customer_id', 'N/A')}</code>\n"
            f"<b>Liên hệ:</b> {data.get('contact_info', 'N/A')}\n"
            f"<b>Mã Hợp Đồng:</b> <code>{data.get('contract_id', 'N/A')}</code>\n"
            f"<b>Còn nợ gốc:</b> <b>{data.get('remaining_principal', '0')} VND</b>\n"
            f"<b>Ngày đáo hạn gốc:</b> {data.get('due_date', 'N/A')}\n"
            f"{'━' * 15}\n"
            f"<i>Vui lòng làm việc với bộ phận thu hồi nợ để giải quyết khoản nợ.</i>"
        )

    @staticmethod
    def _build_maturity_message(data: dict) -> str:
        contract_id = data.get("contract_id")
        if not contract_id or contract_id == "N/A":
            return (
                "🔔 <b>CẢNH BÁO HỢP ĐỒNG VAY SẮP ĐÁO HẠN</b> 🔔\n\n"
                "Vui lòng kiểm tra danh sách các hợp đồng tín dụng sắp đến ngày đáo hạn gốc.\n\n"
                "<i>Liên hệ Admin/Quản lý để biết thêm chi tiết.</i>"
            )

        loan_type = data.get("loan_type", "N/A")
        initial_principal = data.get("initial_principal", "0")

        return (
            f"🔔 <b>CẢNH BÁO HỢP ĐỒNG VAY SẮP ĐÁO HẠN</b> 🔔\n\n"
            f"<b>Khách hàng:</b> {data.get('customer_name', 'N/A')}\n"
            f"<b>Mã Khách Hàng:</b> <code>{data.get('customer_id', 'N/A')}</code>\n"
            f"<b>Liên hệ:</b> {data.get('contact_info', 'N/A')}\n"
            f"<b>Mã Hợp Đồng:</b> <code>{contract_id}</code>\n"
            f"<b>Hình thức vay:</b> {loan_type}\n"
            f"<b>Gốc ban đầu:</b> {initial_principal} VND\n"
            f"<b>Dư nợ gốc còn lại:</b> {data.get('remaining_principal', '0')} VND\n"
            f"<b>Ngày đáo hạn gốc:</b> {data.get('due_date', 'N/A')}\n"
            f"{'━' * 15}\n"
            f"<i>Vui lòng kiểm tra các hợp đồng tín dụng sắp đến ngày đáo hạn gốc để thực hiện gia hạn hoặc thu hồi.</i>"
        )


# ── Rental Resolver ──────────────────────────────────────────────────────────

class RentalNotifyResolver:
    """Resolve dữ liệu cho module Rental."""

    BUSINESS_TYPES = {"rental_payment"}

    @staticmethod
    def get_pending_items(db: Session, config, current_date: datetime.date, is_test: bool = False) -> Optional[List[dict]]:
        if config.notify_type in RentalNotifyResolver.BUSINESS_TYPES:
            return RentalNotifyResolver._get_payment_items(db, config, current_date, is_test=is_test)
        else:
            return None

    @staticmethod
    def build_message(item: Optional[dict], config, days_late: int = 0) -> str:
        data = item or {}
        if config.message_template:
            return render_template(config.message_template, data)

        if config.notify_type == "rental_payment":
            return RentalNotifyResolver._build_payment_message(data)
        elif config.notify_type == "rental_maintenance":
            return RentalNotifyResolver._build_maintenance_message(data)
        elif config.notify_type == "rental_contract_expiry":
            return RentalNotifyResolver._build_contract_expiry_message(data)

        return config.message_template or "🔔 <b>THÔNG BÁO CHO THUÊ</b> 🔔"

    @staticmethod
    def _get_payment_items(db: Session, config, current_date: datetime.date, is_test: bool = False) -> List[dict]:
        """Query hợp đồng Rental cần nhắc đóng tiền thuê."""
        from app.models.rental import Rental, RentalCustomer, RentalStatus

        items = []
        query = db.query(Rental).filter(
            Rental.status == RentalStatus.ACTIVE.value,
            Rental.start_rental != None
        )
        # Filter theo reference_id nếu có (chỉ gửi cho HĐ cụ thể)
        if config.reference_id:
            query = query.filter(Rental.contract_id == config.reference_id)
        active_contracts = query.all()

        for contract in active_contracts:
            rental_day = contract.start_rental.day

            # Tính due_date
            if current_date.day >= rental_day:
                due_year, due_month = current_date.year, current_date.month
            else:
                due_year, due_month = (current_date.year, current_date.month - 1) if current_date.month > 1 else (current_date.year - 1, 12)

            try:
                due_date = datetime.date(due_year, due_month, rental_day)
            except ValueError:
                due_date = datetime.date(due_year, due_month, calendar.monthrange(due_year, due_month)[1])

            days_late = (current_date - due_date).days
            if not is_test:
                if days_late < 0 or days_late > 7:
                    continue

                rental_debt = contract.rental_debt or 0
                if rental_debt <= 0 and days_late > 0:
                    continue
            else:
                rental_debt = contract.rental_debt or 0

            # Manual join — Rental model không có relationship tới RentalCustomer
            customer = db.query(RentalCustomer).filter(
                RentalCustomer.id == contract.customer_id
            ).first()
            if not customer:
                continue

            items.append({
                "customer_name": customer.customer_name or "N/A",
                "customer_id": customer.customer_id or "N/A",
                "contact_info": customer.contact_info or "N/A",
                "contract_id": contract.contract_id,
                "monthly_rental": f"{fmt_num(contract.monthly_rental or 0):,}",
                "rental_debt": f"{fmt_num(rental_debt):,}",
                "deposit": f"{fmt_num(contract.deposit or 0):,}",
                "real_estate_id": contract.real_estate_id or "N/A",
                "type_contract": contract.type_contract or "N/A",
                "start_rental": contract.start_rental.strftime("%d/%m/%Y") if contract.start_rental else "N/A",
                "end_rental": contract.end_rental.strftime("%d/%m/%Y") if contract.end_rental else "N/A",
                "days_late": days_late,
                "days_text": "Đến hạn hôm nay" if days_late == 0 else f"Nhắc nhở lần {days_late} - Trễ hạn {days_late} ngày",
                "reference_id": contract.contract_id,
                "reference_name": customer.customer_name,
                "group_name": customer.group_name if hasattr(customer, 'group_name') else None,
            })

        if is_test and not items:
            real_contract = None
            if config.reference_id:
                ref_str = str(config.reference_id).strip()
                real_contract = db.query(Rental).filter(Rental.contract_id == ref_str).first()
                if not real_contract:
                    cust = db.query(RentalCustomer).filter(RentalCustomer.customer_id == ref_str).first()
                    if cust:
                        real_contract = db.query(Rental).filter(Rental.customer_id == cust.id).first()

            if real_contract:
                customer = db.query(RentalCustomer).filter(RentalCustomer.id == real_contract.customer_id).first()
                if customer:
                    c = real_contract
                    items.append({
                        "customer_name": customer.customer_name or "N/A",
                        "customer_id": customer.customer_id or "N/A",
                        "contact_info": customer.contact_info or "N/A",
                        "contract_id": c.contract_id,
                        "monthly_rental": f"{fmt_num(c.monthly_rental or 0):,}",
                        "rental_debt": f"{fmt_num(c.rental_debt or 0):,}",
                        "deposit": f"{fmt_num(c.deposit or 0):,}",
                        "real_estate_id": c.real_estate_id or "N/A",
                        "type_contract": c.type_contract or "N/A",
                        "start_rental": c.start_rental.strftime("%d/%m/%Y") if c.start_rental else "N/A",
                        "end_rental": c.end_rental.strftime("%d/%m/%Y") if c.end_rental else "N/A",
                        "days_late": 0,
                        "days_text": "Đến hạn hôm nay (Test)",
                        "reference_id": c.contract_id,
                        "reference_name": customer.customer_name,
                        "group_name": customer.group_name if hasattr(customer, 'group_name') else None,
                    })

            if not items:
                ref_code = config.reference_id or "RENTAL_TEST001"
                ref_name = getattr(config, 'reference_name', None) or "Khách Thuê Mẫu Test"
                items.append({
                    "customer_name": ref_name,
                    "customer_id": "KH_RENTAL_TEST",
                    "contact_info": "0900000000",
                    "contract_id": ref_code,
                    "monthly_rental": "5,000,000",
                    "rental_debt": "5,000,000",
                    "deposit": "5,000,000",
                    "real_estate_id": "BĐS_TEST",
                    "type_contract": "Thuê nhà dài hạn",
                    "start_rental": current_date.strftime("%d/%m/%Y"),
                    "end_rental": current_date.strftime("%d/%m/%Y"),
                    "days_late": 0,
                    "days_text": "Đến hạn hôm nay (Test)",
                    "reference_id": ref_code,
                    "reference_name": ref_name,
                    "group_name": getattr(config, 'group_name', None) or "Nhóm Test",
                })

        return items

    @staticmethod
    def _build_payment_message(data: dict) -> str:
        days_text = data.get("days_text", "")
        real_estate = data.get("real_estate_id", "N/A")
        type_contract = data.get("type_contract", "N/A")
        start_rental = data.get("start_rental", "N/A")
        end_rental = data.get("end_rental", "N/A")
        deposit = data.get("deposit", "0")

        return (
            f"🔔 <b>THÔNG BÁO ĐÓNG TIỀN THUÊ ({days_text})</b> 🔔\n\n"
            f"<b>Khách hàng:</b> {data.get('customer_name', 'N/A')}\n"
            f"<b>Mã Khách Hàng:</b> <code>{data.get('customer_id', 'N/A')}</code>\n"
            f"<b>Liên hệ:</b> {data.get('contact_info', 'N/A')}\n"
            f"<b>Mã Hợp Đồng:</b> <code>{data.get('contract_id', 'N/A')}</code>\n"
            f"<b>Mã Bất Động Sản:</b> <code>{real_estate}</code>\n"
            f"<b>Loại Hợp Đồng:</b> {type_contract}\n"
            f"<b>Thời gian thuê:</b> {start_rental} ➔ {end_rental}\n"
            f"<b>Tiền thuê hàng tháng:</b> {data.get('monthly_rental', '0')} VND\n"
            f"<b>Tiền cọc:</b> {deposit} VND\n"
            f"<b>Công nợ hiện tại:</b> <b>{data.get('rental_debt', '0')} VND</b>\n"
            f"{'━' * 15}\n"
            f"<i>Quý khách vui lòng thanh toán đúng hạn. Cảm ơn Quý Khách Hàng!</i>"
        )

    @staticmethod
    def _build_maintenance_message(data: dict) -> str:
        contract_id = data.get("contract_id")
        if not contract_id or contract_id == "N/A":
            return (
                "🔔 <b>NHẮC NHỞ BẢO TRÌ BẤT ĐỘNG SẢN</b> 🔔\n\n"
                "Vui lòng kiểm tra và thực hiện bảo trì, bảo dưỡng định kỳ các hạng mục cho thuê.\n\n"
                "<i>Hệ thống nhắc nhở tự động.</i>"
            )

        real_estate = data.get("real_estate_id", "N/A")
        type_contract = data.get("type_contract", "N/A")

        return (
            f"🔔 <b>NHẮC NHỞ BẢO TRÌ BẤT ĐỘNG SẢN</b> 🔔\n\n"
            f"<b>Khách hàng:</b> {data.get('customer_name', 'N/A')}\n"
            f"<b>Mã Khách Hàng:</b> <code>{data.get('customer_id', 'N/A')}</code>\n"
            f"<b>Liên hệ:</b> {data.get('contact_info', 'N/A')}\n"
            f"<b>Mã Hợp Đồng:</b> <code>{contract_id}</code>\n"
            f"<b>Mã Bất Động Sản:</b> <code>{real_estate}</code>\n"
            f"<b>Loại Hợp Đồng:</b> {type_contract}\n"
            f"{'━' * 15}\n"
            f"<i>Vui lòng kiểm tra và thực hiện bảo trì, bảo dưỡng định kỳ các hạng mục cho thuê.</i>"
        )

    @staticmethod
    def _build_contract_expiry_message(data: dict) -> str:
        contract_id = data.get("contract_id")
        if not contract_id or contract_id == "N/A":
            return (
                "🔔 <b>CẢNH BÁO HỢP ĐỒNG THUÊ SẮP HẾT HẠN</b> 🔔\n\n"
                "Vui lòng kiểm tra các hợp đồng thuê sắp hết hạn để thực hiện gia hạn hoặc thanh lý.\n\n"
                "<i>Hệ thống nhắc nhở tự động.</i>"
            )

        real_estate = data.get("real_estate_id", "N/A")
        type_contract = data.get("type_contract", "N/A")
        start_rental = data.get("start_rental", "N/A")
        end_rental = data.get("end_rental", "N/A")

        return (
            f"🔔 <b>CẢNH BÁO HỢP ĐỒNG THUÊ SẮP HẾT HẠN</b> 🔔\n\n"
            f"<b>Khách hàng:</b> {data.get('customer_name', 'N/A')}\n"
            f"<b>Mã Khách Hàng:</b> <code>{data.get('customer_id', 'N/A')}</code>\n"
            f"<b>Liên hệ:</b> {data.get('contact_info', 'N/A')}\n"
            f"<b>Mã Hợp Đồng:</b> <code>{contract_id}</code>\n"
            f"<b>Mã Bất Động Sản:</b> <code>{real_estate}</code>\n"
            f"<b>Loại Hợp Đồng:</b> {type_contract}\n"
            f"<b>Thời gian thuê:</b> {start_rental} ➔ {end_rental}\n"
            f"{'━' * 15}\n"
            f"<i>Vui lòng kiểm tra các hợp đồng thuê sắp hết hạn để thực hiện gia hạn hoặc thanh lý.</i>"
        )


# ── Rosca Resolver ───────────────────────────────────────────────────────────

class RoscaNotifyResolver:
    """Resolve dữ liệu cho module Rosca (Hụi)."""

    BUSINESS_TYPES = {"rosca_payment"}

    @staticmethod
    def get_pending_items(db: Session, config, current_date: datetime.date, is_test: bool = False) -> Optional[List[dict]]:
        if config.notify_type in RoscaNotifyResolver.BUSINESS_TYPES:
            return RoscaNotifyResolver._get_payment_items(db, config, current_date, is_test=is_test)
        else:
            return None

    @staticmethod
    def build_message(item: Optional[dict], config, days_late: int = 0) -> str:
        data = item or {}
        if config.message_template:
            return render_template(config.message_template, data)

        if config.notify_type == "rosca_payment":
            return RoscaNotifyResolver._build_payment_message(data)
        elif config.notify_type == "rosca_bidding":
            return RoscaNotifyResolver._build_bidding_message(data)

    @staticmethod
    def build_keyboard(item: Optional[dict], config):
        """Build InlineKeyboardMarkup cho thông báo Hụi."""
        data = item or {}
        if config.notify_type == "rosca_payment":
            m_id = data.get("member_id") or getattr(config, "reference_id", None)
            c_rnd = data.get("current_round", 1)
            if m_id:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                return InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Đóng tiền chân Hụi", callback_data=f"rnt_pay|{m_id}|{c_rnd}"),
                        InlineKeyboardButton("Hốt tiền chân Hụi", callback_data=f"rnt_withdraw|{m_id}")
                    ],
                    [
                        InlineKeyboardButton("Hủy", callback_data=f"rnt_cancel_menu|{m_id}|{c_rnd}")
                    ]
                ])
        return None


    @staticmethod
    def _get_payment_items(db: Session, config, current_date: datetime.date, is_test: bool = False) -> List[dict]:
        """Query Chân Hụi (RoscaMember) cần nhắc đóng tiền hụi hàng kỳ."""
        from app.models.rosca import Rosca, RoscaMember, UserRosca, RoscaContribution, RoscaRound
        from sqlalchemy import or_, cast, String

        items = []
        # Query trực tiếp trên bảng RoscaMember (Chân Hụi)
        query = db.query(RoscaMember).filter(
            RoscaMember.status.in_(["Playing", "Dead", "Active"])
        )

        # Lọc trực tiếp theo Mã chân hụi (RoscaMember.id), prefix Dây hụi, hoặc rosca_id
        if config.reference_id:
            ref_str = str(config.reference_id).strip()
            query = query.filter(
                or_(
                    RoscaMember.id == ref_str,
                    RoscaMember.id.like(f"{ref_str}_%"),
                    RoscaMember.rosca_id == ref_str,
                )
            )

        members = query.all()

        for member in members:
            # Query thông tin Dây hụi liên quan từ RoscaMember.rosca_id hoặc prefix
            rosca = db.query(Rosca).filter(Rosca.id == member.rosca_id).first()
            if not rosca and "_" in member.id:
                code_prefix = member.id.split("_")[0]
                rosca = db.query(Rosca).filter(Rosca.code == code_prefix).first()

            if not rosca:
                continue

            # Khi không phải gửi test -> kiểm tra Dây hụi Active và trùng ngày đóng hụi
            if not is_test:
                if rosca.status != "Active":
                    continue
                if rosca.payment_day != current_date.day:
                    continue

            player = db.query(UserRosca).filter(UserRosca.id == member.user_id).first() if member.user_id else None

            # Tính Kỳ đóng lần này = (Số lần đóng hụi: amount < 0) + (Số lần rút hụi: amount > 0) + 1
            paid_count = db.query(RoscaContribution).filter(
                RoscaContribution.member_id == member.id,
                RoscaContribution.amount < 0,
                RoscaContribution.status == "Paid"
            ).count()

            won_count = db.query(RoscaContribution).filter(
                RoscaContribution.member_id == member.id,
                RoscaContribution.amount > 0,
                RoscaContribution.status == "Paid"
            ).count()

            current_round = paid_count + won_count + 1

            owner = db.query(UserRosca).filter(UserRosca.id == rosca.user_id).first()
            owner_name = owner.full_name if owner else "Không xác định"
            player_name = player.full_name if player else member.id

            min_bid = rosca.min_bid_amount or 0
            max_bid = rosca.max_bid_amount or 0
            member_st = "Hụi sống" if member.status == "Playing" else ("Hụi chết" if member.status == "Dead" else member.status or "N/A")

            items.append({
                "member_id": member.id,
                "player_name": player_name,
                "parts_count": member.parts_count or 1,
                "rosca_code": rosca.code,
                "owner_name": owner_name,
                "payment_day": rosca.payment_day,
                "current_round": current_round,
                "base_amount": f"{fmt_num(rosca.base_amount or 0):,}" if hasattr(rosca, 'base_amount') else "N/A",
                "min_bid": f"{fmt_num(min_bid):,}",
                "max_bid": f"{fmt_num(max_bid):,}",
                "total_parts": rosca.total_parts if hasattr(rosca, 'total_parts') else "N/A",
                "period_type": rosca.period_type.value if rosca.period_type else "N/A",
                "member_status": member_st,
                "reference_id": member.id,
                "reference_name": f"Chân hụi {member.id} - {player_name} (Dây {rosca.code})",
            })

        # Fallback mẫu test nếu là Gửi test nhưng không có item thực tế
        if is_test and not items:
            ref_code = config.reference_id or "TEST_CHANHUI001"
            ref_name = getattr(config, 'reference_name', None) or "Chân hụi Mẫu Test"
            items.append({
                "member_id": ref_code,
                "player_name": ref_name,
                "parts_count": 1,
                "rosca_code": "TEST_HUI001",
                "owner_name": "Chủ hụi Mẫu Test",
                "payment_day": current_date.day,
                "current_round": 1,
                "base_amount": "5,000,000",
                "min_bid": "100,000",
                "max_bid": "500,000",
                "total_parts": 12,
                "period_type": "Hụi Tháng",
                "member_status": "Hụi sống",
                "reference_id": ref_code,
                "reference_name": f"Chân hụi {ref_code} - {ref_name}",
            })

        return items

    @staticmethod
    def _build_payment_message(data: dict) -> str:
        member_id = data.get("member_id", "N/A")
        player_name = data.get("player_name", "N/A")
        member_status = data.get("member_status", "N/A")
        parts_count = data.get("parts_count", 1)
        current_round = data.get("current_round", 1)
        payment_day = data.get("payment_day", "N/A")

        return (
            f"🔔 <b>THÔNG BÁO ĐÓNG HỤI HÀNG KỲ</b> 🔔\n\n"
            f"<b>Mã chân hụi:</b> <code>{member_id}</code>\n"
            f"<b>Người chơi:</b> {player_name} ({parts_count} chân)\n"
            f"<b>Tình trạng:</b> {member_status}\n"
            f"<b>Dây hụi:</b> {data.get('rosca_code', 'N/A')}\n"
            f"<b>Chủ hụi:</b> {data.get('owner_name', 'N/A')}\n"
            f"<b>Kỳ đóng:</b> Kỳ {current_round} (Hạn đóng: Ngày {payment_day} hàng tháng)\n"
            f"<b>Mức bỏ hụi tối thiểu:</b> {data.get('min_bid', '0')} VNĐ\n"
            f"<b>Mức bỏ hụi tối đa:</b> {data.get('max_bid', '0')} VNĐ\n\n"
            f"<i>Vui lòng nộp tiền hụi đúng hạn và thực hiện bỏ thăm nếu có nhu cầu hốt hụi kỳ này!</i>\n\n"
            f"💡 <b>GỢI Ý LỆNH THAO TÁC:</b>\n"
            f"🔹 <b>Đóng tiền chân hụi:</b> <code>/hui_dong_tien_chan_hui</code>\n"
            f"  <i>(Gõ lệnh để chọn dây hụi hoặc điền form thông tin đóng hụi)</i>\n"
            f"🔹 <b>Rút dây hụi / Hốt hụi:</b> <code>/hui_rut_day_hui {member_id} [Số_Tiền_Hốt]</code>\n"
            f"  <i>(Ví dụ: <code>/hui_rut_day_hui {member_id} 50000000</code>)</i>"
        )

    @staticmethod
    def _build_bidding_message(data: dict) -> str:
        member_id = data.get("member_id")
        if not member_id or member_id == "N/A":
            return (
                "🔔 <b>THÔNG BÁO LỊCH KHUI HỤI / BỎ THĂM</b> 🔔\n\n"
                "Đã đến giờ khui hụi! Quý thành viên vui lòng thực hiện bỏ thăm / khui hụi kỳ này.\n\n"
                "<i>Chúc Quý thành viên gặp nhiều may mắn!</i>"
            )

        player_name = data.get("player_name", "N/A")
        member_status = data.get("member_status", "N/A")
        parts_count = data.get("parts_count", 1)
        current_round = data.get("current_round", 1)
        payment_day = data.get("payment_day", "N/A")

        return (
            f"🔔 <b>THÔNG BÁO LỊCH KHUI HỤI / BỎ THĂM</b> 🔔\n\n"
            f"<b>Mã chân hụi:</b> <code>{member_id}</code>\n"
            f"<b>Người chơi:</b> {player_name} ({parts_count} chân)\n"
            f"<b>Tình trạng:</b> {member_status}\n"
            f"<b>Dây hụi:</b> {data.get('rosca_code', 'N/A')}\n"
            f"<b>Chủ hụi:</b> {data.get('owner_name', 'N/A')}\n"
            f"<b>Kỳ bỏ thăm:</b> Kỳ {current_round} (Hạn khui: Ngày {payment_day} hàng tháng)\n"
            f"<b>Mức bỏ hụi tối thiểu:</b> {data.get('min_bid', '0')} VNĐ\n"
            f"<b>Mức bỏ hụi tối đa:</b> {data.get('max_bid', '0')} VNĐ\n"
            f"{'━' * 15}\n"
            f"<i>Đã đến giờ khui hụi! Quý thành viên vui lòng thực hiện bỏ thăm / khui hụi kỳ này. Chúc Quý thành viên gặp nhiều may mắn!</i>"
        )

    @staticmethod
    def _build_defaulted_message(data: dict) -> str:
        member_id = data.get("member_id")
        if not member_id or member_id == "N/A":
            return (
                "🔔 <b>CẢNH BÁO BỂ HỤI / TRỄ HẠN HỤI</b> 🔔\n\n"
                "Vui lòng kiểm tra và xử lý danh sách các chân hụi chưa hoàn thành nghĩa vụ đóng hụi.\n\n"
                "<i>Hệ thống cảnh báo tự động.</i>"
            )

        player_name = data.get("player_name", "N/A")
        member_status = data.get("member_status", "N/A")
        parts_count = data.get("parts_count", 1)

        return (
            f"🔔 <b>CẢNH BÁO BỂ HỤI / TRỄ HẠN HỤI</b> 🔔\n\n"
            f"<b>Mã chân hụi:</b> <code>{member_id}</code>\n"
            f"<b>Người chơi:</b> {player_name} ({parts_count} chân)\n"
            f"<b>Tình trạng:</b> {member_status}\n"
            f"<b>Dây hụi:</b> {data.get('rosca_code', 'N/A')}\n"
            f"<b>Chủ hụi:</b> {data.get('owner_name', 'N/A')}\n"
            f"{'━' * 15}\n"
            f"<i>Vui lòng kiểm tra và xử lý chân hụi chưa hoàn thành nghĩa vụ đóng hụi.</i>"
        )


# ── General Resolver ─────────────────────────────────────────────────────────

class GeneralNotifyResolver:
    """
    Resolver cho module 'general'.
    Tất cả general_* đều là loại tự do — gửi message_template trực tiếp.
    """

    @staticmethod
    def get_pending_items(db: Session, config, current_date: datetime.date, is_test: bool = False) -> Optional[List[dict]]:
        return None  # Luôn trả None — không cần query DB

    @staticmethod
    def build_message(item: Optional[dict], config, days_late: int = 0) -> str:
        if config.message_template:
            return render_template(config.message_template, item or {})
        return "🔔 <b>THÔNG BÁO CHUNG HỆ THỐNG</b> 🔔"


# ── Registry ─────────────────────────────────────────────────────────────────

NOTIFY_RESOLVERS = {
    "credit":  CreditNotifyResolver,
    "rental":  RentalNotifyResolver,
    "rosca":   RoscaNotifyResolver,
    "general": GeneralNotifyResolver,
}
