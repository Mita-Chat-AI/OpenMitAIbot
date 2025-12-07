import asyncio
import html
from io import BytesIO
from typing import Optional, Union

import aiohttp
import numpy as np
import soundfile as sf
from aiogram.types.chat_member_updated import ChatMemberUpdated
from aiogram.types.user import User as TelegramUser
from aiogram_i18n.managers import BaseManager
from openai import APIConnectionError
from pedalboard import Pedalboard, Reverb
from pydub import AudioSegment

from ....settings import Config, config
from ...db.models import User
from ...repositories import UserRepository
from ...utils.voice_utils import (
    generate_edge_tts,
    map_person_to_voice,
    map_pitch_int_to_hz
)
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

    async def ask_ai(
            self,
            user_id: int,
            text: str
    ) -> str:
        try:
            user = await self.get_data(user_id)

            ai_response = await self.ai_service.generate_response(
                user_id=user_id,
                session_id=user_id,
                text=text,
                player_prompt=user.settings.player_prompt if user.settings.player_prompt else None
                )

            if not ai_response or not hasattr(ai_response, 'content'):
                self.logger.warning(f"AI вернул пустой ответ для пользователя {user_id}")
                return None
                
            return ai_response.content
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
        Генерирует голосовое сообщение через Edge TTS.
        
        Использует библиотеку edge-tts напрямую (без внешнего API).
        Поддерживает fallback на внешний API если библиотека недоступна.
        """
        self.logger.info(f"Попытка записи голосового сообщения для {user_id} : {text}")

        user = await self.get_data(search_argument=user_id)
        
        # Получаем настройки голоса
        voice_person = user.voice_settings.edge_tts.person or "CrazyMita"
        voice_rate = user.voice_settings.edge_tts.rate or "+10%"
        voice_pitch_int = user.voice_settings.edge_tts.pith or 8
        
        # Конвертируем настройки в формат Edge TTS
        voice = map_person_to_voice(voice_person)
        rate = voice_rate
        pitch = map_pitch_int_to_hz(voice_pitch_int)
        
        self.logger.debug(f"Голос: {voice}, rate: {rate}, pitch: {pitch}")

        # Пробуем использовать библиотеку edge-tts напрямую
        voice_bytes = None
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
            edge_tts_url = self.config.voice_config.edge_tts.get_secret_value()
            if edge_tts_url and edge_tts_url != "":
                try:
                    self.logger.info("Пробуем Edge TTS через внешний API...")
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
                            }
                        ) as response:

                            if response.status != 200:
                                self.logger.error(f"Edge TTS API вернул ошибку: {await response.text()}")
                                return None

                            voice_bytes = await response.read()
                            self.logger.success(f"✅ Edge TTS (API): {len(voice_bytes)} байт")
                except Exception as e:
                    self.logger.error(f"Не удалось записать голосовое через API для {user_id} : {e}")
                    return None
            else:
                self.logger.error("Edge TTS библиотека недоступна и API URL не указан")
                return None
        
        if not voice_bytes:
            self.logger.error("Не удалось получить аудио от Edge TTS")
            return None
        
        # 1) Базовый TTS уже есть - применяем эффекты
        processed = await self.apply_voice_effect(voice_bytes)
        if not processed:
            self.logger.error("apply_voice_effect вернул пустое значение")
            return None

        # 2) Прогоняем через RVC, если настроено
        processed = await self.apply_rvc_remote(processed)
        return processed

    async def apply_voice_effect(
            self,
            voice_bytes: bytes
        ) -> bytes:
        """
        Применяет эффекты к голосовому сообщению.
        
        Поддерживает форматы: MP3 (от Edge TTS), WAV, OGG
        Конвертирует в OGG для Telegram.
        """
        self.logger.info("Попытка применения эффекта для голосового")
        
        try:
            # Определяем формат по первым байтам
            audio_format = self._detect_audio_format(voice_bytes)
            self.logger.debug(f"Определен формат аудио: {audio_format}")
            
            # Конвертируем MP3/WAV в numpy array
            # Пробуем разные методы в зависимости от формата
            if audio_format == "mp3":
                # MP3: пробуем через pydub, если не получится - через librosa
                try:
                    audio_segment = AudioSegment.from_mp3(BytesIO(voice_bytes))
                except Exception as e:
                    self.logger.debug(f"pydub не смог прочитать MP3: {e}, пробуем librosa")
                    try:
                        import librosa
                        samples, samplerate = librosa.load(BytesIO(voice_bytes), sr=None, mono=True)
                        # Применяем эффекты
                        samples += np.random.normal(0, 0.00005, samples.shape).astype(np.float32)
                        board = Pedalboard([Reverb(room_size=0.01, damping=0.8, wet_level=0.1)])
                        processed = board(samples, samplerate)
                        # Сохраняем в OGG
                        out_buffer = BytesIO()
                        sf.write(out_buffer, processed, samplerate, format='OGG', subtype='VORBIS')
                        out_buffer.seek(0)
                        self.logger.success("Эффект для голосового был применен успешно (librosa)")
                        return out_buffer.read()
                    except ImportError:
                        self.logger.error("librosa не установлен, не могу обработать MP3")
                        raise
            elif audio_format == "wav":
                # WAV через pydub или soundfile
                try:
                    audio_segment = AudioSegment.from_wav(BytesIO(voice_bytes))
                except Exception:
                    # Пробуем через soundfile
                    audio_buffer = BytesIO(voice_bytes)
                    samples, samplerate = sf.read(audio_buffer, dtype='float32')
                    if len(samples.shape) > 1:
                        samples = samples.mean(axis=1)  # Стерео -> моно
                    # Применяем эффекты
                    samples += np.random.normal(0, 0.00005, samples.shape).astype(np.float32)
                    board = Pedalboard([Reverb(room_size=0.01, damping=0.8, wet_level=0.1)])
                    processed = board(samples, samplerate)
                    # Сохраняем в OGG
                    out_buffer = BytesIO()
                    sf.write(out_buffer, processed, samplerate, format='OGG', subtype='VORBIS')
                    out_buffer.seek(0)
                    self.logger.success("Эффект для голосового был применен успешно")
                    return out_buffer.read()
            elif audio_format == "ogg":
                # OGG через pydub или soundfile
                try:
                    audio_segment = AudioSegment.from_ogg(BytesIO(voice_bytes))
                except Exception:
                    # Пробуем через soundfile
                    audio_buffer = BytesIO(voice_bytes)
                    samples, samplerate = sf.read(audio_buffer, dtype='float32')
                    if len(samples.shape) > 1:
                        samples = samples.mean(axis=1)  # Стерео -> моно
                    # Применяем эффекты
                    samples += np.random.normal(0, 0.00005, samples.shape).astype(np.float32)
                    board = Pedalboard([Reverb(room_size=0.01, damping=0.8, wet_level=0.1)])
                    processed = board(samples, samplerate)
                    # Сохраняем в OGG
                    out_buffer = BytesIO()
                    sf.write(out_buffer, processed, samplerate, format='OGG', subtype='VORBIS')
                    out_buffer.seek(0)
                    self.logger.success("Эффект для голосового был применен успешно")
                    return out_buffer.read()
            else:
                # Неизвестный формат: пробуем через soundfile или pydub
                try:
                    audio_buffer = BytesIO(voice_bytes)
                    samples, samplerate = sf.read(audio_buffer, dtype='float32')
                    if len(samples.shape) > 1:
                        samples = samples.mean(axis=1)  # Стерео -> моно
                except Exception:
                    # Пробуем через pydub (автоопределение формата)
                    try:
                        audio_segment = AudioSegment.from_file(BytesIO(voice_bytes))
                    except Exception as e:
                        self.logger.error(f"Не удалось определить формат аудио: {e}")
                        raise
                    # Конвертируем в numpy
                    samples = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
                    if audio_segment.channels == 2:
                        samples = samples.reshape((-1, 2))
                        samples = samples.mean(axis=1)
                    samples = samples / (1 << 15)
                    samplerate = audio_segment.frame_rate
                
                # Применяем эффекты
                samples += np.random.normal(0, 0.00005, samples.shape).astype(np.float32)
                board = Pedalboard([Reverb(room_size=0.01, damping=0.8, wet_level=0.1)])
                processed = board(samples, samplerate)
                # Сохраняем в OGG
                out_buffer = BytesIO()
                sf.write(out_buffer, processed, samplerate, format='OGG', subtype='VORBIS')
                out_buffer.seek(0)
                self.logger.success("Эффект для голосового был применен успешно")
                return out_buffer.read()
            
            # Конвертируем в numpy array
            samples = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
            if audio_segment.channels == 2:
                samples = samples.reshape((-1, 2))
                samples = samples.mean(axis=1)  # Стерео -> моно
            samples = samples / (1 << 15)  # Нормализация из int16 в float32
            
            samplerate = audio_segment.frame_rate
            
            # Применяем эффекты
            samples += np.random.normal(0, 0.00005, samples.shape).astype(np.float32)
            board = Pedalboard([Reverb(room_size=0.01, damping=0.8, wet_level=0.1)])
            processed = board(samples, samplerate)
            
            # Сохраняем в OGG
            out_buffer = BytesIO()
            sf.write(out_buffer, processed, samplerate, format='OGG', subtype='VORBIS')
            out_buffer.seek(0)
            self.logger.success("Эффект для голосового был применен успешно")
            return out_buffer.read()
            
        except Exception as e:
            self.logger.error(f"Ошибка при применении эффекта: {e}")
            # Пробуем вернуть исходное аудио, конвертированное в OGG
            try:
                audio_segment = AudioSegment.from_file(BytesIO(voice_bytes))
                ogg_buffer = BytesIO()
                audio_segment.export(ogg_buffer, format="ogg", codec="libvorbis")
                ogg_buffer.seek(0)
                self.logger.warning("Вернули исходное аудио без эффектов (конвертировано в OGG)")
                return ogg_buffer.read()
            except Exception as e2:
                self.logger.error(f"Критическая ошибка: не удалось обработать аудио: {e2}")
                return voice_bytes  # Возвращаем как есть
    
    def _detect_audio_format(self, audio_bytes: bytes) -> str:
        """Определяет формат аудио по первым байтам"""
        if len(audio_bytes) < 4:
            return "unknown"
        
        # MP3: начинается с FF FB или ID3
        if audio_bytes[:3] == b'ID3' or audio_bytes[:2] == b'\xff\xfb':
            return "mp3"
        # WAV: начинается с RIFF
        elif audio_bytes[:4] == b'RIFF':
            return "wav"
        # OGG: начинается с OggS
        elif audio_bytes[:4] == b'OggS':
            return "ogg"
        else:
            return "unknown"

    async def apply_rvc_remote(self, voice_bytes: bytes) -> bytes:
        """
        Отправляет готовое аудио в RVC API (если настроено).
        Если URL не указан или произошла ошибка — возвращаем исходное аудио.
        
        Таймаут: 30 секунд (достаточно для обработки даже длинных аудио)
        """
        rvc_url = getattr(self.config.voice_config, "rvc", None)
        if not rvc_url:
            self.logger.debug("RVC URL не указан, пропускаем преобразование")
            return voice_bytes

        try:
            timeout = aiohttp.ClientTimeout(total=30)  # 30 секунд таймаут
            async with aiohttp.ClientSession(timeout=timeout) as session:
                form = aiohttp.FormData()
                form.add_field(
                    "audio",
                    voice_bytes,
                    filename="voice.ogg",
                    content_type="audio/ogg"
                )

                self.logger.info(f"Отправка аудио в RVC API ({len(voice_bytes)} байт)...")
                
                async with session.post(
                    rvc_url.get_secret_value(),
                    data=form
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        self.logger.warning(
                            f"RVC API вернул ошибку {response.status}: {text[:200]}"
                        )
                        return voice_bytes

                    rvc_bytes = await response.read()
                    if not rvc_bytes:
                        self.logger.warning("RVC API вернул пустой ответ")
                        return voice_bytes

                    self.logger.success(
                        f"✅ RVC успешно применён: {len(voice_bytes)} → {len(rvc_bytes)} байт"
                    )
                    return rvc_bytes

        except aiohttp.ClientError as e:
            self.logger.warning(f"Ошибка подключения к RVC API: {e}")
            return voice_bytes
        except asyncio.TimeoutError:
            self.logger.warning("Таймаут при обращении к RVC API (30 сек)")
            return voice_bytes
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при обращении к RVC API: {e}")
            return voice_bytes

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