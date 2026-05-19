"""
═══════════════════════════════════════════════════════════════════════════════
  SYNC DATABASE SCHEMA: DEV → PROD
═══════════════════════════════════════════════════════════════════════════════

Script đồng bộ cấu trúc database từ Dev sang Prod.
- So sánh tất cả tables/columns được định nghĩa trong SQLAlchemy models
  với database thực tế trên Prod.
- Tự động phát hiện: bảng thiếu, cột thiếu, cột thừa (chỉ báo cáo, không xóa).
- Hỗ trợ 2 chế độ: DRY-RUN (xem trước) và APPLY (thực thi).

Cách dùng:
  # Xem trước thay đổi (không áp dụng):
  python sync_db_prod.py --dry-run

  # Áp dụng thay đổi lên Prod:
  python sync_db_prod.py --apply

  # Chỉ định DB Prod khác (mặc định đọc từ appsettings.json):
  python sync_db_prod.py --apply --db-url "postgresql://user:pass@host/dbname"

  # Xuất SQL ra file (không thực thi):
  python sync_db_prod.py --export-sql sync_changes.sql
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# ── Ensure project root is in sys.path ──────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# ── Import all models so Base.metadata is fully populated ───────────────────
from app.db.base import Base
from app.models import business, credit, device, employee, finance
from app.models import inventory, rental, rosca, task, telegram, vehicle


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

def load_db_url_from_settings() -> str:
    """Load DB connection string from appsettings.json."""
    settings_path = PROJECT_ROOT / "appsettings.json"
    if not settings_path.exists():
        print("❌ appsettings.json not found.")
        sys.exit(1)

    with open(settings_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    db = config.get("DB_Config", {})
    user = db.get("Postgres_User", "postgres")
    password = db.get("Postgres_Password", "")
    server = db.get("Postgres_Server", "localhost")
    dbname = db.get("Postgres_DB", "postgres")
    return f"postgresql://{user}:{password}@{server}/{dbname}"


# ═══════════════════════════════════════════════════════════════════════════
# SCHEMA COMPARISON ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def map_column_type(col) -> str:
    """Map SQLAlchemy column type to PostgreSQL DDL type string."""
    from sqlalchemy import Integer, String, Float, Boolean, Date, DateTime, Text
    from sqlalchemy.dialects.postgresql import UUID

    col_type = col.type

    if isinstance(col_type, UUID):
        return "UUID"
    elif isinstance(col_type, Integer):
        return "INTEGER"
    elif isinstance(col_type, Float):
        return "DOUBLE PRECISION"
    elif isinstance(col_type, String):
        if col_type.length:
            return f"VARCHAR({col_type.length})"
        return "VARCHAR"
    elif isinstance(col_type, Boolean):
        return "BOOLEAN"
    elif isinstance(col_type, Date):
        return "DATE"
    elif isinstance(col_type, DateTime):
        return "TIMESTAMP WITHOUT TIME ZONE"
    elif isinstance(col_type, Text):
        return "TEXT"
    else:
        # Fallback: use the compile output
        try:
            from sqlalchemy.dialects import postgresql
            return col_type.compile(dialect=postgresql.dialect()).upper()
        except Exception:
            return str(col_type).upper()


def get_column_default_sql(col) -> str:
    """Get the DEFAULT clause for a column."""
    if col.server_default is not None:
        return str(col.server_default.arg)
    if col.default is not None:
        if col.default.is_scalar:
            val = col.default.arg
            if isinstance(val, bool):
                return "TRUE" if val else "FALSE"
            elif isinstance(val, (int, float)):
                return str(val)
            elif isinstance(val, str):
                return f"'{val}'"
    return ""


def compare_schemas(engine: Engine) -> dict:
    """
    Compare SQLAlchemy model definitions (Base.metadata) with the live database.
    
    Returns a dict with:
      - tables_to_create: list of (table_name, list_of_columns)
      - columns_to_add: list of (table_name, column_name, column_obj)
      - extra_columns: list of (table_name, column_name) — exist in DB but not in models
      - summary: text summary
    """
    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())
    model_tables = Base.metadata.tables

    result = {
        "tables_to_create": [],
        "columns_to_add": [],
        "extra_columns": [],
        "sql_statements": [],
    }

    for table_name, table_obj in model_tables.items():
        if table_name not in db_tables:
            # ── Entire table is missing ─────────────────────────────────
            result["tables_to_create"].append((table_name, table_obj))
        else:
            # ── Table exists, compare columns ───────────────────────────
            db_columns = {c["name"]: c for c in inspector.get_columns(table_name)}
            model_columns = {c.name: c for c in table_obj.columns}

            for col_name, col_obj in model_columns.items():
                if col_name not in db_columns:
                    result["columns_to_add"].append((table_name, col_name, col_obj))

            for col_name in db_columns:
                if col_name not in model_columns:
                    result["extra_columns"].append((table_name, col_name))

    return result


def generate_sql(result: dict) -> list[str]:
    """Generate SQL statements from comparison results."""
    statements = []

    # ── CREATE TABLE statements ─────────────────────────────────────────
    for table_name, table_obj in result["tables_to_create"]:
        col_defs = []
        pk_cols = []

        for col in table_obj.columns:
            col_type = map_column_type(col)
            parts = [f'    "{col.name}" {col_type}']

            if col.primary_key:
                pk_cols.append(f'"{col.name}"')

            if not col.nullable and not col.primary_key:
                parts.append("NOT NULL")

            default = get_column_default_sql(col)
            if default:
                parts.append(f"DEFAULT {default}")

            col_defs.append(" ".join(parts))

        if pk_cols:
            col_defs.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")

        sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n'
        sql += ",\n".join(col_defs)
        sql += "\n);"
        statements.append(sql)

    # ── ALTER TABLE ADD COLUMN statements ───────────────────────────────
    for table_name, col_name, col_obj in result["columns_to_add"]:
        col_type = map_column_type(col_obj)
        parts = [f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{col_name}" {col_type}']

        default = get_column_default_sql(col_obj)
        if default:
            parts.append(f"DEFAULT {default}")

        if not col_obj.nullable:
            # Thêm cột NOT NULL cần DEFAULT, nếu không có thì bỏ qua NOT NULL
            if default:
                parts.append("NOT NULL")

        statements.append(" ".join(parts) + ";")

    return statements


# ═══════════════════════════════════════════════════════════════════════════
# SEED DATA (cho các cột mới cần giá trị mặc định)
# ═══════════════════════════════════════════════════════════════════════════

def generate_seed_sql() -> list[str]:
    """Generate SQL to seed code_prefix for existing collection_points."""
    return [
        "-- Seed code_prefix cho các điểm thu mua hiện có",
        "UPDATE collection_points SET code_prefix = 'LT' WHERE collection_name LIKE '%Lạc Tánh%' AND (code_prefix IS NULL OR code_prefix = '');",
        "UPDATE collection_points SET code_prefix = 'P' WHERE collection_name LIKE '%Phê%' AND (code_prefix IS NULL OR code_prefix = '');",
        "UPDATE collection_points SET code_prefix = 'GA' WHERE collection_name LIKE '%Gia An%' AND (code_prefix IS NULL OR code_prefix = '');",
        "UPDATE collection_points SET code_prefix = 'DLH' WHERE collection_name LIKE '%Hải%' AND (code_prefix IS NULL OR code_prefix = '');",
        "UPDATE collection_points SET code_prefix = 'DLT' WHERE collection_name LIKE '%Trang%' AND (code_prefix IS NULL OR code_prefix = '');",
        "UPDATE collection_points SET code_prefix = 'DLV' WHERE collection_name LIKE '%Vui%' AND (code_prefix IS NULL OR code_prefix = '');",
    ]


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def print_header():
    # Fix Windows console encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 70)
    print("  SYNC DATABASE SCHEMA: DEV -> PROD")
    print(f"  Thoi gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Đồng bộ cấu trúc DB từ Dev sang Prod"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true",
                       help="Chỉ xem trước thay đổi, không áp dụng")
    group.add_argument("--apply", action="store_true",
                       help="Áp dụng thay đổi lên database")
    group.add_argument("--export-sql", type=str, metavar="FILE",
                       help="Xuất SQL ra file (không thực thi)")

    parser.add_argument("--db-url", type=str, default=None,
                        help="Connection string PostgreSQL (mặc định đọc từ appsettings.json)")
    parser.add_argument("--include-seed", action="store_true", default=True,
                        help="Bao gồm SQL seed data (mặc định: có)")
    parser.add_argument("--no-seed", action="store_true",
                        help="Không bao gồm seed data")

    args = parser.parse_args()

    print_header()

    # ── Resolve DB URL ──────────────────────────────────────────────────
    db_url = args.db_url or load_db_url_from_settings()
    # Mask password in display
    display_url = db_url
    if "@" in db_url:
        pre_at = db_url.split("@")[0]
        if ":" in pre_at:
            parts = pre_at.rsplit(":", 1)
            display_url = f"{parts[0]}:****@{db_url.split('@')[1]}"
    print(f"\n🔗 Database: {display_url}")

    # ── Connect and compare ─────────────────────────────────────────────
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Kết nối database thành công.\n")
    except Exception as e:
        print(f"❌ Không thể kết nối database: {e}")
        sys.exit(1)

    result = compare_schemas(engine)
    sql_statements = generate_sql(result)

    # Add seed data
    seed_sql = []
    if not args.no_seed:
        seed_sql = generate_seed_sql()

    # ── Report ──────────────────────────────────────────────────────────
    has_changes = bool(result["tables_to_create"] or result["columns_to_add"])

    if result["tables_to_create"]:
        print(f"📦 Bảng mới cần tạo: {len(result['tables_to_create'])}")
        for tname, tobj in result["tables_to_create"]:
            col_names = [c.name for c in tobj.columns]
            print(f"   ├── {tname} ({len(col_names)} cột)")
            for cname in col_names:
                print(f"   │   └── {cname}")

    if result["columns_to_add"]:
        print(f"\n🔧 Cột mới cần thêm: {len(result['columns_to_add'])}")
        for tname, cname, cobj in result["columns_to_add"]:
            ctype = map_column_type(cobj)
            print(f"   ├── {tname}.{cname} ({ctype})")

    if result["extra_columns"]:
        print(f"\n⚠️  Cột thừa (có trong DB nhưng không trong model): {len(result['extra_columns'])}")
        for tname, cname in result["extra_columns"]:
            print(f"   ├── {tname}.{cname}")
        print("   └── (Các cột này KHÔNG bị xóa. Xóa thủ công nếu cần.)")

    if not has_changes and not seed_sql:
        print("\n✅ Database đã đồng bộ. Không cần thay đổi gì.")
        return

    if not has_changes:
        print("\n✅ Cấu trúc bảng đã đồng bộ.")

    # ── Show SQL ────────────────────────────────────────────────────────
    all_sql = sql_statements + (seed_sql if seed_sql else [])

    print(f"\n{'─' * 70}")
    print("📋 SQL sẽ được thực thi:")
    print(f"{'─' * 70}")
    for stmt in all_sql:
        print(f"  {stmt}")
    print(f"{'─' * 70}\n")

    # ── Execute based on mode ───────────────────────────────────────────
    if args.dry_run:
        print("🔍 [DRY-RUN] Không có thay đổi nào được áp dụng.")
        print("   Chạy lại với --apply để thực thi.\n")

    elif args.export_sql:
        export_path = Path(args.export_sql)
        header = (
            f"-- ═══════════════════════════════════════════════════════\n"
            f"-- SYNC DB SCHEMA: DEV -> PROD\n"
            f"-- Generated: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n"
            f"-- Database: {display_url}\n"
            f"-- ═══════════════════════════════════════════════════════\n\n"
            f"BEGIN;\n\n"
        )
        footer = "\nCOMMIT;\n"

        with open(export_path, "w", encoding="utf-8") as f:
            f.write(header)
            for stmt in all_sql:
                if stmt.startswith("--"):
                    f.write(f"{stmt}\n")
                else:
                    f.write(f"{stmt}\n\n")
            f.write(footer)

        print(f"📄 SQL đã được xuất ra: {export_path.resolve()}")

    elif args.apply:
        print("🚀 Đang áp dụng thay đổi...")
        try:
            with engine.begin() as conn:
                executed = 0
                for stmt in all_sql:
                    if stmt.startswith("--"):
                        continue  # Skip comments
                    conn.execute(text(stmt))
                    executed += 1
                    print(f"   ✅ {stmt[:80]}{'...' if len(stmt) > 80 else ''}")

            print(f"\n🎉 Hoàn tất! Đã thực thi {executed} câu lệnh SQL.")
        except Exception as e:
            print(f"\n❌ Lỗi khi áp dụng: {e}")
            print("   Tất cả thay đổi đã bị rollback.")
            sys.exit(1)

    # ── Final summary ───────────────────────────────────────────────────
    print("\n📊 Tóm tắt:")
    print(f"   • Bảng mới: {len(result['tables_to_create'])}")
    print(f"   • Cột mới: {len(result['columns_to_add'])}")
    print(f"   • Cột thừa (không xóa): {len(result['extra_columns'])}")
    print(f"   • Seed SQL: {len([s for s in seed_sql if not s.startswith('--')])}")
    print()


if __name__ == "__main__":
    main()
