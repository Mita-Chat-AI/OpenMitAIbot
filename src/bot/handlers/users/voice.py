from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext, LazyProxy
from aiogram_i18n.types import InlineKeyboardButton
from dependency_injector.wiring import Provide, inject

from ...containers import Container
from ...services import UserService

router = Router(name=__name__)

class SendVoiceChannel(StatesGroup):
    wait_send_voice_channel = State()


@router.message(StateFilter(None), Command("voice"))
@inject
async def voice(
    message: Message,
    bot: Bot,
    i18n: I18nContext,
    command: CommandObject,
    state: FSMContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
):
    args = command.args

    if not args:
        await message.reply(
            text=i18n.get("voice_missing_text")
        )
        return
    
    msg = await message.reply(
        text=i18n.get("voice_waiting")
    )

    await bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.RECORD_VOICE
    )

    voice_buffer = await user_service.edge_voice_generate(
        user_id=message.from_user.id,
        text=args
    )
    

    if not voice_buffer:
        await message.reply(
            text=i18n.get("voice_failed")
        )
        return
    
    await bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.UPLOAD_VOICE
    )
    await msg.delete()

    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text=LazyProxy("voice_send_channel"),
            callback_data="send_voice_channel"
        )
    )

    await message.reply_voice(
        voice=BufferedInputFile(
            file=voice_buffer,
            filename='voice.mp3',
        ),
        reply_markup=kb.as_markup()

    )
    await state.set_state(SendVoiceChannel.wait_send_voice_channel)
    await state.update_data(user_id=message.from_user.id, voice_buffer=voice_buffer, text=args)


@router.callback_query(
    SendVoiceChannel.wait_send_voice_channel,
    F.data == 'send_voice_channel'
)
async def send_voice_channel(
    call: CallbackQuery,
    bot: Bot,
    state: FSMContext
) -> None:
    state_data = await state.get_data()
    voice_data = state_data.get("voice_buffer")
    text = state_data.get("text")

    try:
        channel_id = -1002326238712

        chat_info = await bot.get_chat(channel_id)
        channel_username = chat_info.username

        msg = await bot.send_voice(
            chat_id=channel_id,
            voice=BufferedInputFile(voice_data, filename="voice.ogg"),
            caption=text
        )

        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text="Посмотреть в канале",
                url=f"https://t.me/{channel_username}/{msg.message_id}"
            )
        )

        await call.message.reply(
            text="Ваше голосовое, было отправлено в канал: в нем, вы можете общаться, или присылать смешные голосовые.",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
    except Exception as e:
        await call.message.reply(text=f"ну не смог отправить: {e}")

    await state.clear()
