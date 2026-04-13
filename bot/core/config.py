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

settings = Settings()
