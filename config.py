import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram Bot Token (от @BotFather) ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "8581137449:AAFK3V7HzSxrrQjBtYH_ulNmCTIocPAhuHU")

# --- Данные для User Bot (получить на my.telegram.org) ---
API_ID = int(os.getenv("API_ID", "0"))          # Сюда вставьте ваш API ID
API_HASH = os.getenv("API_HASH", "")            # Сюда вставьте ваш API Hash

# --- Elasticsearch (Bonsai) ---
ELASTIC_HOST = os.getenv("ELASTIC_HOST", "https://disciplined-yew-1nybpwf4.us-east-1.bonsaisearch.net")
ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME", "139adac7c0")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "")   # Вставьте ваш пароль от Bonsai

# --- Разрешённые пользователи (оставьте пустым для всех) ---
ALLOWED_USERS = None

# --- Имя индекса в Elasticsearch ---
INDEX_NAME = "telegram_messages"

# --- Список каналов для индексации (username без @) ---
CHANNELS_TO_INDEX = [
    "durov", "rianru", "meduzaproject", "rtvimain", "tass_agency", 
    "kommersant", "lentachold", "mash", "baza_news", "readovkanews",
    "svoboda_news", "currenttime", "dw_russian", "bbcnewsrussian",
    "theinsider", "istories_media", "agentstvonews", "proekt_media",
    "vcovne", "yandex", "tjournal", "dtf", "habr_com", "ixbt_live",
    "codewithpoker", "python_jobs", "datascience_news", "ai_machinelearning",
    "pydigger", "flask_ru", "django_ru", "kotlinlang_ru", "golang_ru"
]
