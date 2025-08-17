from aiogram import Router
from aiogram.filters.command import Command
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject

from ...containers import Container
from ...services import UserService

router = Router(name=__name__)

@router.message(Command('reset'))
async def reset_history(
        message: Message,
        user_service: UserService = Provide[
            Container.user_service
        ]
): 
    pass

