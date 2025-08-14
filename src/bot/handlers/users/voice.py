from aiogram import Router, Bot
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message, BufferedInputFile
from dependency_injector.wiring import Provide, inject
from aiogram.enums import ChatAction
from ...containers import Container
import requests
from ...services import UserService
router = Router(name=__name__)




@router.message(Command("voice"))
@inject
async def voice(
    message: Message,
    bot: Bot,
    command: CommandObject,
    user_service: UserService = Provide[
        Container.user_service
    ]
):
    args = command.args

    if not args:
        await message.reply(
            text="Не правильно. Нужно /voice текст"
        )
        return
    
    await message.reply("Ждем гс. генерирую")

    await bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.RECORD_VOICE
    )

    voice_buffer = await user_service.edge_voice_generate(
        user_id=message.from_user.id,
        text=args
    )
    


    if not voice_buffer:
        await message.reply("Не удалось сгенерировать голосовое.")
        return

    await message.reply_voice(
        voice=BufferedInputFile(
            file=voice_buffer,
            filename='voice.mp3'
        )
    )

