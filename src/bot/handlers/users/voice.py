from aiogram import Router, Bot
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message, BufferedInputFile
from dependency_injector.wiring import Provide, inject
from aiogram.enums import ChatAction
from ...containers import Container
from ...services import UserService
from aiogram_i18n import I18nContext, LazyProxy
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n.types import InlineKeyboardButton


router = Router(name=__name__)


@router.message(Command("voice"))
@inject
async def voice(
    message: Message,
    bot: Bot,
    i18n: I18nContext,
    command: CommandObject,
    user_service: UserService = Provide[
        Container.user_service
    ]
):
    args = command.args

    if not args:
        await message.reply(
            text=i18n.get("voice_missing_text")
        )
        return
    
    await message.reply(
        text=i18n.get("voice_waiting")
    )

    await bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.RECORD_VOICE
    )

    voice_buffer = await user_service.edge_voice_generate(
        user_id=message.from_user.id,
        text=args
    )
    

    if not voice_buffer:
        await message.reply(
            text=i18n.get("voice_failed")
        )
        return
    
    await bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.UPLOAD_VOICE
    )

    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text=LazyProxy("voice_send_channel"),
            callback_data="send_voice_channel"
        )
    )

    await message.reply_voice(
        voice=BufferedInputFile(
            file=voice_buffer,
            filename='voice.mp3',
        ),
        reply_markup=kb.as_markup()

    )

