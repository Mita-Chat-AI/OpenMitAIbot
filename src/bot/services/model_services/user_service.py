import html
from typing import Optional, Union

from ...db.models import User
from ...repositories import UserRepository
from .. import Service


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

        if isinstance(search_argument, str):
            user = await self.user_repository.select(username=search_argument)

        elif search_argument >= 777000:
            user = await self.user_repository.select(telegram_id=search_argument)

        else:
            user = await self.user_repository.select(id=search_argument)

        if not user and isinstance(search_argument, int):
            user = await self.user_repository.upsert(
                telegram_id=search_argument,
                first_name="Unknown"  # Можно брать из message.from_user.first_name
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
