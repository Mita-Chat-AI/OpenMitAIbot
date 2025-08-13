from typing import Optional

from beanie import Document
from pydantic import Field

from ..db.models import User
from ..exeptions import SelectError

# from ..exceptions import RecordNotFoundError, SelectError


class UserRepository:
    async def upsert(
        self,
        user_id: int,

    ) -> User:
        user = await User.find_one(User.user_id == user_id)

        if not user:
            user = User(
                user_id=user_id
            )
            await user.insert()

        return user

    async def select(
        self,
        user_id: Optional[int] = None,
        id: Optional[str] = None,
    ) -> Optional[User]:

        if user_id:
            return await User.find_one(User.user_id == user_id)

        elif id:
            return await User.get(id)

        else:
            raise SelectError("Не был передан ни один аргумент")
        
    async def update_locale(
        self,
        user_id: int,
        locale: str
    ) -> Optional[User]:
        user = await User.find_one(User.user_id == user_id)
        if not user:
            raise SelectError(f"Пользователь с user_id={user_id} не найден")

        user.locale = locale
        await user.save()
        return user
