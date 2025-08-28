from aiogram import Router
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject
from aiogram_i18n import I18nContext
from ...containers import Container
from ...services import UserService


router = Router(name=__name__)


@router.message(Command('ban'))
@inject
async def mailing_channel_post(
    message: Message,
    command: CommandObject,
    i18n: I18nContext,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    args = command.args

    if len(args) < 2 or not args:
        await message.reply(
            text=i18n.get(
                "ban-usage"
            )
        )
        return

    arg = command.args.split()

    try:
        user_id = int(arg[0])
        ban_flag = arg[1] == "1"

        await user_service.user_repository.update_ban(
            user_id=user_id,
            ban=str(ban_flag)
        )

        if ban_flag:
            await message.reply(
                text=i18n.get(
                    "ban-user-blocked",
                    user_id=user_id
                )
            )
        else:
            await message.reply(
                text=i18n.get(
                    "ban-user-unblocked",
                    user_id=user_id
                )
            )

    except ValueError:
        await message.reply(
            text=i18n.get(
                "ban-invalid-format"
                )
            )
    except Exception as e:
        await message.reply(
            text=i18n.get(
                "ban-error",
                error=str(e)    
            )
        )
