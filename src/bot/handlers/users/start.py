from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_i18n import I18nContext
from dependency_injector.wiring import Provide, inject

from ...containers import Container
from ...db.models import User
from ...services import UserService

router = Router(name=__name__)


@router.message(CommandStart())
@inject
async def start_command_deep_link_false(
    message: Message,
    i18n: I18nContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    await user_service.get_data(
        search_argument=message.from_user.id
    )

    await message.answer(
        text=i18n.get('hello')
    )
