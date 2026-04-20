import asyncio
import logging
import subprocess
import tempfile
import os
import shlex
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode
from config import BOT_TOKEN, ALLOWED_USERS, SHERLOCK_PATH, BLACKBIRD_PATH, HOLEHE_PATH
from keyboards import main_menu, get_result_actions
from handlers import router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
dp.include_router(router)

# Проверка доступа
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
        "🕵️ **Добро пожаловать в OSINT Бот!**\n\n"
        "Я помогу тебе найти публичную информацию о человеке по его цифровому следу.\n\n"
        "Используй кнопки ниже для навигации.",
        reply_markup=main_menu
    )

# Поиск по username
@dp.message(lambda msg: msg.text == "🔍 Поиск по username")
async def username_prompt(message: types.Message):
    await message.answer("Введите username для поиска:")

@dp.message(lambda msg: msg.text and not msg.text.startswith("/") and len(msg.text) < 50)
async def perform_search(message: types.Message):
    username = message.text.strip().lstrip('@')
    status_msg = await message.answer(f"🔍 Ищу `{username}` на 400+ сайтах...\n⏳ Это может занять 30-60 секунд.", parse_mode="Markdown")

    try:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
            report_path = tmp.name

        # Используем Blackbird, если доступен, иначе Sherlock
        if os.path.exists(BLACKBIRD_PATH):
            cmd = f"cd {shlex.quote(BLACKBIRD_PATH)} && python -m blackbird -u {shlex.quote(username)} -o {shlex.quote(report_path)}"
        else:
            cmd = f"cd {shlex.quote(SHERLOCK_PATH)} && python -m sherlock {shlex.quote(username)} --output {shlex.quote(report_path)} --print-found"

        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            await status_msg.edit_text(f"❌ Ничего не найдено для `{username}`.\n\nВозможно, профиль не существует или скрыт.", parse_mode="Markdown")
            if os.path.exists(report_path):
                os.unlink(report_path)
            return

        if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if len(content) > 3500:
                await message.answer_document(FSInputFile(report_path, filename=f"{username}_osint.txt"), caption=f"📄 Результаты для @{username}")
                await status_msg.delete()
            else:
                await status_msg.edit_text(f"✅ **Найденные профили для @{username}:**\n\n```\n{content}```", parse_mode="Markdown")
        else:
            await status_msg.edit_text(f"❌ Не найдено ни одного публичного профиля для `{username}`.", parse_mode="Markdown")

    except Exception as e:
        logger.exception("Search error")
        await status_msg.edit_text("⚠️ Внутренняя ошибка. Попробуйте позже.")
    finally:
        if os.path.exists(report_path):
            os.unlink(report_path)

async def main():
    logger.info("OSINT Bot запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
