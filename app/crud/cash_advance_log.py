from typing import List, Optional
from datetime import date, datetime, time

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.business import CashAdvanceLog, Customers, CollectionPoint

ENTRY_TYPES = ("ADVANCE", "DEDUCT")
ADVANCE_TYPES = ("SEASON_END", "IN_MONTH")

# Số dư của mỗi loại ứng nằm ở một cột riêng trên customers.
BALANCE_COLUMN = {
    "SEASON_END": "cash_advance",
    "IN_MONTH": "cash_advance_monthly",
}


def _apply_filters(
    query,
    hoursehold_id: Optional[str] = None,
    collection_point_id: Optional[List[str]] = None,
    entry_type: Optional[str] = None,
    advance_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    is_over_limit: Optional[bool] = None,
):
    if hoursehold_id:
        query = query.filter(CashAdvanceLog.hoursehold_id == hoursehold_id)
    if collection_point_id:
        query = query.filter(CashAdvanceLog.collection_point_id.in_(collection_point_id))
    if entry_type:
        query = query.filter(CashAdvanceLog.entry_type == entry_type.upper())
    if advance_type:
        query = query.filter(CashAdvanceLog.advance_type == advance_type.upper())
    if start_date:
        query = query.filter(CashAdvanceLog.created_at >= datetime.combine(start_date, time.min))
    if end_date:
        # end_date là ngày, phải lấy hết ngày đó chứ không cắt ở 00:00.
        query = query.filter(CashAdvanceLog.created_at <= datetime.combine(end_date, time.max))
    if is_over_limit is not None:
        query = query.filter(CashAdvanceLog.is_over_limit.is_(is_over_limit))
    return query


def get_cash_advance_logs(
    db: Session,
    hoursehold_id: Optional[str] = None,
    collection_point_id: Optional[List[str]] = None,
    entry_type: Optional[str] = None,
    advance_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    is_over_limit: Optional[bool] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[dict]:
    """Nhật ký ứng/khấu trừ, mới nhất trước, kèm tên hộ dân và tên điểm thu mua."""
    query = db.query(
        CashAdvanceLog,
        Customers.fullname,
        CollectionPoint.collection_name,
    ).outerjoin(
        Customers, Customers.hoursehold_id == CashAdvanceLog.hoursehold_id
    ).outerjoin(
        CollectionPoint, CollectionPoint.id == CashAdvanceLog.collection_point_id
    )

    query = _apply_filters(
        query, hoursehold_id, collection_point_id, entry_type,
        advance_type, start_date, end_date, is_over_limit,
    )

    rows = query.order_by(CashAdvanceLog.created_at.desc()).offset(offset).limit(limit).all()

    data = []
    for log, fullname, collection_name in rows:
        data.append({
            "id": log.id,
            "hoursehold_id": log.hoursehold_id,
            "collection_point_id": log.collection_point_id,
            "collection_name": collection_name,
            "fullname": fullname,
            "entry_type": log.entry_type,
            "advance_type": log.advance_type,
            "amount": log.amount,
            "balance_before": log.balance_before,
            "balance_after": log.balance_after,
            "is_over_limit": log.is_over_limit,
            "debt_applied": log.debt_applied,
            "debt_before": log.debt_before,
            "debt_after": log.debt_after,
            "approved_by": log.approved_by,
            "created_by": log.created_by,
            "chat_id": log.chat_id,
            "note": log.note,
            "created_at": log.created_at,
        })
    return data


def count_cash_advance_logs(
    db: Session,
    hoursehold_id: Optional[str] = None,
    collection_point_id: Optional[List[str]] = None,
    entry_type: Optional[str] = None,
    advance_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    is_over_limit: Optional[bool] = None,
) -> int:
    query = _apply_filters(
        db.query(func.count(CashAdvanceLog.id)),
        hoursehold_id, collection_point_id, entry_type,
        advance_type, start_date, end_date, is_over_limit,
    )
    return query.scalar() or 0


def delete_cash_advance_logs(db: Session, ids: List) -> dict:
    """Xóa dòng nhật ký và hoàn tác đúng phần số dư mà dòng đó đã ghi.

    Xóa một dòng ADVANCE thì trừ lại `amount` khỏi số dư, xóa một dòng DEDUCT thì
    cộng lại, nhờ vậy customers.cash_advance / cash_advance_monthly luôn khớp với
    phần nhật ký còn lại. Dòng nào có `debt_applied` thì hoàn tác thêm cả
    customers.total_debt theo cùng chiều.

    Lưu ý: balance_before / balance_after của những dòng phát sinh SAU dòng bị xóa
    vẫn giữ giá trị lịch sử nên chuỗi số dư trong nhật ký sẽ không còn nối liền mạch.

    Trả về ``{"deleted": [...], "skipped": [...]}`` — mỗi id xử lý độc lập, một id
    hỏng không chặn các id còn lại.
    """
    deleted = []
    skipped = []

    for log_id in ids:
        log = db.query(CashAdvanceLog).filter(CashAdvanceLog.id == log_id).first()
        if not log:
            skipped.append({"id": str(log_id), "reason": "Không tìm thấy bản ghi nhật ký."})
            continue

        entry_type = (log.entry_type or "").upper()
        column = BALANCE_COLUMN.get((log.advance_type or "").upper())
        if column is None or entry_type not in ENTRY_TYPES:
            skipped.append({
                "id": str(log_id),
                "reason": (
                    f"Bản ghi có entry_type={log.entry_type!r} / advance_type={log.advance_type!r} "
                    "không hợp lệ nên không xác định được số dư cần hoàn tác."
                ),
            })
            continue

        # Khóa dòng hộ dân giống /process-advance-amount: bot và API là hai tiến
        # trình cùng ghi số dư, đọc rồi ghi mà không khóa thì một thao tác sẽ mất.
        # Mọi nhánh thoát bên dưới phải commit hoặc rollback trước khi sang id kế
        # tiếp để không tích lũy khóa gây deadlock.
        customer = db.query(Customers).filter(
            Customers.hoursehold_id == log.hoursehold_id
        ).with_for_update().first()
        if not customer:
            skipped.append({
                "id": str(log_id),
                "reason": f"Không tìm thấy hộ dân có mã {log.hoursehold_id}.",
            })
            db.rollback()
            continue

        amount = int(log.amount or 0)
        balance_before = int(getattr(customer, column) or 0)
        balance_after = balance_before - amount if entry_type == "ADVANCE" else balance_before + amount

        if balance_after < 0:
            skipped.append({
                "id": str(log_id),
                "reason": (
                    f"Hoàn tác sẽ làm số dư ứng của hộ {log.hoursehold_id} bị âm "
                    f"({balance_before:,} - {amount:,}). Hãy kiểm tra các giao dịch phát sinh sau đó."
                ),
            })
            db.rollback()
            continue

        # Dòng nào đã trừ/cộng vào công nợ thì hoàn tác luôn công nợ, ngược chiều
        # với lúc ghi: DEDUCT đã giảm total_debt -> cộng lại, ADVANCE thì ngược lại.
        debt_before = int(customer.total_debt or 0)
        debt_after = debt_before
        if log.debt_applied:
            debt_after = debt_before - amount if entry_type == "ADVANCE" else debt_before + amount
            if debt_after < 0:
                skipped.append({
                    "id": str(log_id),
                    "reason": (
                        f"Hoàn tác sẽ làm công nợ của hộ {log.hoursehold_id} bị âm "
                        f"({debt_before:,} - {amount:,}). Hãy kiểm tra các giao dịch phát sinh sau đó."
                    ),
                })
                db.rollback()
                continue
            customer.total_debt = debt_after

        setattr(customer, column, balance_after)
        db.delete(log)
        db.commit()

        deleted.append({
            "id": str(log_id),
            "hoursehold_id": log.hoursehold_id,
            "entry_type": entry_type,
            "advance_type": (log.advance_type or "").upper(),
            "amount": amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "debt_applied": bool(log.debt_applied),
            "debt_before": debt_before,
            "debt_after": debt_after,
        })

    return {"deleted": deleted, "skipped": skipped}


def get_cash_advance_summary(
    db: Session,
    hoursehold_id: Optional[str] = None,
    collection_point_id: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict:
    """
    Tổng hợp theo hộ dân: cộng dồn ứng/khấu trừ từng loại trong khoảng lọc,
    kèm số dư hiện tại lấy từ bảng customers.
    """
    def _sum_case(entry, adv):
        # Cộng dồn có điều kiện trong một lần quét thay vì 4 truy vấn riêng
        return func.coalesce(func.sum(
            func.coalesce(CashAdvanceLog.amount, 0)
        ).filter(
            CashAdvanceLog.entry_type == entry,
            CashAdvanceLog.advance_type == adv,
        ), 0)

    query = db.query(
        CashAdvanceLog.hoursehold_id.label("hoursehold_id"),
        _sum_case("ADVANCE", "SEASON_END").label("adv_season"),
        _sum_case("ADVANCE", "IN_MONTH").label("adv_monthly"),
        _sum_case("DEDUCT", "SEASON_END").label("ded_season"),
        _sum_case("DEDUCT", "IN_MONTH").label("ded_monthly"),
        func.coalesce(func.count(CashAdvanceLog.id), 0).label("entry_count"),
        func.coalesce(func.count(CashAdvanceLog.id).filter(
            CashAdvanceLog.is_over_limit.is_(True)
        ), 0).label("over_limit_count"),
        func.max(CashAdvanceLog.created_at).label("last_entry_at"),
    )
    query = _apply_filters(
        query, hoursehold_id, collection_point_id,
        None, None, start_date, end_date, None,
    ).group_by(CashAdvanceLog.hoursehold_id)

    rows = query.all()
    if not rows:
        return {
            "total_households": 0,
            "total_advanced": 0,
            "total_deducted": 0,
            "total_outstanding": 0,
            "items": [],
        }

    ids = [r.hoursehold_id for r in rows]
    cust_rows = db.query(Customers, CollectionPoint.collection_name).outerjoin(
        CollectionPoint, CollectionPoint.id == Customers.collection_point_id
    ).filter(Customers.hoursehold_id.in_(ids)).all()
    cust_map = {c.hoursehold_id: (c, cp_name) for c, cp_name in cust_rows}

    items = []
    total_advanced = total_deducted = total_outstanding = 0
    for r in rows:
        customer, cp_name = cust_map.get(r.hoursehold_id, (None, None))
        season = (customer.cash_advance or 0) if customer else 0
        monthly = (customer.cash_advance_monthly or 0) if customer else 0

        advanced = int(r.adv_season) + int(r.adv_monthly)
        deducted = int(r.ded_season) + int(r.ded_monthly)
        total_advanced += advanced
        total_deducted += deducted
        total_outstanding += season + monthly

        items.append({
            "hoursehold_id": r.hoursehold_id,
            "fullname": customer.fullname if customer else None,
            "collection_point_id": customer.collection_point_id if customer else None,
            "collection_name": cp_name,
            "cash_advance": season,
            "cash_advance_monthly": monthly,
            "total_advance": season + monthly,
            "total_advanced_season": int(r.adv_season),
            "total_advanced_monthly": int(r.adv_monthly),
            "total_deducted_season": int(r.ded_season),
            "total_deducted_monthly": int(r.ded_monthly),
            "over_limit_count": int(r.over_limit_count),
            "entry_count": int(r.entry_count),
            "last_entry_at": r.last_entry_at,
        })

    items.sort(key=lambda x: (x["collection_name"] or "", x["hoursehold_id"]))

    return {
        "total_households": len(items),
        "total_advanced": total_advanced,
        "total_deducted": total_deducted,
        "total_outstanding": total_outstanding,
        "items": items,
    }
