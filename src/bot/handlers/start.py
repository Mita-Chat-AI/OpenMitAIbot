from aiogram import Router
from aiogram.types import Message 
from aiogram.filters import CommandStart 
from dependency_injector.wiring import inject, Provide 
from ..containers import Container
from ..db.models import User
from ..services import UserService




router = Router(name=__name__)

@router.message(CommandStart())
@inject
async def start_command_deep_link_false(
    message: Message,
    user_service: UserService = Provide[
        Container.user_service
    ]
):
    await user_service.get_data(
        search_argument=message.from_user.id
    )
    data = user_service.data 
    print(data)

    result_text: str = f"Hello, I'm Bot"
    await message.answer(text=result_text)