from typing import Optional
from beanie import Document
from pydantic import Field
# from ..exceptions import RecordNotFoundError, SelectError

from ..db.models import User


class UserRepository:
    async def upsert(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> User:
        user = await User.find_one(User.telegram_id == telegram_id)

        if not user:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            await user.insert()
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            await user.save()

        return user


    async def select(
        self,
        telegram_id: Optional[int] = None,
        id: Optional[str] = None,
        username: Optional[str] = None
    ) -> Optional[User]:

        if telegram_id:
            return await User.find_one(User.telegram_id == telegram_id)

        elif id:
            return await User.get(id)

        elif username:
            return await User.find_one(User.username == username)

        else:
            raise ValueError("Не был передан ни один аргумент")
