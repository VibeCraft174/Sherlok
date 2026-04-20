import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен!")

ALLOWED_USERS = None
allowed_str = os.getenv("ALLOWED_USERS", "")
if allowed_str:
    ALLOWED_USERS = [uid.strip() for uid in allowed_str.split(",") if uid.strip()]

BLACKBIRD_PATH = os.getenv("BLACKBIRD_PATH", "/app/blackbird-osint")
