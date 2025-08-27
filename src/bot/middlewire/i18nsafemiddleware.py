from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from aiogram_i18n.exceptions import KeyNotFoundError
from loguru import logger


class I18nSafeMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler,
            event,
            data

        ):
        try:
            return await handler(event, data)
        except KeyNotFoundError as e:
            locale = {data.get("i18n").locale}
            logger.error(f"Неудача i18n | key: {e} | locale: {locale if locale else 'unklown'}")
            
            chat_id = None
            if hasattr(event, "message"):
                chat_id = event.message.chat.id
            elif hasattr(event, "callback_query"):
                chat_id = event.callback_query.message.chat.id

            if chat_id is not None:
                await event.bot.send_message(
                    chat_id=chat_id,
                    text=f"translate {e} sorry..."
                )
                return
            