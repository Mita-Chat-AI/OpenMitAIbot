from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.filters.command import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram_i18n.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dependency_injector.wiring import Provide, inject

from aiogram_i18n import LazyProxy, I18nContext

from ...containers import Container, UserService


class WaitVoiceMod(StatesGroup):
    wait_voice_mod = State()


router = Router(name=__name__)


@router.message(Command('voice_mode'))
async def config_voice_mode(
    message: Message,
    state: FSMContext,
    i18n: I18nContext,
) -> None:
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(
            text=LazyProxy("voice_mode-enable-btn"),
            callback_data='on:voice_mod',
        )
    )
    
    kb.add(
        InlineKeyboardButton(
            text=LazyProxy("voice_mode-disable-btn"),
            callback_data='off:voice_mod',
        )
    )
    kb.adjust()
    
    await state.set_state(WaitVoiceMod.wait_voice_mod)
    
    await message.reply(
        text=i18n.get("voice_mode-choose"),
        reply_markup=kb.as_markup()
    )


@router.callback_query(StateFilter(WaitVoiceMod.wait_voice_mod))
@inject
async def process_voice_mode(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    action, _ = callback.data.split(":")

    if action == "on":
        await user_service.user_repository.update_voicemod(
            user_id=callback.from_user.id,
            mode=True,
        )
        await callback.message.edit_text(
            text=i18n.get("voice_mode-enabled")
        )

    elif action == "off":
        await user_service.user_repository.update_voicemod(
            user_id=callback.from_user.id,
            mode=False,
        )
        await callback.message.edit_text(
            text=i18n.get("voice_mode-disabled")
        )

    await state.clear()
    await callback.answer()
