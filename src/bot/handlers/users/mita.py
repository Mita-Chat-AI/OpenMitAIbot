from aiogram import F, Router
from aiogram.enums import ChatType, ContentType
from aiogram.types import Message

router = Router(name=__name__)

@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.content_type.in_([ContentType.TEXT]),
    ~F.text.startswith("/")
)
async def mita_handler(message: Message) -> None:
    await message.reply("Я Мита, как дела?")
