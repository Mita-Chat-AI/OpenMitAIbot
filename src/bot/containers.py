from dependency_injector import containers, providers
from aiogram import Bot
from .repositories import UserRepository
from .services.model_services.user_service import UserService
from .services.model_services.ai_service import AiService
from ..settings import config

class Container(containers.DeclarativeContainer):
    bot = providers.Dependency(instance_of=Bot)

    user_repo = providers.Factory(UserRepository)

    ai_service = providers.Factory(
        AiService,
        model=config.ai_config.model,
        api_key=config.ai_config.api_key.get_secret_value(),
        base_url=config.ai_config.base_url.get_secret_value()
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repo,
        ai_service=ai_service
    )
