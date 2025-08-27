

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction, ChatType, ContentType
from aiogram.types import BufferedInputFile, Message
from aiogram_i18n import I18nContext
from dependency_injector.wiring import Provide, inject
from openai import APIConnectionError

from ...containers import Container
from ...services import UserService

router = Router(name=__name__)

@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.content_type.in_([ContentType.TEXT]),
    ~F.text.startswith("/")
)
@inject
async def mita_handler(
    message: Message,
    bot: Bot,
    i18n: I18nContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> Message:

    await bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )

    try:
        msg = await user_service.ask_ai(
            user_id=message.from_user.id,
            text=message.text
        )
    except APIConnectionError:
        await message.reply(
            text=i18n.get('mita-no-response')
        )
        return

    if not msg:
        await message.reply(
            text=i18n.get('mita-no-response')
        )
        return msg

    user = await user_service.get_data(
        message.from_user.id
    )

    if user.settings.voice_mode:
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.RECORD_VOICE
        )
        voice_buffer = await user_service.edge_voice_generate(
            user_id=message.from_user.id,
            text=msg
        )

        result = await message.reply_voice(
            voice=BufferedInputFile(
                file=voice_buffer,
                filename='voice.mp3'
            )
        )
        return result

    result = await message.reply(text=msg)
    return result






