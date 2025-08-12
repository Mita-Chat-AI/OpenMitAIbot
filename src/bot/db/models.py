from typing import Optional, List
from beanie import Document
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# 🎙️ Голоса
class VoicePerson(str, Enum):
    CRAZYMITA = "CrazyMita"
    OTHER = "Other"


class UserSettings(BaseModel):
    conditions: bool = False
    system_prompt: Optional[str] = None
    is_blocked: bool = False
    is_history: bool = True
    voice_mode: bool = False
    lang: str = "ru"
    voice_engine: int = 1
    person_voice: VoicePerson = VoicePerson.CRAZYMITA
    subscribe: int = 0


class Statistics(BaseModel):
    all_chars: int = 0
    user_chars: int = 0
    mita_chars: int = 0
    conv: int = 0
    user_time: List[str] = []
    time_response: List[str] = []
    voice_use: List[str] = []
    voice_recognition: List[str] = []

    @field_validator("user_time", "time_response", "voice_use", "voice_recognition", pre=True, always=True)
    def limit_list_length(cls, v):
        if isinstance(v, list):
            # Ограничиваем суммарную длину всех элементов до 1000 символов
            total_len = 0
            new_list = []
            for item in v:
                if total_len + len(item) > 1000:
                    break
                new_list.append(item)
                total_len += len(item)
            return new_list
        return v


# 👤 Модель пользователя
class User(Document):
    tg_id: int
    settings: UserSettings = Field(default_factory=UserSettings)
    statistics: Statistics = Field(default_factory=Statistics)

    class Settings:
        name = "users"
