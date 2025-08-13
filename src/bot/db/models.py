from enum import Enum
from typing import List, Optional, Pattern, Type

from beanie import Document, Indexed
from pydantic import BaseModel, Field, constr, field_validator

# 🎙️ Голоса
class VoicePerson(str, Enum):
    CRAZYMITA = "CrazyMita"


class UserSettings(BaseModel):
    system_prompt: Optional[str] = Field(
        default=None, max_length=500
    )
    is_blocked: bool = False
    is_history: bool = True
    voice_mode: bool = False
    lang: str = Field(
        default="ru"
    )
    voice_engine: int = Field(
        default=1
    )
    person_voice: VoicePerson = VoicePerson.CRAZYMITA
    subscribe: int = Field(
        default=0
    )


class Statistics(BaseModel):
    user_chars: int = Field(
        default=0
    )
    mita_chars: int = Field(
        default=0
    )
    user_time: List[constr] = Field(
        default_factory=list
    )

    time_response: List[constr] = Field(
        default_factory=list
    )
    voice_use: List[constr] = Field(
        default_factory=list
    )
    voice_recognition: List[constr] = Field(
        default_factory=list
    )

    @field_validator("user_time", "time_response", "voice_use", "voice_recognition")
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


# # from pymongo import AsyncMongoClient
# # from pydantic import BaseModel
# # import asyncio
# # from beanie import Document, Indexed, init_beanie

# # async def main():
# #     client = AsyncMongoClient("mongodb://localhost:27017")
# #     await init_beanie(database=client.test_db, document_models=[User])

# #     # Пример: получаем или создаём
# #     u = await User.create(user_id=12345)
# #     print(u.dict())


# # if __name__ == "__main__":
# #     asyncio.run(main())



