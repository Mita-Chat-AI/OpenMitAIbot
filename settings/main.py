from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='settings/.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


class AiogramConfig(BaseConfig):
    model_config = SettingsConfigDict(
        env_prefix="tg_"
    )

    bot_token: SecretStr
    owner_id: int


class Config(BaseSettings):
    telegram: AiogramConfig = Field(
        default_factory=AiogramConfig
    )

    @classmethod
    def load(cls) -> Self:
        return cls()

config = Config.load()
