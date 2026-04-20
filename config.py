import os
from dotenv import load_dotenv

load_dotenv()

# ===== ОТЛАДКА: печатаем все переменные окружения =====
print("=== Все переменные окружения, которые видит Python ===")
for key, value in os.environ.items():
    # Не печатаем полные значения, чтобы случайно не засветить секреты в логах
    print(f"{key} = {repr(value[:20]) if value else 'None'}...")  
print("=== КОНЕЦ СПИСКА ===")

# Проверяем именно BOT_TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN из os.getenv = {repr(BOT_TOKEN)}")

ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",")
SHERLOCK_PATH = os.getenv("SHERLOCK_PATH", "/app/sherlock")

if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")
