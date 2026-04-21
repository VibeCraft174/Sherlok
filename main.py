import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from elasticsearch import AsyncElasticsearch
from config import BOT_TOKEN, ALLOWED_USERS, ELASTIC_HOST, ELASTIC_USERNAME, ELASTIC_PASSWORD, INDEX_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

es = AsyncElasticsearch(
    [ELASTIC_HOST],
    basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD) if ELASTIC_USERNAME else None,
    verify_certs=False
)

# Клавиатура
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск по индексу")],
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="⚖️ Политика")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

user_consent = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    consent_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен", callback_data="consent_yes")],
            [InlineKeyboardButton(text="❌ Не согласен", callback_data="consent_no")]
        ]
    )
    await message.answer(
        "👋 <b>OSINT Поисковый Бот</b>\n\n"
        "Я индексирую публичные сообщения из открытых Telegram-каналов.\n\n"
        "⚠️ Для использования необходимо согласие на обработку данных (152-ФЗ).\n\n"
        "Ваши данные не передаются третьим лицам.",
        reply_markup=consent_kb
    )

@dp.callback_query(lambda c: c.data.startswith("consent_"))
async def process_consent(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if callback.data == "consent_yes":
        user_consent[user_id] = True
        await callback.message.edit_text("✅ Согласие получено.")
        await callback.message.answer(
            "Вы можете искать по индексу.\n\n"
            "🔍 Нажмите «Поиск по индексу» и введите запрос.",
            reply_markup=main_menu
        )
    else:
        user_consent[user_id] = False
        await callback.message.edit_text("❌ Без согласия использование невозможно.")
    await callback.answer()

@dp.message(lambda msg: msg.text == "🔍 Поиск по индексу")
async def search_prompt(message: types.Message):
    if not user_consent.get(message.from_user.id):
        await message.answer("⚠️ Сначала дайте согласие: /start")
        return
    await message.answer("Введите поисковый запрос:")

@dp.message(lambda msg: msg.text == "📊 Статистика")
async def show_stats(message: types.Message):
    if not user_consent.get(message.from_user.id):
        await message.answer("⚠️ Сначала дайте согласие: /start")
        return
    try:
        count = await es.count(index=INDEX_NAME)
        total = count.get("count", 0)
        await message.answer(f"📊 Всего сообщений в индексе: <b>{total}</b>", parse_mode="HTML")
    except Exception as e:
        logger.error(e)
        await message.answer("⚠️ Ошибка получения статистики.")

@dp.message(lambda msg: msg.text == "⚖️ Политика")
async def show_privacy(message: types.Message):
    await message.answer(
        "📄 <b>Политика конфиденциальности</b>\n\n"
        "1. Собираются только публичные сообщения.\n"
        "2. Данные используются для поиска.\n"
        "3. Вы можете отозвать согласие: /revoke\n"
        "4. Данные не продаются и не передаются.\n"
        "5. Хранение — до 30 дней после отзыва.",
        parse_mode="HTML"
    )

@dp.message(lambda msg: msg.text == "❓ Помощь")
async def help_cmd(message: types.Message):
    await message.answer(
        "❓ <b>Помощь</b>\n\n"
        "🔍 Поиск — нажмите кнопку, введите слово или фразу.\n"
        "📊 Статистика — количество сообщений.\n"
        "⚖️ Политика — правила обработки данных.\n"
        "🚫 /revoke — отозвать согласие.",
        parse_mode="HTML"
    )

@dp.message(Command("revoke"))
async def revoke(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_consent:
        del user_consent[user_id]
        await message.answer("✅ Согласие отозвано. Данные будут удалены в течение 30 дней.")
    else:
        await message.answer("Вы ещё не давали согласия.")

@dp.message(lambda msg: msg.text and msg.text not in ["🔍 Поиск по индексу", "📊 Статистика", "⚖️ Политика", "❓ Помощь"])
async def search_messages(message: types.Message):
    if not user_consent.get(message.from_user.id):
        await message.answer("⚠️ Сначала дайте согласие: /start")
        return
    query = message.text.strip()
    status = await message.answer(f"🔍 Ищу <b>{query}</b>...", parse_mode="HTML")
    try:
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["text^2", "chat_title", "sender_first_name"],
                    "fuzziness": "AUTO"
                }
            },
            "highlight": {"fields": {"text": {"fragment_size": 200, "number_of_fragments": 2}}},
            "size": 8,
            "sort": [{"date": "desc"}]
        }
        resp = await es.search(index=INDEX_NAME, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            await status.edit_text(f"❌ Ничего не найдено по запросу «{query}».")
            return
        result_text = f"✅ <b>Результаты по запросу:</b> «{query}»\n\n"
        for hit in hits[:5]:
            src = hit["_source"]
            highlight = hit.get("highlight", {}).get("text", [""])[0]
            text_preview = highlight if highlight else (src.get("text", "")[:150] + "...")
            result_text += (
                f"📌 <b>{src.get('chat_title', '?')}</b>\n"
                f"   👤 {src.get('sender_first_name', 'Аноним')}\n"
                f"   🕒 {src.get('date', '')[:10]}\n"
                f"   📝 {text_preview}\n"
                f"   🔗 t.me/{src.get('chat_username')}/{src.get('message_id')}\n\n"
            )
        await status.edit_text(result_text, disable_web_page_preview=True)
    except Exception as e:
        logger.error(e)
        await status.edit_text("⚠️ Ошибка поиска. Попробуйте позже.")

async def main():
    logger.info("Поисковый бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
