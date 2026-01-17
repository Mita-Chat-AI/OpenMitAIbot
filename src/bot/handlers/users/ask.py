import time

from aiogram import Bot, F, Router
from aiogram.enums.chat_type import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram_i18n import I18nContext

from .mita import mita_handler

from ...containers import Container
from ...services import UserService
from dependency_injector.wiring import Provide, inject

ask_router = Router()


@ask_router.message(
        Command("ask"),
        F.chat.type.in_(
            [
                ChatType.GROUP,
                ChatType.SUPERGROUP
            ]
        )
)
@inject
async def ask(
    message: Message,
    bot: Bot,
    i18n: I18nContext,
    command: CommandObject,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    args = command.args
    if not args:
        await message.reply(
            text=i18n.get('ask-wait-question')
        )
        return

    msg = await message.reply(
        text=i18n.get("ask-waiting-for-message")
    )
    user_id = message.from_user.id

    bot_response: Message | None = await mita_handler(
        message=message,
        bot=bot,
        i18n=i18n
    )
    await msg.delete()

    if bot_response:
        await user_service.user_repository.update_last_bot_message(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            message_id=bot_response.message_id
        )

        await user_service.user_repository.update_memory_time(
            user_id=message.from_user.id,
            chat_id=message.chat.id
        )
@ask_router.message(
    F.reply_to_message,
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
@inject
async def handle_reply_to_bot(
    message: Message,
    bot: Bot,
    i18n: I18nContext,
    user_service: UserService = Provide[Container.user_service]
) -> None:

    user = await user_service.get_data(message.from_user.id)
    chat_id = str(message.chat.id)

    last_msg_id = user.messages.last_bot_message.get(chat_id)
    if not last_msg_id:
        return

    if message.reply_to_message.message_id != last_msg_id:
        return

    bot_response = await mita_handler(
        message=message,
        bot=bot,
        i18n=i18n
    )

    if not bot_response:
        return

    await user_service.user_repository.update_last_bot_message(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        message_id=bot_response.message_id
    )

    await user_service.user_repository.update_memory_time(
        user_id=message.from_user.id,
        chat_id=message.chat.id
    )
