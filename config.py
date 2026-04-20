import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

# ALLOWED_USERS теперь опционально. Если переменная не задана или пуста, бот пускает всех.
allowed_users_str = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS = [uid.strip() for uid in allowed_users_str.split(",") if uid.strip()] if allowed_users_str else None

SHERLOCK_PATH = os.getenv("SHERLOCK_PATH", "/app/sherlock")
