from loguru import logger

from ...settings.main import config


async def shutdown(bot):
    try:
        await bot.send_message(
            chat_id=config.telegram.owner_id,
            text='👋 Бот остановлен'
        )
    except Exception as e:
        logger.error(f"Не удалось отправить shutdown сообщение: {e}")