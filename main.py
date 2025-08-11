from aiogram import Dispatcher, Bot
import asyncio

from settings.main import config
from src.utils.startup import startup

async def main() -> None:
    bot = Bot(
        token=config.telegram.bot_token.get_secret_value()
    )

    dp = Dispatcher()

    @dp.startup()
    async def on_startup():
        await startup(bot)

    await dp.start_polling(bot)



asyncio.run(main())