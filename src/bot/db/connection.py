from pymongo import AsyncMongoClient
from beanie import init_beanie
from .models import User

async def init_db():
    client = AsyncMongoClient("mongodb://localhost:27017")
    await init_beanie(database=client.my_database, document_models=[User])
