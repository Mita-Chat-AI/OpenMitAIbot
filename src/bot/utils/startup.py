from loguru import logger

from ...settings.main import config


async def startup(bot):
    try:
        await bot.send_message(
            chat_id=config.telegram.owner_id,
            text='✅ Бот запущен!'
        )
    except Exception as e:
        logger.error(f"Не удалось отправить startup сообщение: {e}")