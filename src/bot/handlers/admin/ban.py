from aiogram import Router
from dependency_injector.wiring import Provide, inject
from aiogram.types import Message

from aiogram.filters.command import Command, CommandObject
from ...containers import Container

from ...services import UserService

router = Router(name=__name__)

@router.message(Command('ban'))
@inject
async def mailing_channel_post(
    message: Message,
    command: CommandObject,
    user_service: UserService = Provide[
        Container.user_service
    ]
) -> None:
    arg = command.args.split()

    if len(arg) < 2:
        await message.reply("Используй: /ban <user_id> <1-блок/0-разблок>")
        return

    try:
        user_id = int(arg[0])
        ban_flag = arg[1] == "1"


        await user_service.user_repository.update_ban(
            user_id=user_id,
            ban=str(True if ban_flag == 1 else False)
        )

        if ban_flag:
            await message.reply(f"Пользователь {user_id} заблокирован ✅")
        else:
            await message.reply(f"Пользователь {user_id} разблокирован ✅")

    except ValueError:
        await message.reply("Неверный формат user_id или флага.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")
        