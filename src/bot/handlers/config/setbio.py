from aiogram import Router
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject

from ...containers import Container, UserService

router = Router(name=__name__)


@router.message(Command('setbio'))
@inject
async def set_bio(
    message: Message,
    command: CommandObject,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    
    arg = command.args

    if not arg:
        await message.reply('ты ничего не указал')
        return
    
    await user_service.user_repository.update_bio(
        user_id=message.from_user.id,
        bio=arg
    )

    await message.reply('твое био было записано')