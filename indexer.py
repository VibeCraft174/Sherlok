import asyncio
import logging
import re
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from elasticsearch import AsyncElasticsearch
from config import API_ID, API_HASH, ELASTIC_HOST, ELASTIC_USERNAME, ELASTIC_PASSWORD, INDEX_NAME, CHANNELS_TO_INDEX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключение к Elasticsearch
es = AsyncElasticsearch(
    [ELASTIC_HOST],
    basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD) if ELASTIC_USERNAME else None,
    verify_certs=False  # для Bonsai может потребоваться
)

async def create_index():
    """Создаёт индекс с русским анализатором, если его нет"""
    if await es.indices.exists(index=INDEX_NAME):
        logger.info(f"Индекс {INDEX_NAME} уже существует")
        return
    mapping = {
        "mappings": {
            "properties": {
                "message_id": {"type": "long"},
                "chat_id": {"type": "long"},
                "chat_username": {"type": "keyword"},
                "chat_title": {"type": "text"},
                "sender_id": {"type": "long"},
                "sender_username": {"type": "keyword"},
                "sender_first_name": {"type": "text"},
                "text": {"type": "text", "analyzer": "russian"},
                "date": {"type": "date"},
                "views": {"type": "integer"},
                "forwards": {"type": "integer"},
                "reply_to_msg_id": {"type": "long"},
                "media": {"type": "boolean"},
                "urls": {"type": "text"},
                "hashtags": {"type": "keyword"}
            }
        },
        "settings": {
            "analysis": {
                "analyzer": {
                    "russian": {
                        "type": "russian"
                    }
                }
            }
        }
    }
    await es.indices.create(index=INDEX_NAME, body=mapping)
    logger.info(f"Индекс {INDEX_NAME} создан")

def extract_urls(text):
    return re.findall(r'https?://[^\s]+', text)

def extract_hashtags(text):
    return re.findall(r'#\w+', text)

async def index_message(message):
    """Индексирует одно сообщение в Elasticsearch"""
    if not message.text or len(message.text.strip()) == 0:
        return
    doc = {
        "message_id": message.id,
        "chat_id": message.chat_id,
        "chat_username": getattr(message.chat, "username", None),
        "chat_title": getattr(message.chat, "title", None),
        "sender_id": message.sender_id,
        "sender_username": getattr(message.sender, "username", None) if message.sender else None,
        "sender_first_name": getattr(message.sender, "first_name", None) if message.sender else None,
        "text": message.text,
        "date": message.date.isoformat() if message.date else datetime.now().isoformat(),
        "views": getattr(message, "views", 0),
        "forwards": getattr(message, "forwards", 0),
        "reply_to_msg_id": getattr(message, "reply_to_msg_id", None),
        "media": bool(message.media),
        "urls": extract_urls(message.text),
        "hashtags": extract_hashtags(message.text)
    }
    await es.index(index=INDEX_NAME, id=f"{message.chat_id}_{message.id}", body=doc, refresh=False)
    logger.debug(f"Индексировано: {message.chat.title} / {message.id}")

async def index_channel_history(client, channel_username, limit=5000):
    """Индексирует историю канала (последние limit сообщений)"""
    try:
        logger.info(f"Начинаю индексацию канала @{channel_username}")
        entity = await client.get_entity(channel_username)
        messages = await client.get_messages(entity, limit=limit)
        count = 0
        for msg in messages:
            await index_message(msg)
            count += 1
            if count % 100 == 0:
                logger.info(f"Проиндексировано {count} сообщений из @{channel_username}")
                await asyncio.sleep(0.5)  # небольшая задержка, чтобы не спамить Elastic
        logger.info(f"Закончена индексация @{channel_username}: {count} сообщений")
    except FloodWaitError as e:
        logger.warning(f"Flood wait {e.seconds} секунд для @{channel_username}")
        await asyncio.sleep(e.seconds)
        await index_channel_history(client, channel_username, limit)
    except Exception as e:
        logger.error(f"Ошибка индексации @{channel_username}: {e}")

async def monitor_new_messages(client):
    """Мониторит новые сообщения во всех каналах, где состоит аккаунт"""
    @client.on(events.NewMessage)
    async def handler(event):
        if event.is_private:
            return
        await index_message(event.message)
        logger.info(f"Новое сообщение от {event.sender_id} в {event.chat.title}")

async def main():
    # Создаём клиента Telethon
    client = TelegramClient("indexer_session", API_ID, API_HASH)
    await client.start()
    logger.info("User Bot авторизован")

    # Создаём индекс в Elasticsearch
    await create_index()

    # Присоединяемся ко всем каналам из списка (если не присоединены)
    for channel in CHANNELS_TO_INDEX:
        try:
            await client(JoinChannelRequest(channel))
            logger.info(f"Присоединился к @{channel}")
        except Exception as e:
            logger.warning(f"Не удалось присоединиться к @{channel}: {e}")

    # Индексация истории каждого канала
    for channel in CHANNELS_TO_INDEX:
        await index_channel_history(client, channel, limit=5000)

    # Запускаем мониторинг новых сообщений
    await monitor_new_messages(client)
    logger.info("Индексатор запущен, ожидаю новые сообщения...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
