

from aiogram import Bot, F, Router
from aiogram.types.chat_member_updated import ChatMemberUpdated
from dependency_injector.wiring import Provide, inject

from ...containers import Container
from ...services import UserService

router = Router(name=__name__)

@router.channel_post()
@inject
async def mailing_channel_post(
    post: ChatMemberUpdated,
    bot: Bot,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    channel_id = user_service.config.telegram.channel_mailing_id

    if post.chat.id != channel_id:
        return

    tg_ids = await user_service.return_all_user_ids()

    for user_id in tg_ids:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=post.chat.id,
                message_id=post.message_id
            )
        except Exception as e:
            user_service.logger.warning(f"Ошибка при рассылке {user_id}: {e}")
