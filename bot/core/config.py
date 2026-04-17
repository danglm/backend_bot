import json
from pathlib import Path

def load_settings():
    # Setup path to appsettings.json
    base_dir = Path(__file__).resolve().parent.parent.parent
    settings_path = base_dir / "appsettings.json"
    
    with open(settings_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Load JSON configurations globally
app_config = load_settings()

class Settings:
    # Read Telegram config from appsettings.json -> "Telegram"
    telegram_config = app_config.get("Telegram", {})
    BOT_TOKEN = telegram_config.get("Bot_Token", "")
    WEBHOOK_URL = telegram_config.get("Webhook_URL", "")
    API_ID = int(telegram_config.get("API_ID", 0)) if telegram_config.get("API_ID") else 0
    API_HASH = telegram_config.get("API_HASH", "")

    # Read Scheduler config from appsettings.json -> "Scheduler"
    scheduler_config = app_config.get("Scheduler", {})
    SCHEDULER_MONTHLY_REPORT = scheduler_config.get("Monthly_Attendance_Report", {"day": 1, "hour": 8, "minute": 0})
    SCHEDULER_RESTART_TASK = scheduler_config.get("Recurring_Task_Restart", {"hour": 22, "minute": 21})
    SCHEDULER_BAD_DEBT = scheduler_config.get("Bad_Debt_Notification", {"hour": 8, "minute": 0})
    SCHEDULER_INTEREST = scheduler_config.get("Interest_Payment_Notification", {"hour": 8, "minute": 0})
    SCHEDULER_RENTAL = scheduler_config.get("Rental_Payment_Notification", {"hour": 16, "minute": 2})
    SCHEDULER_MONTHLY_SUMMARY = scheduler_config.get("Monthly_Attendance_Summary", {"day": 1, "hour": 8, "minute": 0})
    SCHEDULER_DAILY_PURCHASE = scheduler_config.get("Daily_Purchase_Summary", {"hour": 20, "minute": 0})

settings = Settings()
