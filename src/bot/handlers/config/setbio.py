from aiogram import Router
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext
from ...containers import Container, UserService

router = Router(name=__name__)

class WaitBio(StatesGroup):
    bio = State()


@router.message(Command("setbio"))
async def set_bio_start(
    message: Message,
    state: FSMContext,
    i18n: I18nContext
) -> None:
    await state.set_state(WaitBio.bio)
    await message.reply(i18n.get("setbio-enter"))


@router.message(WaitBio.bio)
@inject
async def set_bio_save(
    message: Message,
    state: FSMContext,
    i18n: I18nContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    try:
        await user_service.user_repository.update_bio(
            user_id=message.from_user.id,
            bio=message.text
        )
        await message.reply(i18n.get("setbio-saved"))
    except Exception:
        await message.reply(i18n.get("setbio-error"))
    finally:
        await state.clear()
