from typing import Optional

from ..db.models import User
from ..exeptions import SelectError


class UserRepository:
    async def upsert(
        self,
        user_id: int,
    ) -> User:
        from ...settings.main import config
        
        user = await User.find_one(User.user_id == user_id)

        if not user:
            user = User(user_id=user_id)
            # Автоматически настраиваем Minimax Voice для нового пользователя
            if config.voice_config.minimax_voice_enabled:
                user.voice_settings.minimax_voice.enabled = True
                # Автоматически подставляем voice_id из конфига, если указан
                if config.voice_config.minimax_voice_id:
                    user.voice_settings.minimax_voice.voice_id = config.voice_config.minimax_voice_id
            # Автоматически включаем voice_mode для нового пользователя
            if config.voice_config.voice_mode_enabled:
                user.settings.voice_mode = True
            await user.insert()

        return user

    async def select(
        self,
        user_id: Optional[int] = None,
        id: Optional[str] = None,
    ) -> Optional[User]:

        if user_id:
            user = await self.upsert(user_id)
        elif id:
            user = await User.get(id)
            if not user:
                raise SelectError(f"Пользователь с id={id} не найден")
        else:
            raise SelectError("Не был передан ни один аргумент")

        return user

    async def get_all_users(self) -> list[str]:
        users = User.find_all()
        return await users.to_list()

    async def update_bio(
        self,
        user_id: int,
        bio: str
    ) -> None:
        user = await self.upsert(user_id=user_id)
        user.settings.player_prompt = bio
        await user.save()

    
    async def get_bio(
            self,
            user_id: int
    ) -> str:
        user: User = await self.upsert(
            user_id=user_id
        )
        if user.settings.player_prompt:
            return user.settings.player_prompt
        return ""


    async def update_ban(
        self,
        user_id: int,
        ban: str
    ) -> Optional[User]:
        user = await self.upsert(user_id)
        user.settings.is_blocked = ban
        await user.save()
        return user

    async def update_voicemod(
        self,
        user_id: int,
        mode: str
    ) -> Optional[User]:
        user = await self.upsert(user_id)
        user.settings.voice_mode = mode
        await user.save()
        return user

    async def update_locale(
        self,
        user_id: int,
        locale: str
    ) -> Optional[User]:
        user = await self.upsert(user_id)
        user.settings.locale = locale
        await user.save()
        return user

    # async def update_message_history(
    #     self,
    #     user_id: int,
    #     human: str,
    #     ai: str
    # ) -> None:
    #     user = await self.upsert(user_id)

    #     def to_message(type_, content):
    #         return TypeMessage(type=type_, content=content)

    #     user.user_history.messages.extend([
    #         to_message("human", human),
    #         to_message("ai", ai)
    #     ])
    #     await user.save()

    async def clear_history(
        self,
        user_id: int
    ) -> None:
        user = await self.upsert(user_id)


    async def get_history(
        self,
        user_id: int
    ) -> list[dict]:
        user = await self.upsert(user_id)
        if user.user_history:
            return [{"type": m.type, "content": m.content} for m in user.user_history.messages]
        else:
            return [{}]

    async def update_subscription(
        self,
        user_id: int,
        subscription_type: int,
        tokens: int,
        expires_days: int = 7,
        phone_number: Optional[str] = None
    ) -> None:
        """Обновляет подписку пользователя"""
        from datetime import datetime, timedelta
        from ...db.models import Subscription
        
        user = await self.upsert(user_id)
        
        user.settings.subscription.type = subscription_type
        user.settings.subscription.tokens = tokens
        user.settings.subscription.expires_at = datetime.now() + timedelta(days=expires_days)
        user.settings.subscription.created_at = datetime.now()
        
        if phone_number:
            user.settings.subscription.phone_number = phone_number
        
        await user.save()

    async def update_phone_number(
        self,
        user_id: int,
        phone_number: str
    ) -> None:
        """Обновляет номер телефона пользователя"""
        user = await self.upsert(user_id)
        user.settings.subscription.phone_number = phone_number
        await user.save()

    async def get_subscription_info(
        self,
        user_id: int
    ) -> dict:
        """Возвращает информацию о подписке пользователя"""
        user = await self.upsert(user_id)
        sub = user.settings.subscription
        
        return {
            "type": sub.type,
            "tokens": sub.tokens,
            "expires_at": sub.expires_at,
            "phone_number": sub.phone_number,
            "min_request_interval": user.settings.min_request_interval
        }

    async def update_minimax_voice(
        self,
        user_id: int,
        voice_id: Optional[str] = None,
        file_id: Optional[str] = None,
        prompt_audio_file_id: Optional[str] = None,
        prompt_text: Optional[str] = None,
        model: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> None:
        """Обновляет настройки Minimax Voice Clone для пользователя"""
        user = await self.upsert(user_id)
        minimax_voice = user.voice_settings.minimax_voice
        
        if voice_id is not None:
            # Используем единую функцию очистки (убирает HTML-теги, кавычки, пробелы)
            from ...utils.minimax_voice import validate_and_clean_voice_id
            cleaned_voice_id = validate_and_clean_voice_id(voice_id)
            if cleaned_voice_id:
                minimax_voice.voice_id = cleaned_voice_id
            else:
                # Если не удалось очистить - сохраняем как есть (но с предупреждением)
                # validate_and_clean_voice_id уже залогировал ошибку
                minimax_voice.voice_id = voice_id.strip()  # Хотя бы пробелы уберем
        # file_id и prompt_audio_file_id больше не используются - только voice_id
        if prompt_text is not None:
            minimax_voice.prompt_text = prompt_text
        if model is not None:
            minimax_voice.model = model
        if enabled is not None:
            minimax_voice.enabled = enabled
        
        await user.save()