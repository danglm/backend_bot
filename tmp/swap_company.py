from app.db.session import SessionLocal
from app.models.business import CompanyCustomers

db = SessionLocal()
try:
    customers = db.query(CompanyCustomers).all()
    
    seen = set()
    for cust in customers:
        old_id = cust.unit_id
        old_name = cust.unit_name
        
        new_id = old_name
        if new_id in seen:
            new_id = f"{new_id}_2"
        seen.add(new_id)
        
        # update fields
        cust.unit_id = new_id
        cust.unit_name = old_id

    db.commit()
    print(f"Swapped {len(customers)} records successfully!")
except Exception as e:
    db.rollback()
    import traceback
    traceback.print_exc()
finally:
    db.close()
