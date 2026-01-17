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
        logger.info(f"Подключение к MongoDB успешно: {config.db.url}")
        
        await init_beanie(
            database=client[config.db.name],
            document_models=[User]
        )
        logger.info(f"База данных инициализирована: {config.db.name}")
        
    except ServerSelectionTimeoutError as e:
        logger.error(
            f"\n{'='*60}\n"
            f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к MongoDB\n"
            f"{'='*60}\n"
            f"📍 Адрес: {config.db.url}\n"
            f"⏱ Таймаут: 10 секунд\n\n"
            f"💡 Возможные причины:\n"
            f"   1. MongoDB не запущен локально (localhost:27017)\n"
            f"   2. Неправильный URL в .env файле\n"
            f"   3. Проблемы с интернетом (для MongoDB Atlas)\n"
            f"   4. Блокировка файрволом/VPN\n\n"
            f"🔧 Решения:\n"
            f"   1. Для локальной MongoDB: запустите 'mongod' в отдельном терминале\n"
            f"   2. Проверьте переменную DB_URL в файле .env\n"
            f"   3. Для MongoDB Atlas: проверьте интернет и настройки файрвола\n"
            f"   4. Отключите VPN если включен\n"
            f"   5. Проверьте, что MongoDB установлен и запущен\n"
            f"{'='*60}\n"
        )
        logger.error(f"Техническая информация: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при подключении к MongoDB: {e}")
        raise
