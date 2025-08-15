import hashlib
import json

from aiogram import F, Router
from aiogram.enums import ChatType, ContentType
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject
from langchain.schema import BaseCache
from langchain_core.outputs.chat_generation import ChatGeneration
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pymongo import MongoClient

from ...containers import Container
from ...services import UserService


class MongoCache(BaseCache):
    def __init__(self, uri="mongodb://localhost:27017", db_name="chat_cache", collection="responses"):
        self.client = MongoClient(uri)
        self.collection = self.client[db_name][collection]

    def _key(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()

    def lookup(self, prompt: str, llm_string: str | None = None):
        key = self._key(prompt)
        result = self.collection.find_one({"_id": key})
        if result:
            # Десериализуем JSON обратно в объекты ChatGeneration
            response_list = json.loads(result["response"])
            return [ChatGeneration(**gen) for gen in response_list]
        return None

    def update(self, prompt: str, llm_string: str | None, response: list):
        key = self._key(prompt)
        # Сериализуем объекты ChatGeneration в JSON
        response_json = json.dumps([gen.dict() if isinstance(gen, ChatGeneration) else str(gen) for gen in response])
        self.collection.update_one(
            {"_id": key},
            {"$set": {"response": response_json}},
            upsert=True
        )

    def clear(self):
        """Очистка всего кэша"""
        self.collection.delete_many({})


router = Router(name=__name__)

@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.content_type.in_([ContentType.TEXT]),
    ~F.text.startswith("/")
)
@inject
async def mita_handler(
    message: Message,
    user_service: UserService = Provide[
        Container.user_service
    ]) -> None:


    prompt = ChatPromptTemplate.from_messages(
        [

            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    llm = ChatOpenAI(
        model="CrazyMita",
        api_key="lm-studio",
        base_url="http://hour-checking.gl.at.ply.gg:45843/v1",
        temperature=0.7,
        max_completion_tokens=1000,
        cache=MongoCache()  # наш MongoDB кэш
    )



    chain = prompt | llm


    history = await user_service.user_repository.get_history(message.from_user.id)


    msg = chain.invoke({
        "question": message.text,
        "history": history  # обязательно передаем
    })
    print(msg)
    if msg.response_metadata.get("finish_reason") == "length":
        print(f"⚠ Достигнут лимит токенов, ответ обрезан ")
        print({msg.response_metadata.get("finish_reason")})

    

    await message.reply(text=msg.content)
    

    await user_service.user_repository.update_message_history(
        user_id=message.from_user.id,
        human=message.text,
        ai=msg.content
    )





