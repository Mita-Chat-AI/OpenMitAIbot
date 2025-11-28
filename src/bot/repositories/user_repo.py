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
            user = User(user_id=user_id)
            await user.insert()

        return user

    async def select(
        self,
        user_id: Optional[int] = None,
        id: Optional[str] = None,
    ) -> Optional[User]:

        if user_id:
            user = await self.upsert(user_id)
        elif id:
            user = await User.get(id)
            if not user:
                raise SelectError(f"Пользователь с id={id} не найден")
        else:
            raise SelectError("Не был передан ни один аргумент")

        return user

    async def get_all_users(self) -> list[str]:
        users = User.find_all()
        return await users.to_list()

    async def update_bio(
        self,
        user_id: int,
        bio: str
    ) -> None:
        user = await self.upsert(user_id=user_id)
        user.settings.system_prompt = bio
        await user.save()

    async def update_ban(
        self,
        user_id: int,
        ban: str
    ) -> Optional[User]:
        user = await self.upsert(user_id)
        user.settings.is_blocked = ban
        await user.save()
        return user

    async def update_voicemod(
        self,
        user_id: int,
        mode: str
    ) -> Optional[User]:
        user = await self.upsert(user_id)
        user.settings.voice_mode = mode
        await user.save()
        return user

    async def update_locale(
        self,
        user_id: int,
        locale: str
    ) -> Optional[User]:
        user = await self.upsert(user_id)
        user.locale = locale
        await user.save()
        return user

    # async def update_message_history(
    #     self,
    #     user_id: int,
    #     human: str,
    #     ai: str
    # ) -> None:
    #     user = await self.upsert(user_id)

    #     def to_message(type_, content):
    #         return TypeMessage(type=type_, content=content)

    #     user.user_history.messages.extend([
    #         to_message("human", human),
    #         to_message("ai", ai)
    #     ])
    #     await user.save()

    async def clear_history(
        self,
        user_id: int
    ) -> None:
        user = await self.upsert(user_id)
        if user.user_history:
            user.user_history.messages = []
            await user.save()

    async def get_history(
        self,
        user_id: int
    ) -> list[dict]:
        user = await self.upsert(user_id)
        if user.user_history:
            return [{"type": m.type, "content": m.content} for m in user.user_history.messages]
        else:
            return [{}]
