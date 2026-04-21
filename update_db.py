from app.db.session import SessionLocal
from sqlalchemy import text

def update_schema():
    db = SessionLocal()
    try:
        try:
            db.execute(text("ALTER TABLE employee ADD COLUMN telegram_group VARCHAR;"))
            print("Added telegram_group to employee")
        except Exception as e:
            print("employee telegram_group:", e)
            db.rollback()

        try:
            db.execute(text("ALTER TABLE customers ADD COLUMN telegram_group VARCHAR;"))
            print("Added telegram_group to customers")
        except Exception as e:
            print("customers telegram_group:", e)
            db.rollback()

        try:
            db.execute(text("ALTER TABLE customers ADD COLUMN number_bank VARCHAR;"))
            print("Added number_bank to customers")
        except Exception as e:
            print("customers number_bank:", e)
            db.rollback()

        try:
            db.execute(text("ALTER TABLE customers ADD COLUMN bank_name VARCHAR;"))
            print("Added bank_name to customers")
        except Exception as e:
            print("customers bank_name:", e)
            db.rollback()

        db.commit()
        print("Schema update completed!")
    finally:
        db.close()

if __name__ == "__main__":
    update_schema()
