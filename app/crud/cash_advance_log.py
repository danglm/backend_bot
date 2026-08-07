from typing import List, Optional
from datetime import date, datetime, time

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.business import CashAdvanceLog, Customers, CollectionPoint

ENTRY_TYPES = ("ADVANCE", "DEDUCT")
ADVANCE_TYPES = ("SEASON_END", "IN_MONTH")


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
