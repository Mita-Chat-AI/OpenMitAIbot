from aiogram import Router
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject
from aiogram_i18n import I18nContext

from ...containers import Container, UserService

router = Router(name=__name__)

@router.message(Command("setbio"))
@inject
async def set_bio(
    message: Message,
    command: CommandObject,
    i18n: I18nContext,
    user_service: UserService = Provide[Container.user_service]
) -> None:
    bio_text = command.args
    if not bio_text:
        await message.reply(i18n.get("setbio-enter"))
        return

    try:
        await user_service.user_repository.update_bio(
            user_id=message.from_user.id,
            bio=bio_text
        )
        await message.reply(i18n.get("setbio-saved"))
    except Exception:
        await message.reply(i18n.get("setbio-error"))
