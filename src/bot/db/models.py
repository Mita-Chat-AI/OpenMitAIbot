import re
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Pattern, Type
from uuid import UUID

from beanie import Document
from pydantic import BaseModel, Field, constr, field_validator


class Edge_TTS(BaseModel):
    person: Optional[str] = Field(
        default='CrazyMita'
    )
    rate: Optional[str] = Field(
        default="+10%"
    )
    pith: Optional[int] = Field(
        default=8
    )


class VoiceSettings(BaseModel):
    edge_tts: Edge_TTS = Field(
        default_factory=Edge_TTS
    )


class Subscription(BaseModel):
    """Модель подписки пользователя"""
    type: int = Field(default=0)  # 0 - нет подписки, 1 - недельная, 2 - месячная
    tokens: int = Field(default=0)  # Оставшиеся токены
    expires_at: Optional[datetime] = Field(default=None)  # Дата истечения подписки
    created_at: Optional[datetime] = Field(default=None)  # Дата создания подписки
    phone_number: Optional[str] = Field(default=None, max_length=20)  # Номер телефона

class UserSettings(BaseModel):
    player_prompt: Optional[str] = Field(
        default=None, max_length=500
    )
    is_blocked: bool = False
    is_history: bool = True
    voice_mode: bool = True  # По умолчанию включен для всех
    locale: str = Field(
        default="ru"
    )
    voice_engine: int = Field(
        default=1
    )
    subscribe: int = Field(
        default=0
    )
    subscription: Subscription = Field(
        default_factory=Subscription
    )
    last_request_time: Optional[datetime] = Field(default=None)  # Время последнего запроса
    min_request_interval: int = Field(default=2)  # Минимальный интервал между запросами в секундах


class Statistics(BaseModel):
    voice_use: List[constr] = Field(
        default_factory=list
    )
    voice_recognition: List[constr] = Field(
        default_factory=list
    )

    @field_validator("voice_recognition")
    def limit_list_length(cls, v):
        """Ограничитель длины спискв до 1000 символов"""
        if len(v) > 1000:
            return v[-1000:]  # оставляем последние 1000
        return v


class User(Document):
    user_id: int
    settings: UserSettings = Field(
        default_factory=UserSettings
    )
    voice_settings: VoiceSettings = Field(
        default_factory=VoiceSettings
    )
    statistics: Statistics = Field(
        default_factory=Statistics
    )

    class Settings:
        name = "users"

    @classmethod
    async def create(
        cls: Type["User"],
        user_id: int
    ):
        user = await cls.find_one(cls.user_id == user_id)

        if user:
            return user

        user = cls(user_id=user_id)
        await user.insert()
        return user
