from beanie import init_beanie
from pymongo import AsyncMongoClient

from .models import User


async def init_db(

) -> None:
    client = AsyncMongoClient(
        host="mongodb://localhost:27017"
    )

    await init_beanie(
        database=client.my_database,
        document_models=[User]
    )
