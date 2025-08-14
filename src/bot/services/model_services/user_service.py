import html
from typing import Optional, Union

from aiogram.types.chat_member_updated import ChatMemberUpdated
from aiogram.types.user import User as TelegramUser
from aiogram_i18n.managers import BaseManager

from ...db.models import User
from ...repositories import UserRepository
from ..service import Service
import requests
from io import BytesIO

from ....settings import config

import aiohttp

from io import BytesIO
import numpy as np
import requests
import soundfile as sf
from pedalboard import Pedalboard, Reverb

class UserService(Service):

    data: User | None

    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self.user_repository = user_repository
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

    def create_link(
        self,
        name: str,
        id: Optional[int] = None,
        username: Optional[str] = None
    ) -> str:
        
        name = name.replace('>', '').replace('<', '')
        print(f"name: {name}; id: {id}; username: {username}")
        if id:
            return f"<a href='tg://user?id={id}'>{name}</a>"
        
        elif username:
            return f"<a href='https://t.me/{html.escape(username)}'>{name}</a>"
        
        else:
            return name
        
    def get_env(self):
        return config


    async def edge_voice_generate(
            self, user_id: int,
            text: str
    ) -> bytes:
        self.logger.info(f"Попытка записи голосового сообщения для {user_id} : {text}")

        user = await self.get_data(search_argument=user_id)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=self.config.voice_config.edge_tts.get_secret_value(),
                    json={
                        "text": text,
                        "person": user.voice_settings.edge_tts.person,
                        "rate": user.voice_settings.edge_tts.rate,
                        "pith": user.voice_settings.edge_tts.pith
                    },
                    headers={
                        'Content-type': 'application/json'
                    }
                ) as response:

                    if response.status != 200:
                        self.logger.error(f"{await response.text()}")
                        return None

                    voice_bytes = await response.read()
                    self.logger.success(f"Удалось записать голосовое для {user_id}")
        except Exception as e:
            self.logger.error(f"Не удалось записать голосовое для {user_id} : {e}")
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