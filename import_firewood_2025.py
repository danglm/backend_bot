"""
Import dữ liệu từ sheet 'CỦI MỚI' (CS Tiến Nga 2025.xlsx) vào bảng firewood_purchases.
- Bước 1: Tạo bản ghi customers mới cho KH chưa có mã FW
- Bước 2: Import 120 dòng firewood purchases
- Có check trùng → chạy lại an toàn
"""
import sys
import io
import uuid
import openpyxl
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'd:\ExtraJob\backend')

from app.db.session import SessionLocal
from app.models.business import Customers, FirewoodPurchases

# ==================== CONFIG ====================
EXCEL_PATH = r'd:\ExtraJob\backend\CS Tiến Nga 2025.xlsx'
SHEET_NAME = 'CỦI MỚI'

# Mapping: Tên KH trong Excel → hoursehold_id (FW prefix)
CUSTOMER_MAP = {
    'hiện vh':      'FW001',
    'bảo trà cụ':  'FW002',
    'cô linh':     'FW003',
    'thuận':        'FW004',
}

# KH cần tạo mới trong bảng customers (copy info từ bản ghi X-prefix)
NEW_FW_CUSTOMERS = {
    'FW003': {
        'source_hoursehold_id': 'X027',   # Cô Linh
        'fullname': 'Cô Linh',
    },
    'FW004': {
        'source_hoursehold_id': 'X115',   # Thuận
        'fullname': 'Thuận',
    },
}


def create_fw_customers(db):
    """Bước 1: Tạo bản ghi customers mới cho KH chưa có mã FW."""
    created = 0
    for fw_id, info in NEW_FW_CUSTOMERS.items():
        existing = db.query(Customers).filter(Customers.hoursehold_id == fw_id).first()
        if existing:
            print(f"  ⏭️  {fw_id} ({info['fullname']}) đã tồn tại → bỏ qua")
            continue

        # Lấy thông tin từ bản ghi gốc
        source = db.query(Customers).filter(
            Customers.hoursehold_id == info['source_hoursehold_id']
        ).first()

        new_cust = Customers(
            id=str(uuid.uuid4()),
            fullname=info['fullname'],
            hoursehold_id=fw_id,
            collection_point_id=source.collection_point_id if source else None,
            number_phone=source.number_phone if source else None,
            address=source.address if source else None,
            ingredient='Củi',
            amount_of_debt=0,
            cash_advance=0,
            total_debt=0,
            status='ACTIVE',
            username=source.username if source else None,
            is_subsidized=0,
        )
        db.add(new_cust)
        created += 1
        print(f"  ✅ Tạo mới {fw_id} - {info['fullname']}")

    if created > 0:
        db.commit()
    print(f"  → Tạo mới: {created} KH\n")


def fmt_vehicle_size(val):
    """Convert 14.0 → '14', 13.5 → '13.5'"""
    if val is None:
        return ''
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return str(val)


def import_firewood(db):
    """Bước 2: Import dữ liệu từ Excel vào firewood_purchases."""
    print("Đang đọc file Excel...")
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True, read_only=True)
    ws = wb[SHEET_NAME]

    total = 0
    inserted = 0
    skipped_dup = 0
    skipped_empty = 0
    errors = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        total += 1

        # Lấy giá trị các cột
        ngay = row[0]       # C1: NGÀY
        ma_cui = row[1]     # C2: MÃ CỦI
        kich_thuoc = row[2] # C3: KÍCH THƯỚC XE
        so_chuyen = row[3]  # C4: SỐ LƯỢNG CHUYẾN
        khoi_luong = row[4] # C5: KHỐI LƯỢNG CỦI
        don_gia = row[5]    # C6: ĐƠN GIÁ
        thanh_tien = row[6] # C7: THÀNH TIỀN
        tam_ung = row[7] if len(row) > 7 else None  # C8: TẠM ỨNG

        # Bỏ qua dòng trống
        if not ngay or not ma_cui:
            skipped_empty += 1
            continue

        # Lookup hoursehold_id
        name_lower = str(ma_cui).strip().lower()
        hoursehold_id = CUSTOMER_MAP.get(name_lower)
        if not hoursehold_id:
            print(f"  ⚠️  Row {total+1}: Không tìm thấy KH '{ma_cui}' trong mapping → bỏ qua")
            errors += 1
            continue

        # Convert types
        try:
            day_val = ngay.date() if isinstance(ngay, datetime) else ngay
            vehicle_size = fmt_vehicle_size(kich_thuoc)
            trip_count = int(float(so_chuyen)) if so_chuyen else 0
            firewood_weight = float(khoi_luong) if khoi_luong else 0
            unit_price = float(don_gia) if don_gia else 0
            total_amount = float(thanh_tien) if thanh_tien else 0
            advance_amount = float(tam_ung) if tam_ung else 0
        except Exception as e:
            print(f"  ❌ Row {total+1}: Lỗi convert dữ liệu: {e}")
            errors += 1
            continue

        # Check trùng
        existing = db.query(FirewoodPurchases).filter(
            FirewoodPurchases.day == day_val,
            FirewoodPurchases.hoursehold_id == hoursehold_id,
            FirewoodPurchases.trip_count == trip_count,
            FirewoodPurchases.firewood_weight == firewood_weight,
        ).first()
        if existing:
            skipped_dup += 1
            continue

        # Insert
        new_purchase = FirewoodPurchases(
            id=uuid.uuid4(),
            day=day_val,
            hoursehold_id=hoursehold_id,
            vehicle_size=vehicle_size,
            trip_count=trip_count,
            firewood_weight=firewood_weight,
            unit_price=unit_price,
            total_amount=total_amount,
            advance_amount=advance_amount,
        )
        db.add(new_purchase)
        inserted += 1

    db.commit()
    wb.close()

    print(f"\n{'='*40}")
    print(f"  Tổng dòng đọc:    {total}")
    print(f"  ✅ Đã thêm:        {inserted}")
    print(f"  ⏭️  Trùng (bỏ qua): {skipped_dup}")
    print(f"  ⏭️  Trống (bỏ qua): {skipped_empty}")
    print(f"  ❌ Lỗi:            {errors}")
    print(f"{'='*40}")


if __name__ == '__main__':
    db = SessionLocal()
    try:
        print("=" * 40)
        print("IMPORT DỮ LIỆU CỦI MỚI")
        print("=" * 40)

        print("\n[Bước 1] Tạo KH củi mới (FW prefix)...")
        create_fw_customers(db)

        print("[Bước 2] Import firewood purchases...")
        import_firewood(db)

        print("\nHoàn tất! ✅")
    except Exception as e:
        db.rollback()
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
