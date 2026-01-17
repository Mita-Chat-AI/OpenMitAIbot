from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f'{Path(__file__).parents[2]}/.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


class AiogramConfig(BaseConfig):
    model_config = SettingsConfigDict(
        env_prefix="tg_"
    )

    bot_token: SecretStr
    owner_id: int
    channel_id: int
    channel_mailing_id: int

class VoiceConfig(BaseConfig):
    model_config = SettingsConfigDict(
        env_prefix="api_"
    )

    edge_tts: SecretStr | None = Field(default=None)
    rvc: SecretStr | None = None
    voice_mode_enabled: bool = Field(default=False)

class AiConfig(BaseConfig):
    model_config = SettingsConfigDict(
        env_prefix='ai_'
    )

    model: str
    api_key: SecretStr
    base_url: SecretStr
    provider: str = Field(default="openai")
    proxy_url: SecretStr | None = Field(default=None)
    tokens_per_request: int = Field(default=200)
    subscription_weekly_tokens: int = Field(default=2000)
    subscription_monthly_tokens: int = Field(default=10000)


class DbConfig(BaseConfig):
    model_config = SettingsConfigDict(
        env_prefix="db_"
    )

    url: str = Field(default="mongodb://localhost:27017")
    name: str = Field(default="my_database")


class Config(BaseSettings):
    telegram: AiogramConfig = Field(
        default_factory=AiogramConfig
    )
    voice_config: VoiceConfig = Field(
        default_factory=VoiceConfig
    )
    ai_config: AiConfig = Field(
        default_factory=AiConfig
    )
    db: DbConfig = Field(
        default_factory=DbConfig
    )

    @classmethod
    def load(cls) -> Self:
        return cls()

config = Config.load()
