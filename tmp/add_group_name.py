import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlalchemy import text

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE telegram_project_members ADD COLUMN group_name VARCHAR;"))
    print("Column 'group_name' added successfully.")
except Exception as e:
    print(f"Error adding column: {e}")
