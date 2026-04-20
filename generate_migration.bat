@echo off
set /p msg="Nhap ten migration (khong dau, vi du: add_new_table): "
call .venv\Scripts\alembic revision --autogenerate -m "%msg%"
echo Da tao xong file migration trong thu muc alembic/versions.
pause
