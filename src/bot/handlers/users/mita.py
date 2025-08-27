

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction, ChatType, ContentType
from aiogram.types import BufferedInputFile, Message
from dependency_injector.wiring import Provide, inject

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
    user_service: UserService = Provide[
        Container.user_service
    ]) -> Message:

    await bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )

    msg = await user_service.ask_ai(
        user_id=message.from_user.id,
        text=message.text
    )
    if not msg:
        await message.reply(
            text="К сожалению, Мита ничего не вернула в ответ"
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






