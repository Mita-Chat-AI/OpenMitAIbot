import asyncio

from aiogram import Bot, Dispatcher

from settings.main import config
from src.handlers import load_routers
from src.utils.shutdown import shutdown
from src.utils.startup import startup


async def main() -> None:
    bot = Bot(
        token=config.telegram.bot_token.get_secret_value()
    )
    dp = Dispatcher()

    @dp.startup()
    async def on_startup():
        await startup(bot)

    for router in await load_routers():
        dp.include_routers(router)

    @dp.shutdown()
    async def on_shutdown():
        await shutdown(bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

asyncio.run(main())
