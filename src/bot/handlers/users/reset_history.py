from aiogram import Router
from aiogram.filters.command import Command
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject
from aiogram_i18n import I18nContext
from ...containers import Container
from ...services import UserService

router = Router(name=__name__)

@router.message(Command('reset'))
@inject
async def reset_history(
    message: Message,
    i18n: I18nContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None: 
    await user_service.user_repository.clear_history(
        user_id=message.from_user.id
    )

    await message.reply(
        text=i18n.get('reset_history-reset')
    )

