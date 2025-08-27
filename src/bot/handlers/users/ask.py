import time

from aiogram import Bot, F, Router
from aiogram.enums.chat_type import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram_i18n import I18nContext

from .mita import mita_handler

ask_router = Router()

memory_time = {}
last_bot_message = {}


@ask_router.message(
        Command("ask"),
        F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def ask(
    message: Message,
    bot: Bot,
    i18n: I18nContext,
    command: CommandObject
) -> None:
    args = command.args
    if not args:
        await message.reply(
            text=i18n.get('ask-wait-question')
        )
        return

    msg = await message.reply(text=i18n.get("ask-waiting-for-message"))
    user_id = message.from_user.id

    bot_response: Message | None = await mita_handler(message, bot, i18n)
    await msg.delete()

    if bot_response and bot_response.message_id:
        last_bot_message[user_id] = bot_response.message_id
        memory_time[user_id] = time.time()


@ask_router.message(
        F.reply_to_message,
        F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def handle_reply_to_bot(
    message: Message,
    bot: Bot,
    i18n: I18nContext
) -> None:
    user_id = message.from_user.id

    if user_id in last_bot_message and message.reply_to_message.message_id == last_bot_message[user_id]:
        bot_response = await mita_handler(message, bot, i18n)
        last_bot_message[user_id] = bot_response.message_id