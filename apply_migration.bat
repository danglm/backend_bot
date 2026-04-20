@echo off
echo Dang cap nhat database len phien ban moi nhat...
call .venv\Scripts\alembic upgrade head
echo Da cap nhat thanh cong!
pause
