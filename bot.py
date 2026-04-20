import asyncio
import logging
import subprocess
import tempfile
import os
import shlex
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN, ALLOWED_USERS, SHERLOCK_PATH, BLACKBIRD_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Правильная инициализация бота для aiogram 3.7+
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Простое меню с одной кнопкой
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Найти по username")]
    ],
    resize_keyboard=True
)

def is_allowed(user_id: int) -> bool:
    if ALLOWED_USERS is None:
        return True
    return str(user_id) in ALLOWED_USERS

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("🚫 Доступ запрещён.")
        return
    await message.answer(
        "👋 Привет! Я бот для поиска публичных профилей.\n\n"
        "Нажми кнопку «🔍 Найти по username» и введи никнейм.\n"
        "Я проверю его на 700+ сайтах (Instagram, Twitter, TikTok и др.)",
        reply_markup=main_menu
    )

@dp.message(lambda msg: msg.text == "🔍 Найти по username")
async def ask_username(message: types.Message):
    await message.answer("Введите username (например, elonmusk или @johndoe):")

@dp.message(lambda msg: msg.text and not msg.text.startswith("/") and msg.text != "🔍 Найти по username")
async def search_username(message: types.Message):
    username = message.text.strip().lstrip('@')
    status_msg = await message.answer(f"🔍 Ищу <b>{username}</b>... Это может занять до минуты.")

    try:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
            report_path = tmp.name

        # Используем Blackbird (700+ сайтов) если он есть, иначе Sherlock
        if os.path.exists(BLACKBIRD_PATH):
            cmd = f"cd {shlex.quote(BLACKBIRD_PATH)} && python -m blackbird -u {shlex.quote(username)} -o {shlex.quote(report_path)}"
        else:
            cmd = f"cd {shlex.quote(SHERLOCK_PATH)} && python -m sherlock {shlex.quote(username)} --output {shlex.quote(report_path)}"

        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()

        if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if len(content) > 3500:
                await message.answer_document(FSInputFile(report_path, filename=f"{username}_report.txt"), caption=f"📄 Результаты для {username}")
                await status_msg.delete()
            else:
                await status_msg.edit_text(f"✅ <b>Найденные профили:</b>\n<pre>{content}</pre>")
        else:
            await status_msg.edit_text(f"❌ Не найдено ни одного публичного профиля для <b>{username}</b>.")

    except Exception as e:
        logger.exception("Ошибка поиска")
        await status_msg.edit_text("⚠️ Произошла ошибка. Попробуйте позже.")
    finally:
        if os.path.exists(report_path):
            os.unlink(report_path)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)

async def main():
    logger.info("Бот запущен и готов к работе")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
