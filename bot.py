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
from config import BOT_TOKEN, ALLOWED_USERS, BLACKBIRD_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Клавиатура с кнопками для удобства
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск по username")],
        [KeyboardButton(text="📧 Поиск по email")],
        [KeyboardButton(text="❓ Помощь")]
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
        "Нажми на кнопку и введи никнейм или email.\n"
        "Проверю на 700+ сайтах.",
        reply_markup=main_menu
    )

@dp.message(lambda msg: msg.text == "🔍 Поиск по username")
async def ask_username(message: types.Message):
    await message.answer("Введите username (например, elonmusk):")

@dp.message(lambda msg: msg.text == "📧 Поиск по email")
async def ask_email(message: types.Message):
    await message.answer("Введите email (например, example@gmail.com):")

@dp.message(lambda msg: msg.text == "❓ Помощь")
async def help_cmd(message: types.Message):
    await cmd_start(message)

@dp.message(lambda msg: msg.text and not msg.text.startswith("/") and msg.text not in ["🔍 Поиск по username", "📧 Поиск по email", "❓ Помощь"])
async def search_handler(message: types.Message):
    query = message.text.strip().lower()
    is_email = "@" in query and "." in query.split("@")[-1]
    if is_email:
        await search_email(message, query)
    else:
        await search_username(message, query)

async def search_username(message: types.Message, username: str):
    status_msg = await message.answer(f"🔍 Ищу <b>{username}</b>... Это может занять до минуты.")

    try:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
            report_path = tmp.name

        # Используем Blackbird, он мощнее Sherlock
        cmd = f"cd {shlex.quote(BLACKBIRD_PATH)} && python -m blackbird -u {shlex.quote(username)} -o {shlex.quote(report_path)}"
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

async def search_email(message: types.Message, email: str):
    await message.answer(f"🔍 Проверяю email <b>{email}</b>...")

    try:
        # Проверка через haveibeenpwned API
        cmd = f"curl -s 'https://haveibeenpwned.com/api/v3/breachedaccount/{email}' -H 'hibp-api-key: YOUR_API_KEY'"
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await process.communicate()

        if stdout:
            breaches = stdout.decode('utf-8')
            await message.answer(f"✅ Email <b>{email}</b> найден в утечках:\n<pre>{breaches}</pre>")
        else:
            await message.answer(f"❌ Email <b>{email}</b> не найден в публичных утечках.")
    except Exception as e:
        logger.exception("Ошибка проверки email")
        await message.answer("⚠️ Ошибка при проверке email.")

async def main():
    logger.info("Бот запущен и готов к работе")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
