from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores.fluent_runtime_core import FluentRuntimeCore

from ..settings.main import config
from .containers import Container
from .db.connection import init_db
from .handlers import load_routers
from .utils.shutdown import shutdown
from .utils.startup import startup
from .middlewire.i18nsafemiddleware import I18nSafeMiddleware

async def main() -> None:
    bot = Bot(
        token=config.telegram.bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )
    dp = Dispatcher()

    @dp.startup()
    async def on_startup():
        await startup(bot)
        

    container = Container(bot=bot)
    container.wire(
        modules=[__name__], packages=[
            '.handlers.users'
            ]
    )
    await init_db()
    for router in await load_routers():
        dp.include_routers(router)

    
    # from .services.model_services.user_service import UserManager

    service = container.user_service()
    i18n_middleware = I18nMiddleware(
        
        manager=service.UserManager(service.user_repository),  # передаём self-сервис
        core=FluentRuntimeCore(path="src/bot/locales/{locale}/LC_MESSAGES"),
        default_locale="ru"
    )

    # dp.update.outer_middleware.register(db_middleware.DBMiddleware())





    # 1. Сначала подключаем i18n
    i18n_middleware.setup(dispatcher=dp)

    # 2. Потом SafeMiddleware, чтобы ловил все KeyNotFoundError уже от i18n
    dp.update.outer_middleware.register(I18nSafeMiddleware())

    @dp.shutdown()
    async def on_shutdown():
        await shutdown(bot)


    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

