import os
import sys
import json
import socket
import uvicorn
import yaml
from pathlib import Path
from urllib.parse import urlparse
from pyngrok import ngrok, conf

# Force IPv4 to avoid IPv6 connectivity issues with ngrok CRL servers
_original_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(*args, **kwargs):
    responses = _original_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET] or responses
socket.getaddrinfo = _ipv4_only_getaddrinfo

BASE_DIR = Path(__file__).parent


def load_ngrok_config():
    """Load ngrok authtoken and region from ngrok_token.yml"""
    ngrok_config_path = BASE_DIR / "ngrok_token.yml"
    if not ngrok_config_path.exists():
        print("[Ngrok] Warning: ngrok_token.yml not found. Proceeding without authtoken.")
        return None, "us"

    with open(ngrok_config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    authtoken = config.get("authtoken", "")
    region = config.get("region", "us")
    return authtoken, region


def load_app_settings():
    """Load appsettings.json and return the full config dict."""
    settings_path = BASE_DIR / "appsettings.json"
    with open(settings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_static_domain(app_config: dict) -> str:
    """Extract the static ngrok domain from Webhook_URL in appsettings.json.
    
    E.g. 'https://nonsuggestively-approvable-oswaldo.ngrok-free.dev' -> 
         'nonsuggestively-approvable-oswaldo.ngrok-free.dev'
    """
    webhook_url = app_config.get("Telegram", {}).get("Webhook_URL", "")
    if not webhook_url:
        return ""
    parsed = urlparse(webhook_url)
    return parsed.hostname or ""


def main():
    # ── 0. Load configurations ──────────────────────────────────────
    app_config = load_app_settings()
    port = app_config.get("Service", {}).get("Port", 8000)

    authtoken, region = load_ngrok_config()
    static_domain = get_static_domain(app_config)

    # ── 1. Configure pyngrok ────────────────────────────────────────
    if authtoken:
        conf.get_default().auth_token = authtoken
        conf.get_default().region = region
        print(f"[Ngrok] Authtoken loaded (region: {region})")
    else:
        print("[Ngrok] No authtoken configured – static domain will NOT work.")

    # ── 2. Start ngrok tunnel ───────────────────────────────────────
    print(f"[Ngrok] Opening tunnel at port {port}...")
    try:
        if static_domain:
            # Use the static (free-tier) domain so URL stays the same
            http_tunnel = ngrok.connect(
                port,
                "http",
                hostname=static_domain,
            )
            print(f"[Ngrok] Static domain tunnel opened: {http_tunnel.public_url}")
        else:
            # Fallback: let ngrok assign a random URL
            http_tunnel = ngrok.connect(port)
            print(f"[Ngrok] Random tunnel opened: {http_tunnel.public_url}")
    except Exception as e:
        print(f"[Ngrok] Error creating tunnel: {e}")
        print("  → Make sure ngrok is installed and your authtoken is valid.")
        print("  → If using a static domain, verify it exists in your ngrok dashboard.")
        sys.exit(1)

    public_url = http_tunnel.public_url
    print(f"[Ngrok] Webhook URL: {public_url}")

    # ── 3. Start uvicorn (FastAPI) ──────────────────────────────────
    print(f"[Uvicorn] Starting FastAPI on 127.0.0.1:{port} ...")
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

