import html
import warnings
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional, Union

# Подавляем предупреждение о ffmpeg/avconv от pydub ДО импорта
warnings.filterwarnings("ignore", message=".*Couldn't find ffmpeg or avconv.*", category=RuntimeWarning)

import aiohttp
import numpy as np
import soundfile as sf
from aiogram.types.chat_member_updated import ChatMemberUpdated
from aiogram.types.user import User as TelegramUser
from aiogram_i18n.managers import BaseManager
from openai import APIConnectionError
from pedalboard import Pedalboard, Reverb

from ....settings import Config, config
from ...db.models import User
from ...repositories import UserRepository
from ..model_services.ai_service import AiService
from ..service import Service


class UserService(Service):
    data: User | None

    def __init__(
            self,
            user_repository: UserRepository,
            ai_service: AiService
    ) -> None:
        super().__init__()
        self.user_repository = user_repository
        self.ai_service = ai_service
        self.data = None
        self.config = self.get_env()

    async def get_data(
        self,
        search_argument: Union[str, int]
    ) -> User:
        user: User | None = None

        if search_argument >= 777000:
            user = await self.user_repository.select(user_id=search_argument)

        else:
            user = await self.user_repository.select(id=search_argument)

        if not user and isinstance(search_argument, int):
            user = await self.user_repository.upsert(
                user_id=search_argument,
            )

        self.data = user
        return user

    async def check_tokens_and_time(
            self,
            user: User
    ) -> tuple[bool, Optional[str]]:
        """
        Проверяет наличие токенов и минимальное время между запросами.
        Возвращает (можно_отправить, сообщение_об_ошибке)
        """
        now = datetime.now()
        
        # Проверка минимального времени между запросами
        if user.settings.last_request_time:
            time_diff = (now - user.settings.last_request_time).total_seconds()
            min_interval = user.settings.min_request_interval
            
            if time_diff < min_interval:
                remaining = min_interval - time_diff
                return False, f"⏳ Подожди еще {remaining:.1f} секунд перед следующим запросом..."
        
        # ПРОВЕРКА ПОДПИСОК ОТКЛЮЧЕНА
        # Все пользователи могут использовать бота без ограничений
        
        # # Проверка подписки и токенов
        # subscription = user.settings.subscription
        # 
        # # Если подписка истекла, сбрасываем её
        # if subscription.expires_at and subscription.expires_at < now:
        #     subscription.type = 0
        #     subscription.tokens = 0
        #     subscription.expires_at = None
        #     await user.save()
        #     return False, "💔 Твоя подписка истекла. Оформи новую подписку, чтобы продолжить общение!"
        # 
        # # Если нет активной подписки
        # if subscription.type == 0 or subscription.tokens <= 0:
        #     return False, "💎 У тебя нет активной подписки или закончились токены. Оформи подписку, чтобы общаться со мной!"
        # 
        # # Проверяем, достаточно ли токенов для запроса
        # tokens_needed = config.ai_config.tokens_per_request
        # if subscription.tokens < tokens_needed:
        #     return False, f"💎 У тебя недостаточно токенов. Нужно {tokens_needed}, осталось {subscription.tokens}."
        
        return True, None
    
    async def consume_tokens(
            self,
            user: User,
            tokens_used: Optional[int] = None
    ) -> None:
        """Списывает токены после запроса (ОТКЛЮЧЕНО)"""
        # СПИСАНИЕ ТОКЕНОВ ОТКЛЮЧЕНО
        # Токены больше не списываются, все пользователи могут использовать бота без ограничений
        
        # if tokens_used is None:
        #     tokens_used = config.ai_config.tokens_per_request
        # 
        # subscription = user.settings.subscription
        # subscription.tokens = max(0, subscription.tokens - tokens_used)
        
        # Обновляем время последнего запроса
        user.settings.last_request_time = datetime.now()
        
        await user.save()
        # self.logger.info(f"Списано {tokens_used} токенов у пользователя {user.user_id}. Осталось: {subscription.tokens}")

    async def ask_ai(
            self,
            user_id: int,
            text: str
    ) -> str:
        try:
            user = await self.get_data(user_id)
            
            # Проверяем токены и время
            can_proceed, error_msg = await self.check_tokens_and_time(user)
            if not can_proceed:
                raise ValueError(error_msg)

            ai_response = await self.ai_service.generate_response(
                user_id=user_id,
                session_id=user_id,
                text=text,
                player_prompt=user.settings.player_prompt if user.settings.player_prompt else None
                )

            if not ai_response or not hasattr(ai_response, 'content'):
                self.logger.warning(f"AI вернул пустой ответ для пользователя {user_id}")
                return None
            
            # Списываем токены после успешного запроса
            await self.consume_tokens(user)
                
            return ai_response.content
        except ValueError as e:
            # Это ошибка проверки токенов/времени - пробрасываем дальше
            raise
        except Exception as e:
            self.logger.error(f"Ошибка при запросе к AI для пользователя {user_id}: {e}")
            raise
    
    def get_env(self) -> Config:
        return config

    async def return_all_user_ids(self) -> list[str]:
        return [doc.user_id for doc in await self.user_repository.get_all_users()]

    async def edge_voice_generate(
            self, user_id: int,
            text: str
    ) -> bytes:
        """
        Генерирует голосовое сообщение.
        
        Использует Edge TTS (библиотека или внешний API).
        """
        self.logger.info(f"Попытка записи голосового сообщения для {user_id} : {text}")

        user = await self.get_data(search_argument=user_id)
        
        # Используем Edge TTS
        # Получаем настройки голоса
        voice_person = user.voice_settings.edge_tts.person or "CrazyMita"
        voice_rate = user.voice_settings.edge_tts.rate or "+10%"
        voice_pitch_int = user.voice_settings.edge_tts.pith or 8
        
        # Конвертируем настройки в формат Edge TTS
        voice = map_person_to_voice(voice_person)
        rate = voice_rate
        pitch = map_pitch_int_to_hz(voice_pitch_int)
        
        self.logger.debug(f"Голос: {voice}, rate: {rate}, pitch: {pitch}")

        try:
            voice_bytes = await generate_edge_tts(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch
            )
            if voice_bytes:
                self.logger.success(f"✅ Edge TTS (библиотека): {len(voice_bytes)} байт")
        except Exception as e:
            self.logger.warning(f"Edge TTS библиотека недоступна: {e}, пробуем API...")
            voice_bytes = None
        
        # Fallback: пробуем внешний API если библиотека не работает
        if not voice_bytes:
            edge_tts_secret = self.config.voice_config.edge_tts
            edge_tts_url = edge_tts_secret.get_secret_value() if edge_tts_secret else None
            if edge_tts_url and edge_tts_url != "" and edge_tts_url != "your_edge_tts_api_url":
                try:
                    self.logger.info(f"Пробуем Edge TTS через внешний API: {edge_tts_url}")
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            url=edge_tts_url,
                            json={
                                "text": text,
                                "person": voice_person,
                                "rate": rate,
                                "pith": voice_pitch_int
                            },
                            headers={
                                'Content-type': 'application/json'
                            },
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:

                            if response.status != 200:
                                error_text = await response.text()
                                self.logger.warning(f"Edge TTS API вернул ошибку {response.status}: {error_text}")
                                voice_bytes = None
                            else:
                                voice_bytes = await response.read()
                                if voice_bytes:
                                    self.logger.success(f"✅ Edge TTS (API): {len(voice_bytes)} байт")
                                else:
                                    self.logger.warning("Edge TTS API вернул пустой ответ")
                                    voice_bytes = None
                except aiohttp.ClientError as e:
                    self.logger.warning(f"Не удалось подключиться к Edge TTS API ({edge_tts_url}): {e}")
                    voice_bytes = None
                except Exception as e:
                    self.logger.warning(f"Ошибка при обращении к Edge TTS API: {e}")
                    voice_bytes = None
            else:
                self.logger.debug("Edge TTS API URL не указан или пустой, пропускаем")
        
        if not voice_bytes:
            self.logger.error("Не удалось получить аудио от Edge TTS")
            return None
        
        return await self.apply_voice_effect(voice_bytes)

    async def apply_voice_effect(
            self,
            voice_bytes: bytes
        ) -> bytes:
        self.logger.info("Попытка применения эффека для голосового")
        audio_buffer = BytesIO(voice_bytes)
        samples, samplerate = sf.read(audio_buffer, dtype='float32')

        samples += np.random.normal(0, 0.00005, samples.shape).astype(np.float32)

        board = Pedalboard([Reverb(room_size=0.01, damping=0.8, wet_level=0.1)])
        processed = board(samples, samplerate)

        out_buffer = BytesIO()
        sf.write(out_buffer, processed, samplerate, format='OGG', subtype='VORBIS')
        out_buffer.seek(0)
        self.logger.success("Эффект для голосового, был применен успешно")
        return out_buffer.read()

    class UserManager(BaseManager):
        def __init__(self, user_repository: UserRepository):
            super().__init__()
            self.user_repository = user_repository

        async def get_locale(
                self,
                event: ChatMemberUpdated
        ) -> str:
            if hasattr(event, "from_user") and event.from_user:
                tg_user: TelegramUser = event.from_user
            else:
                tg_user = None
            
            if tg_user:
                user = await self.user_repository.select(user_id=tg_user.id)
                return user.settings.locale if user else self.default_locale
            return self.default_locale
    
        async def set_locale(
                self,
                locale: str,
                event: ChatMemberUpdated
        ) -> None:
            if hasattr(event, "from_user") and event.from_user:
                tg_user: TelegramUser = event.from_user
                await self.user_repository.update_locale(tg_user.id, locale)