import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from bot.core.config import settings
from bot.utils.logger import LogInfo, LogError, LogType

# Import handlers so they are registered with Pyrogram
import bot.handlers

from app.api import hello

from bot.utils.bot import bot
@asynccontextmanager
async def lifespan(app: FastAPI):
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
        daily_purchase_summary_worker,
        daily_factory_purchase_summary_worker,
        daily_fund_summary_worker,
        daily_inventory_summary_worker,
        daily_harvest_summary_worker,
        auto_attendance_worker,
        rosca_payment_notification_worker,
        document_reminder_worker
    )
    asyncio.create_task(checkin_reminder_worker())
    asyncio.create_task(monthly_attendance_report_worker())
    asyncio.create_task(recurring_task_worker())
    asyncio.create_task(bad_debt_notification_worker())
    asyncio.create_task(interest_payment_notification_worker())
    asyncio.create_task(rental_payment_notification_worker())
    asyncio.create_task(monthly_attendance_summary_worker())
    asyncio.create_task(daily_purchase_summary_worker())
    asyncio.create_task(daily_factory_purchase_summary_worker())
    asyncio.create_task(daily_fund_summary_worker())
    asyncio.create_task(daily_inventory_summary_worker())
    asyncio.create_task(daily_harvest_summary_worker())
    asyncio.create_task(auto_attendance_worker())
    asyncio.create_task(rosca_payment_notification_worker())
    asyncio.create_task(document_reminder_worker())

    yield
    
    if bot.is_connected:
        await bot.stop()

app = FastAPI(lifespan=lifespan)

# CORS - cho phép frontend Cloudflare Workers kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hdggroup-frontend-2026.lmd16032002.workers.dev",
        "https://hdg-group-2026.lmd16032002.workers.dev",
        "https://unaffecting-christel-semijocularly.ngrok-free.dev",
        "https://spore-unknown-crank.ngrok-free.dev",
        "https://nonsuggestively-approvable-oswaldo.ngrok-free.dev",
        "http://localhost:5173",   # dev local frontend
        "http://localhost:3000",   # dev local frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello.router)

from app.api.v1 import telegram, auth, business, employee, salary, vehicle, document, credit, rental, tien_nga, attendance, harvest, other, projects
app.include_router(telegram.router, prefix="/api/v1/telegram", tags=["telegram"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(business.router, prefix="/api/v1/business", tags=["business"])
app.include_router(employee.router, prefix="/api/v1/employee", tags=["employee"])
app.include_router(salary.router, prefix="/api/v1", tags=["salary"])
app.include_router(vehicle.router, prefix="/api/v1/vehicle", tags=["vehicle"])
app.include_router(document.router, prefix="/api/v1/vehicle", tags=["document"])
app.include_router(credit.router, prefix="/api/v1/credit", tags=["credit"])
app.include_router(rental.router, prefix="/api/v1/rental", tags=["rental"])
app.include_router(tien_nga.router, prefix="/api/v1/tien-nga", tags=["tien-nga"])
app.include_router(attendance.router, prefix="/api/v1", tags=["attendance"])
app.include_router(harvest.router, prefix="/api/v1/harvest", tags=["harvest"])
app.include_router(other.router, prefix="/api/v1/other", tags=["other"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])



@app.get("/")
async def root():
    return {"message": "Web API + Bot is running!"}
# touch fourth




