

from aiogram import F, Router
from aiogram.enums import ChatType, ContentType
from aiogram.types import Message
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
    user_service: UserService = Provide[
        Container.user_service
    ]) -> None:

    msg = await user_service.ask_ai(
        user_id=message.from_user.id,
        text=message.text
    )

    print(msg)

    if not msg:
        await message.reply(
            text="К сожалению, Мита ничего не вернула в ответ"
        )
        return msg

    result = await message.reply(text=msg)
    return result
    





