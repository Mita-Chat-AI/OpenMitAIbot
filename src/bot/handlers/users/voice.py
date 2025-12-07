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


@router.message(Command("voice"))
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
) -> None:
    args = command.args

    if not args:
        await message.reply(
            text=i18n.get("voice-missing-text")
        )
        return

    msg = await message.reply(
        text=i18n.get("voice-waiting")
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
            text=i18n.get("voice-failed-voice-buffer")
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
            text=LazyProxy("voice-send-channel"),
            callback_data="send_voice_channel"
        )
    )

    await message.reply_voice(
        voice=BufferedInputFile(
            file=voice_buffer,
            filename='voice.ogg',  # OGG формат после обработки
        ),
        reply_markup=kb.as_markup()
    )

    await state.set_state(
        SendVoiceChannel.wait_send_voice_channel
    )
    await state.update_data(
        user_id=message.from_user.id,
        voice_buffer=voice_buffer,
        text=args
    )


@router.callback_query(
    SendVoiceChannel.wait_send_voice_channel,
    F.data == 'send_voice_channel'
)
@inject
async def send_voice_channel(
    call: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    i18n: I18nContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    state_data = await state.get_data()
    voice_data = state_data.get("voice_buffer")
    text = state_data.get("text")

    try:
        channel_id = user_service.config.telegram.channel_id

        chat_info = await bot.get_chat(
            chat_id=channel_id
        )
        channel_username = chat_info.username

        msg = await bot.send_voice(
            chat_id=channel_id,
            voice=BufferedInputFile(voice_data, filename="voice.ogg"),  # OGG формат
            caption=f"{text}\n{call.from_user.mention_html()}"
        )

        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text=i18n.get('voice-watch-to-channel'),
                url=f"https://t.me/{channel_username}/{msg.message_id}"
            )
        )

        await call.message.reply(
            text=i18n.get('voice-succeful-channel'),
            reply_markup=builder.as_markup(resize_keyboard=True)
        )

    except Exception as e:
        await call.message.reply(
            text=i18n.get(
                'voice-error-send-channel',
                e=str(e)
            )
        )

    await state.clear()
