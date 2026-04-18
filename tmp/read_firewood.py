"""Check if firewood customers exist in the customers table."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project to path
sys.path.insert(0, r'd:\ExtraJob\backend')

from app.db.session import SessionLocal
from app.models.business import Customers

db = SessionLocal()
try:
    firewood_names = ['Bảo Trà Cụ', 'Cô Linh', 'Hiện VH', 'Thuận']
    
    print("=== Tìm kiếm KH củi trong bảng customers ===\n")
    for name in firewood_names:
        # Try exact match on fullname
        cust = db.query(Customers).filter(Customers.fullname == name).first()
        if cust:
            print(f"✅ '{name}' → hoursehold_id='{cust.hoursehold_id}', id='{cust.id}'")
        else:
            # Try partial match
            custs = db.query(Customers).filter(Customers.fullname.ilike(f'%{name}%')).all()
            if custs:
                print(f"⚠️ '{name}' → Partial matches:")
                for c in custs:
                    print(f"   - fullname='{c.fullname}', hoursehold_id='{c.hoursehold_id}', id='{c.id}'")
            else:
                print(f"❌ '{name}' → KHÔNG TÌM THẤY trong bảng customers")
    
    print(f"\n=== Tổng KH trong DB: {db.query(Customers).count()} ===")
finally:
    db.close()
