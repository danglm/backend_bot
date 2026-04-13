import os
import sys
import json
import uvicorn
from pathlib import Path
from pyngrok import ngrok

def update_webhook_url(new_url: str):
    settings_path = Path(__file__).parent / "appsettings.json"
    
    with open(settings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if "Telegram" not in data:
        data["Telegram"] = {}
        
    data["Telegram"]["Webhook_URL"] = new_url
    
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    # Read port from appsettings.json or use default 8000
    settings_path = Path(__file__).parent / "appsettings.json"
    port = 8000
    if settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            port = data.get("Service", {}).get("Port", 8000)

    print(f"[Ngrok] Opening Webhook Tunnel at Port {port}...")
    
    # 1. Start ngrok tunnel
    # Note: If you have an ngrok authtoken, you can set it via ngrok.set_auth_token("TOKEN") 
    # or login in your terminal first: ngrok config add-authtoken <YOUR_TOKEN>
    try:
        http_tunnel = ngrok.connect(port)
        public_url = http_tunnel.public_url
        print(f"[Ngrok] Tunnel URL opened: {public_url}")
    except Exception as e:
        print(f"[Ngrok] Error when creating tunnel: {e}")
        print("Please make sure you have installed ngrok and set authtoken (if needed).")
        sys.exit(1)

    # 2. Update appsettings.json with the new URL
    update_webhook_url(public_url)
    print(f"[Config] Updated Webhook_URL into appsettings.json.")

    # 3. Start uvicorn
    print("[Uvicorn] Starting FastAPI Server...")
    try:
        uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)
    except KeyboardInterrupt:
        print("\n[System] Shutting down server...")
    finally:
        print("[Ngrok] Closing tunnel...")
        ngrok.disconnect(http_tunnel.public_url)
        ngrok.kill()

if __name__ == "__main__":
    main()
