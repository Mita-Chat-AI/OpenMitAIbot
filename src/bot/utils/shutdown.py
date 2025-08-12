from ...settings.main import config


async def shutdown(bot):
    await bot.send_message(
        chat_id=config.telegram.owner_id,
        text='пока'
    )