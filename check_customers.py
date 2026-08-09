import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import SessionLocal
from app.models.business import Customers

db = SessionLocal()

print("=== CUSTOMER COUNTS BY INGREDIENT ===")
from sqlalchemy import func
results = db.query(Customers.ingredient, func.count(Customers.id)).group_by(Customers.ingredient).all()
for ing, count in results:
    print(f"Ingredient: {ing} | Count: {count}")

print("\n=== SAMPLE CUSTOMERS ===")
custs = db.query(Customers).limit(10).all()
for c in custs:
    print(f"ID: {c.id} | Code: {c.hoursehold_id} | Name: {c.fullname} | Ingredient: {c.ingredient} | Status: {c.status}")

db.close()
