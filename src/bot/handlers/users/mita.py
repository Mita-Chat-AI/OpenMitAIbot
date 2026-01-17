

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction, ChatType, ContentType
from aiogram.types import BufferedInputFile, Message
from aiogram_i18n import I18nContext
from dependency_injector.wiring import Provide, inject
from loguru import logger
from openai import APIConnectionError
from typing import Optional
from ...containers import Container
from ...services import UserService

router = Router(name=__name__)

@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.content_type.in_([ContentType.TEXT]),
    ~F.text.startswith("/")
)
@inject
async def mita_handler(
    message: Message,
    bot: Bot,
    i18n: I18nContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> Optional[Message] | None:
    
    logger.info(f"Получено сообщение от {message.from_user.id}: {message.text}")

    await bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )

    try:
        logger.info("Отправляю запрос к AI...")
        msg = await user_service.ask_ai(
            user_id=message.from_user.id,
            text=message.text
        )
        logger.info(f"Получен ответ от AI: {msg[:50] if msg else 'None'}...")
    except ValueError as e:
        logger.warning(f"Ошибка проверки токенов/времени: {e}")
        await message.reply(text=str(e))
        return None
    except APIConnectionError as e:
        logger.error(f"Ошибка подключения к AI API: {e}")
        await message.reply(
            text=i18n.get('mita-connection-error')
        )
        return None
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg:
            await message.reply(
                text=i18n.get('mita-connection-error')
            )
        else:
            await message.reply(
                text=i18n.get('mita-no-response')
            )
        return None

    if not msg:
        await message.reply(
            text=i18n.get('mita-no-response')
        )
        return msg

    user = await user_service.get_data(
        search_argument=message.from_user.id
    )
    
    from ....settings.main import config
    if config.voice_config.voice_mode_enabled and not user.settings.voice_mode:
        user.settings.voice_mode = True
        await user.save()
        logger.info(f"Автоматически включен voice_mode для пользователя {message.from_user.id}")

    if user.settings.voice_mode:
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.RECORD_VOICE
        )
        try:
            voice_buffer = await user_service.edge_voice_generate(
                user_id=message.from_user.id,
                text=msg
            )
            
            if not voice_buffer:
                logger.error("Не удалось сгенерировать голосовое сообщение")
                # Fallback: отправляем текстом
                result = await message.reply(text=msg)
                return result
            
            logger.info(f"Голосовое сообщение сгенерировано: {len(voice_buffer)} байт")
            
            result = await message.reply_voice(
                voice=BufferedInputFile(
                    file=voice_buffer,
                    filename='voice.ogg'
                )
            )
            logger.info("Голосовое сообщение отправлено успешно")
            return result
        except Exception as e:
            logger.error(f"Ошибка при отправке голосового сообщения: {e}")
            # Fallback: отправляем текстом
            result = await message.reply(text=msg)
            return result

    result = await message.reply(
        text=msg
    )
    return result






