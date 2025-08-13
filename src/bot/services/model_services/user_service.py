import html
from typing import Optional, Union

from ...db.models import User
from ...repositories import UserRepository
from ..service import Service

from aiogram_i18n.managers import BaseManager
from aiogram.types.user import User as TelegramUser

class UserService(Service):

    data: User | None

    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self.user_repository = user_repository
        self.data = None

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

    class UserManager(BaseManager):
        def __init__(self, user_repository: UserRepository):
            super().__init__()
            self.user_repository = user_repository

        async def get_locale(
                self,
                event_from_user: TelegramUser
        ) -> str:
            user = await self.user_repository.select(event_from_user.id)
            return user.settings.locale if user else "ru"

        async def set_locale(
                self,
                locale: str,
                event_from_user: TelegramUser
        ) -> None:
            await self.user_repository.update_locale(event_from_user.id, locale)

