from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dependency_injector.wiring import Provide, inject

from ...containers import Container, UserService


class WaitVoiceMod(StatesGroup):
    wait_voice_mod = State()


router = Router(name=__name__)


@router.message(Command('voice_mode'))
@inject
async def config_voice_mode(
    message: Message,
    state: FSMContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(
            text="Включить VoiceMod",
            callback_data='on:voice_mod'
        )
    )
    
    kb.add(
        InlineKeyboardButton(
            text="Выключить VoiceMod",
            callback_data='off:voice_mod'
        )
    )
    kb.adjust()
    
    await state.set_state(WaitVoiceMod.wait_voice_mod)
    
    await message.reply(
        text="Выбиретие режим для войс мод:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(StateFilter(WaitVoiceMod.wait_voice_mod))
@inject
async def process_voice_mode(
    callback: CallbackQuery,
    state: FSMContext,
    user_service: UserService = Provide[Container.user_service]
):
    action, _ = callback.data.split(":")

    if action == "on":
        await user_service.user_repository.update_voicemod(callback.from_user.id, True)
        await callback.message.edit_text("✅ VoiceMod включён")
    elif action == "off":
        await user_service.user_repository.update_voicemod(callback.from_user.id, False)
        await callback.message.edit_text("❌ VoiceMod выключен")

    await state.clear()
    await callback.answer()
