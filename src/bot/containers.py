from contextvars import ContextVar

from aiogram import Bot
from dependency_injector import containers, providers

from .repositories import UserRepository
from .services import UserService


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    bot = providers.Dependency(instance_of=Bot)

    # Репозиторий
    user_repo = providers.Factory(
        UserRepository
    )

    # Сервис
    user_service = providers.Factory(
        UserService,
        user_repository=user_repo
    )
