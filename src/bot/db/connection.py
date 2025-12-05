from beanie import init_beanie
from pymongo import AsyncMongoClient
from pymongo.errors import ServerSelectionTimeoutError
from loguru import logger

from .models import User
from ...settings.main import config


async def init_db() -> None:
    try:
        client = AsyncMongoClient(
            host=config.db.url,
            serverSelectionTimeoutMS=10000,  # Таймаут 10 секунд
            connectTimeoutMS=10000
        )
        
        # Проверяем подключение
        await client.admin.command('ping')
        logger.success(f"✅ Подключение к MongoDB успешно: {config.db.url}")
        
        await init_beanie(
            database=client[config.db.name],
            document_models=[User]
        )
        logger.success(f"✅ База данных инициализирована: {config.db.name}")
        
    except ServerSelectionTimeoutError as e:
        logger.error(
            f"❌ Не удалось подключиться к MongoDB по адресу: {config.db.url}\n"
            f"💡 Возможные причины:\n"
            f"   1. Проблемы с DNS/интернетом\n"
            f"   2. Блокировка файрволом/VPN\n"
            f"   3. MongoDB Atlas недоступен\n"
            f"💡 Решения:\n"
            f"   1. Проверьте интернет-соединение\n"
            f"   2. Попробуйте другой DNS (8.8.8.8 или 1.1.1.1)\n"
            f"   3. Отключите VPN если включен\n"
            f"   4. Проверьте настройки файрвола\n"
            f"   5. Запустите MongoDB локально: mongod"
        )
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при подключении к MongoDB: {e}")
        raise
