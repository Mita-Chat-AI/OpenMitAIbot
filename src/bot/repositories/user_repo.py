from typing import Optional


from ..db.models import TypeMessage, User
from ..exeptions import SelectError


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
            user = await User.find_one(User.user_id == user_id)
        elif id:
            user = await User.get(id)
        else:
            raise SelectError("Не был передан ни один аргумент")

        if not user:
            user = await self.upsert(user_id)

        return user
    

    async def get_all_users(self) -> list[str]:
        users = User.find_all()
        return await users.to_list()


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
    
    async def update_message_history(
        self,
        user_id: int,
        human: str,
        ai: str
    ) -> None:
        user = await self.select(user_id=user_id)

        def to_message(type_, content):
            return TypeMessage(type=type_, content=content)

        user.user_history.messages.extend([
            to_message("human", human),
            to_message("ai", ai)
        ])

        await user.save()

    async def clear_history(
        self,
        user_id: int
    ) -> None:
        user = await self.select(user_id=user_id)
        if user.user_history:
            user.user_history.messages = []
            await user.save()

    async def get_history(
            self,
            user_id: int
    ) -> None:
        user = await self.select(user_id=user_id)
        if user.user_history:
            return [{"type": m.type, "content": m.content} for m in user.user_history.messages]
        else:
            return [{}]


