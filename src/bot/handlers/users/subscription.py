from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from dependency_injector.wiring import Provide, inject
from datetime import datetime

from ...containers import Container
from ...services import UserService
from ...repositories import UserRepository
from ....settings import config

router = Router(name=__name__)


@router.message(Command("subscription", "sub"))
@inject
async def subscription_info(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository = Provide[Container.user_repo]
) -> None:
    """Показывает информацию о текущей подписке"""
    user_id = message.from_user.id
    sub_info = await user_repo.get_subscription_info(user_id)
    
    sub_type_names = {
        0: "Нет подписки",
        1: "Недельная подписка",
        2: "Месячная подписка"
    }
    
    sub_type = sub_type_names.get(sub_info["type"], "Неизвестно")
    tokens = sub_info["tokens"]
    expires_at = sub_info["expires_at"]
    phone = sub_info["phone_number"] or "Не указан"
    min_interval = sub_info["min_request_interval"]
    
    if expires_at:
        expires_str = expires_at.strftime("%d.%m.%Y %H:%M")
        time_left = expires_at - datetime.now()
        if time_left.total_seconds() > 0:
            days_left = time_left.days
            hours_left = time_left.seconds // 3600
            time_left_str = f"{days_left} дн. {hours_left} ч."
        else:
            time_left_str = "Истекла"
    else:
        expires_str = "Не указана"
        time_left_str = "-"
    
    text = f"""💎 <b>Информация о подписке</b>

📋 Тип: {sub_type}
🪙 Токены: {tokens}
⏰ Истекает: {expires_str}
⏱ Осталось: {time_left_str}
📱 Телефон: {phone}
⚡ Минимальный интервал: {min_interval} сек.

💡 Для оформления подписки используй команду /buy_subscription"""
    
    await message.answer(text=text)


@router.message(Command("buy_subscription", "buy"))
async def buy_subscription(
    message: Message,
    i18n: I18nContext
) -> None:
    """Показывает варианты подписок"""
    weekly_tokens = config.ai_config.subscription_weekly_tokens
    monthly_tokens = config.ai_config.subscription_monthly_tokens
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"📅 Неделя - {weekly_tokens} токенов (~50₽)",
                callback_data="sub_weekly"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📆 Месяц - {monthly_tokens} токенов (~200₽)",
                callback_data="sub_monthly"
            )
        ],
        [
            InlineKeyboardButton(
                text="📱 Указать номер телефона",
                callback_data="sub_phone"
            )
        ]
    ])
    
    text = """💎 <b>Оформление подписки</b>

Выбери тип подписки:
📅 <b>Недельная</b> - {weekly_tokens} токенов (~50₽)
   Достаточно для ~{weekly_hours} часов общения

📆 <b>Месячная</b> - {monthly_tokens} токенов (~200₽)
   Достаточно для ~{monthly_hours} часов общения

💡 После оплаты используй команду /activate_subscription <номер_телефона> <тип>
   Тип: 1 - неделя, 2 - месяц

📱 <b>Важно:</b> Укажи номер телефона для активации подписки!""".format(
        weekly_tokens=weekly_tokens,
        weekly_hours=weekly_tokens // config.ai_config.tokens_per_request,
        monthly_tokens=monthly_tokens,
        monthly_hours=monthly_tokens // config.ai_config.tokens_per_request
    )
    
    await message.answer(text=text, reply_markup=keyboard)


@router.message(Command("activate_subscription", "activate"))
@inject
async def activate_subscription(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository = Provide[Container.user_repo]
) -> None:
    """Активирует подписку по номеру телефона"""
    args = message.text.split()[1:] if message.text else []
    
    if len(args) < 2:
        await message.answer(
            text="❌ Используй: /activate_subscription <номер_телефона> <тип>\n"
                 "Тип: 1 - неделя, 2 - месяц\n"
                 "Пример: /activate_subscription +79991234567 1"
        )
        return
    
    phone_number = args[0]
    try:
        sub_type = int(args[1])
        if sub_type not in [1, 2]:
            await message.answer("❌ Тип подписки должен быть 1 (неделя) или 2 (месяц)")
            return
    except ValueError:
        await message.answer("❌ Тип подписки должен быть числом (1 или 2)")
        return
    
    # Определяем количество токенов и дней
    if sub_type == 1:
        tokens = config.ai_config.subscription_weekly_tokens
        days = 7
    else:
        tokens = config.ai_config.subscription_monthly_tokens
        days = 30
    
    # Активируем подписку
    await user_repo.update_subscription(
        user_id=message.from_user.id,
        subscription_type=sub_type,
        tokens=tokens,
        expires_days=days,
        phone_number=phone_number
    )
    
    await message.answer(
        text=f"✅ <b>Подписка активирована!</b>\n\n"
             f"📋 Тип: {'Недельная' if sub_type == 1 else 'Месячная'}\n"
             f"🪙 Токены: {tokens}\n"
             f"📱 Телефон: {phone_number}\n"
             f"⏰ Действует: {days} дней\n\n"
             f"Теперь ты можешь общаться со мной! 💕"
    )


@router.callback_query(F.data.startswith("sub_"))
@inject
async def subscription_callback(
    callback: CallbackQuery,
    i18n: I18nContext,
    user_repo: UserRepository = Provide[Container.user_repo]
) -> None:
    """Обработка callback для подписок"""
    action = callback.data
    
    if action == "sub_phone":
        await callback.message.answer(
            text="📱 <b>Укажи номер телефона</b>\n\n"
                 "Используй команду:\n"
                 "/set_phone <номер>\n\n"
                 "Пример: /set_phone +79991234567"
        )
        await callback.answer()
        return
    
    await callback.answer("💡 Используй команду /activate_subscription для активации подписки")


@router.message(Command("set_phone"))
@inject
async def set_phone(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository = Provide[Container.user_repo]
) -> None:
    """Устанавливает номер телефона пользователя"""
    args = message.text.split()[1:] if message.text else []
    
    if not args:
        await message.answer(
            text="❌ Используй: /set_phone <номер_телефона>\n"
                 "Пример: /set_phone +79991234567"
        )
        return
    
    phone_number = " ".join(args)
    await user_repo.update_phone_number(
        user_id=message.from_user.id,
        phone_number=phone_number
    )
    
    await message.answer(
        text=f"✅ <b>Номер телефона сохранен!</b>\n\n"
             f"📱 {phone_number}\n\n"
             f"Теперь ты можешь активировать подписку командой /activate_subscription"
    )

