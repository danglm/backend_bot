import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import os
from bot.core.config import settings
from bot.utils.logger import LogInfo, LogError, LogType

# Import handlers so they are registered with Pyrogram
import bot.handlers

from app.api import hello

from bot.utils.bot import bot
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tự động cập nhật database với Alembic khi app start
    import init_db
    LogInfo("[DB] Running automatic database migrations...", LogType.SYSTEM_STATUS)
    init_db.init_db()

    try:
        await bot.start()
        LogInfo("[Bot] Connected to Telegram (Bot API)", LogType.SYSTEM_STATUS)
    except Exception as e:
        LogError(f"[Bot] Error connecting to Telegram: {e}", LogType.SYSTEM_STATUS)

    # Start background scheduler
    from bot.utils.scheduler import (
        checkin_reminder_worker, 
        monthly_attendance_report_worker, 
        recurring_task_worker, 
        bad_debt_notification_worker, 
        interest_payment_notification_worker, 
        rental_payment_notification_worker,
        monthly_attendance_summary_worker,
        daily_purchase_summary_worker
    )
    asyncio.create_task(checkin_reminder_worker())
    asyncio.create_task(monthly_attendance_report_worker())
    asyncio.create_task(recurring_task_worker())
    asyncio.create_task(bad_debt_notification_worker())
    asyncio.create_task(interest_payment_notification_worker())
    asyncio.create_task(rental_payment_notification_worker())
    asyncio.create_task(monthly_attendance_summary_worker())
    asyncio.create_task(daily_purchase_summary_worker())

    yield
    
    if bot.is_connected:
        await bot.stop()

app = FastAPI(lifespan=lifespan)
app.include_router(hello.router)

from app.api.v1 import telegram, auth, business, employee, salary, vehicle, credit, rental
app.include_router(telegram.router, prefix="/api/v1/telegram", tags=["telegram"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(business.router, prefix="/api/v1/business", tags=["business"])
app.include_router(employee.router, prefix="/api/v1/employee", tags=["employee"])
app.include_router(salary.router, prefix="/api/v1/salary", tags=["salary"])
app.include_router(vehicle.router, prefix="/api/v1/vehicle", tags=["vehicle"])
app.include_router(credit.router, prefix="/api/v1/credit", tags=["credit"])
app.include_router(rental.router, prefix="/api/v1/rental", tags=["rental"])

@app.get("/")
async def root():
    return {"message": "Web API + Bot is running!"}

