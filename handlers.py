from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards import main_menu, get_result_actions

router = Router()

@router.message(F.text == "🔍 Поиск по username")
async def username_search_start(message: Message):
    await message.answer(
        "🔎 Введите username для поиска.\n"
        "Username — это уникальный идентификатор на платформах (например: `johndoe` или `@johndoe`).\n\n"
        "Я проверю этот ник на 400+ сайтах: Instagram, Twitter, TikTok, GitHub и многих других.",
        parse_mode="Markdown"
    )

@router.message(F.text == "📧 Поиск по email")
async def email_search_start(message: Message):
    await message.answer(
        "📧 Введите email-адрес для проверки.\n\n"
        "Я проверю, на каких сайтах зарегистрирован этот email, и покажу публичную информацию о нём.",
        parse_mode="Markdown"
    )

@router.message(F.text == "📱 Поиск по номеру телефона")
async def phone_search_start(message: Message):
    await message.answer(
        "📱 Введите номер телефона в международном формате.\n\n"
        "Пример: +79123456789\n\n"
        "⚠️ Поиск по номеру телефона — зона повышенной юридической ответственности!",
        parse_mode="Markdown"
    )

@router.message(F.text == "❓ Помощь")
async def help_cmd(message: Message):
    await message.answer(
        "🤖 **OSINT Бот — инструкция**\n\n"
        "**Что умеет бот:**\n"
        "• Поиск по username — проверка ника на 400+ сайтах\n"
        "• Поиск по email — проверка email в утечках данных\n"
        "• Поиск по номеру телефона — проверка номера в утечках (опционально)\n\n"
        "**Как пользоваться:**\n"
        "1. Нажми на нужную кнопку в меню\n"
        "2. Введи данные для поиска\n"
        "3. Получи результат\n\n"
        "**⚠️ Важное предупреждение:**\n"
        "• Бот собирает только общедоступную информацию\n"
        "• Не используйте бота для незаконных действий\n"
        "• Автор не несёт ответственности за неправомерное использование\n\n"
        "**Поддержка:** @username (твой Telegram для связи)",
        parse_mode="Markdown"
    )
