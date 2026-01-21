import html
from io import BytesIO
from typing import Optional, Union

import aiohttp
import numpy as np
import soundfile as sf
from aiogram.types.chat_member_updated import ChatMemberUpdated
from aiogram.types.user import User as TelegramUser
from aiogram_i18n.managers import BaseManager
from aiogram.types import Message
from aiogram import Bot
from pedalboard import Pedalboard, Reverb

from ....settings import Config, config
from ...db.models import User
from ...repositories import UserRepository
from ..model_services.ai_service import AiService
from ..service import Service

import asyncio
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
SPK_ID = "d3311f8f9ffe"


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
            text: str,
            image: bytes =  None
    ) -> str:
        user = await self.get_data(user_id)

        ai_response = await self.ai_service.generate_response(
            user_id=user_id,
            session_id=user_id,
            text=text,
            player_prompt=user.settings.player_prompt if user.settings.player_prompt else None,
            image=image
            )


        return ai_response
    
    async def images(
            self,
            message: Message,
            bot: Bot
    ) -> tuple[str | None, bytes | None]:
        try:
            # Фото
            if message.photo:
                file = await bot.download(message.photo[-1].file_id)
                return message.caption or "Что ты видишь на этом фото? Какая твоя реакция?", file.read()

            # Стикеры
            if message.sticker:
                from PIL import Image
                import io
                import numpy as np
                import imageio.v3 as iio

                st = message.sticker
                raw = await bot.download(st.file_id)
                buf = raw.read()

                # STATIC WEBP → PNG
                if not st.is_animated and not st.is_video:
                    img = Image.open(io.BytesIO(buf))
                    out = io.BytesIO()
                    img.save(out, format="PNG")
                    return message.caption or "Что ты видишь на этом стикере? Какая твоя реакция?", out.getvalue()

                # TGS → unsupported for vision
                if st.is_animated:
                    return None, None

                # VIDEO STICKER WEBM → PNG
                if st.is_video:
                    try:
                        frame = next(iio.imiter(buf, plugin="ffmpeg"))
                    except Exception:
                        return None, None

                    out = io.BytesIO()
                    Image.fromarray(frame).save(out, format="PNG")
                    return message.caption or "Что ты видишь на этом стикере? Какая твоя реакция?", out.getvalue()

            return None, None

        except Exception as e:
            await message.reply(f"Ошибка изображения: {e}")
            return None, None
        
    def get_env(self) -> Config:
        return config

    async def return_all_user_ids(self) -> list[str]:
        return [doc.user_id for doc in await self.user_repository.get_all_users()]

    async def edge_voice_generate(self, user_id: int, text: str) -> bytes:
        data = {
            "text": text,
            "mode": "zero_shot",
            "spk_id": SPK_ID,
            "speed": 1.0,
        }

        async with aiohttp.ClientSession() as session:
            # 1. Отправляем запрос на создание задачи (POST)
            async with session.post(f"{BASE_URL}/api/tts/async", data=data) as response:
                response.raise_for_status()
                result = await response.json()
                task_id = result["task_id"]

            # 2. Ожидаем завершения задачи (Polling)
            filename = None
            while True:
                await asyncio.sleep(0.5)
                async with session.get(f"{BASE_URL}/api/task/{task_id}") as response:
                    response.raise_for_status()
                    status_data = await response.json()

                    if status_data["status"] == "completed":
                        filename = status_data["output_file"]
                        break
                    if status_data["status"] == "failed":
                        raise RuntimeError(status_data.get("error", "Unknown error"))

            # 3. Скачиваем готовый файл (GET)
            async with session.get(f"{BASE_URL}/api/download/{filename}") as response:
                response.raise_for_status()
                return await response.read()
        


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