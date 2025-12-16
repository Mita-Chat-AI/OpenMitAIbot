from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram_i18n import I18nContext
from dependency_injector.wiring import Provide, inject
from typing import Optional

from ...containers import Container
from ...repositories import UserRepository
from ...utils.minimax_voice import create_voice_from_file_id

router = Router(name=__name__)


@router.message(Command("set_minimax_voice"))
@inject
async def set_minimax_voice(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository = Provide[Container.user_repo]
) -> None:
    """Настройка Minimax Voice Clone - простая версия"""
    args = message.text.split()[1:] if message.text else []
    
    if not args:
        await message.answer(
            text="🎤 <b>Настройка Minimax Voice Clone</b>\n\n"
                 "Использование:\n"
                 "/set_minimax_voice <voice_id> [true/false]\n\n"
                 "Параметры:\n"
                 "- voice_id: ID клонированного голоса (обязательно)\n"
                 "- enabled: true/false - включить/выключить (по умолчанию true)\n\n"
                 "Пример:\n"
                 "/set_minimax_voice voice_abc123 true\n\n"
                 "💡 <b>Если у вас есть только file_id:</b>\n"
                 "Используйте команду /get_voice_id <file_id>\n"
                 "Она автоматически создаст голос и получит voice_id.\n\n"
                 "После настройки включите голосовой режим:\n"
                 "/voice_mode\n\n"
                 "И всё! Бот будет автоматически отвечать вашим голосом."
        )
        return
    
    voice_id = args[0]
    
    # Только voice_id и enabled
    enabled_str = args[1].lower() if len(args) > 1 else "true"
    enabled = enabled_str == "true"
    
    # Используем только voice_id, file_id не нужен
    await user_repo.update_minimax_voice(
        user_id=message.from_user.id,
        voice_id=voice_id,
        file_id=None,  # Не нужен, если есть voice_id
        prompt_audio_file_id=None,  # Не нужен, если есть voice_id
        enabled=enabled
    )
    
    response_text = f"✅ <b>Minimax Voice Clone настроен!</b>\n\n" \
                   f"🎤 Voice ID: <code>{voice_id}</code>\n" \
                   f"⚙️ Включен: {'Да' if enabled else 'Нет'}\n\n" \
                   f"💡 <b>Следующий шаг:</b>\n" \
                   f"Включите голосовой режим командой /voice_mode\n" \
                   f"После этого бот будет автоматически отвечать вашим клонированным голосом!"
    
    await message.answer(text=response_text)


@router.message(Command("minimax_voice_info"))
@inject
async def minimax_voice_info(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository = Provide[Container.user_repo]
) -> None:
    """Показывает информацию о настройках Minimax Voice Clone"""
    user = await user_repo.select(user_id=message.from_user.id)
    minimax_voice = user.voice_settings.minimax_voice
    
    # Проверяем статус
    status_icon = "✅" if (minimax_voice.enabled and minimax_voice.voice_id) else "⚠️"
    status_text = "Готов к использованию" if (minimax_voice.enabled and minimax_voice.voice_id) else "Не настроен"
    
    text = f"""🎤 <b>Настройки Minimax Voice Clone</b>

{status_icon} <b>Статус:</b> {status_text}

🆔 Voice ID: {minimax_voice.voice_id or '❌ Не указан'}
🤖 Model: {minimax_voice.model}
⚙️ Включен: {'✅ Да' if minimax_voice.enabled else '❌ Нет'}
🔇 Редукция шума: {'Да' if minimax_voice.need_noise_reduction else 'Нет'}
🔊 Нормализация громкости: {'Да' if minimax_voice.need_volumn_normalization else 'Нет'}

"""
    
    # Добавляем предупреждения если что-то не настроено
    if not minimax_voice.enabled:
        text += "⚠️ <b>Внимание:</b> Minimax Voice отключен!\n"
        text += "Используйте /set_minimax_voice <voice_id> true\n\n"
    elif not minimax_voice.voice_id:
        text += "⚠️ <b>Внимание:</b> Voice ID не настроен!\n"
        text += "Используйте /set_minimax_voice <voice_id> или /get_voice_id <file_id>\n\n"
    
    text += "💡 <b>Команды:</b>\n"
    text += "/set_minimax_voice <voice_id> - настроить голос\n"
    text += "/get_voice_id <file_id> - получить voice_id из file_id\n"
    text += "/voice_mode - включить голосовой режим"
    
    await message.answer(text=text)


@router.message(Command("get_voice_id"))
@inject
async def get_voice_id(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository = Provide[Container.user_repo]
) -> None:
    """Автоматически получает voice_id из file_id"""
    args = message.text.split()[1:] if message.text else []
    
    if not args:
        await message.answer(
            text="🎤 <b>Получение voice_id из file_id</b>\n\n"
                 "Использование:\n"
                 "/get_voice_id <file_id>\n\n"
                 "Пример:\n"
                 "/get_voice_id moss_audio_c58a23ef-d454-11f0-b86f-92cea958fabe\n\n"
                 "Эта команда автоматически создаст голос через Minimax API и получит voice_id.\n"
                 "После получения voice_id он будет автоматически настроен в боте."
        )
        return
    
    file_id = args[0]
    
    # Показываем, что начали процесс
    status_msg = await message.answer("⏳ Создаю голос из file_id... Это может занять несколько секунд.")
    
    try:
        # Получаем voice_id из file_id
        voice_id = await create_voice_from_file_id(
            file_id=file_id,
            prompt_audio_file_id=file_id,  # Используем тот же file_id
            prompt_text="This voice sounds natural and pleasant.",
            model="speech-2.6-hd"
        )
        
        if voice_id:
            # Автоматически настраиваем voice_id в боте (file_id не нужен)
            await user_repo.update_minimax_voice(
                user_id=message.from_user.id,
                voice_id=voice_id,
                file_id=None,  # Не нужен, так как есть voice_id
                prompt_audio_file_id=None,  # Не нужен, так как есть voice_id
                enabled=True
            )
            
            await status_msg.edit_text(
                text=f"✅ <b>Голос успешно создан!</b>\n\n"
                     f"🆔 Voice ID: <code>{voice_id}</code>\n\n"
                     f"✅ Настройки автоматически применены!\n\n"
                     f"💡 <b>Следующий шаг:</b>\n"
                     f"Включите голосовой режим командой /voice_mode\n"
                     f"После этого бот будет автоматически отвечать вашим клонированным голосом!"
            )
        else:
            await status_msg.edit_text(
                text="❌ <b>Не удалось создать голос</b>\n\n"
                     "Возможные причины:\n"
                     "• Неправильный file_id\n"
                     "• Проблемы с API ключом\n"
                     "• Ошибка подключения к Minimax API\n\n"
                     "Проверьте логи бота для подробностей."
            )
    except Exception as e:
        await status_msg.edit_text(
            text=f"❌ <b>Ошибка при создании голоса:</b>\n\n{str(e)}\n\n"
                 "Проверьте логи бота для подробностей."
        )


