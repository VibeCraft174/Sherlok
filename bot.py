import asyncio
import logging
import subprocess
import tempfile
import os
import shlex
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from config import BOT_TOKEN, ALLOWED_USERS, SHERLOCK_PATH

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Проверка доступа (если ALLOWED_USERS задан и не пуст)
def is_allowed(user_id: int) -> bool:
    if ALLOWED_USERS is None:
        return True  # бот открыт для всех
    return str(user_id) in ALLOWED_USERS

# Обработчик /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("🚫 Доступ запрещён.")
        return
    await message.answer(
        "👋 Привет! Я OSINT-бот на основе Sherlock.\n\n"
        "📌 Доступные команды:\n"
        "/search <username> — поиск аккаунта по username на 300+ сайтах\n"
        "/help — показать это сообщение\n\n"
        "⚠️ Используй в образовательных целях."
    )

# Обработчик /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("🚫 Доступ запрещён.")
        return
    await cmd_start(message)  # просто показываем то же самое

# Обработчик /search
@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("🚫 Доступ запрещён.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите username для поиска.\nПример: `/search johndoe`", parse_mode="Markdown")
        return
    username = args[1].strip()

    status_msg = await message.answer(f"🔍 Ищу `{username}`... Это может занять до 30 секунд.", parse_mode="Markdown")

    try:
        # Создаём временный файл для результата
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
            report_path = tmp.name

        # Запускаем Sherlock (предполагается, что он установлен в SHERLOCK_PATH)
        cmd = f"cd {shlex.quote(SHERLOCK_PATH)} && python -m sherlock {shlex.quote(username)} --output {shlex.quote(report_path)}"
        logger.info(f"Executing: {cmd}")

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode('utf-8')
            logger.error(f"Sherlock error: {error_msg}")
            await status_msg.edit_text(f"❌ Ошибка при поиске `{username}`. Возможно, имя не найдено или проблемы с сетью.")
            if os.path.exists(report_path):
                os.unlink(report_path)
            return

        # Проверяем, есть ли результаты
        if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Если результат большой — отправляем файлом
            if len(content) > 3500:
                await message.answer_document(
                    FSInputFile(report_path, filename=f"{username}_sherlock.txt"),
                    caption=f"📄 Результат для `{username}`"
                )
                await status_msg.delete()
            else:
                await status_msg.edit_text(f"✅ Найденные профили для `{username}`:\n\n```\n{content}```", parse_mode="Markdown")
        else:
            await status_msg.edit_text(f"❌ Не найдено ни одного публичного профиля для `{username}`.")

    except Exception as e:
        logger.exception("Unexpected error")
        await status_msg.edit_text("⚠️ Внутренняя ошибка. Попробуйте позже.")
    finally:
        if os.path.exists(report_path):
            os.unlink(report_path)

# (Опционально) Команда /email для поиска по email через haveibeenpwned API
# Если хочешь добавить, дай знать — напишу отдельно.

async def main():
    logger.info("Бот запущен и слушает команды...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
