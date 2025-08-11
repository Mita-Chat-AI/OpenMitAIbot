from aiogram import Dispatcher, Bot
import asyncio

from settings.main import config
from src.utils.startup import startup
from src.utils.shutdown import shutdown

async def main() -> None:
    bot = Bot(token=config.telegram.bot_token.get_secret_value())
    dp = Dispatcher()

    @dp.startup()
    async def on_startup():
        await startup(bot)

    @dp.shutdown()
    async def on_shutdown():
        await shutdown(bot)

    try:
        await dp.start_polling(bot)
        
    finally:
        await bot.session.close()

asyncio.run(main())
