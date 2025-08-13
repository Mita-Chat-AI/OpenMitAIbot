from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject
from loguru import logger

from ...containers import Container
from ...services import UserService
from aiogram_i18n import I18nContext

router = Router(name=__name__)

@router.message(CommandStart())
@inject
async def start_command_deep_link_false(
    message: Message,
    i18n: I18nContext,
    user_service: UserService = Provide[Container.user_service],
) -> None:
    logger.info(f"Start command received from user_id={message.from_user.id}")
    await user_service.get_data(search_argument=message.from_user.id)
    data = user_service.data
    logger.debug(f"User data fetched: {data}")

    text = i18n.get('hello')
    logger.info(i18n.locale)
    logger.debug(f"Sending message with i18n text: {text}")
    await message.answer(text)
