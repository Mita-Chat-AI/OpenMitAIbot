from settings.main import config

async def startup(bot):
    await bot.send_message(
        chat_id=config.telegram.owner_id,
        text='Привет'
    )