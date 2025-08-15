from typing import List

from beanie import Document, init_beanie
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from pymongo import AsyncMongoClient


async def get_history(session):
    return [{"type": m.type, "content": m.content} for m in session.messages]


async def test():
    client = AsyncMongoClient(host="mongodb://localhost:27017")

    await init_beanie(
        database=client.test_db,
        document_models=[Message]
    )

    session_id = 3
    session = await Message.find_one(
        Message.session_id == session_id
    )
    if not session:
        session = Message(
            session_id=session_id,
            messages=[]
        )
        await session.insert()



    prompt = ChatPromptTemplate.from_messages(
        [

            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    llm = ChatOpenAI(model="CrazyMita", api_key="lm-studio",base_url="http://hour-checking.gl.at.ply.gg:45843/v1")

    chain = prompt | llm

    while True:
        history = await get_history(session)

        question = input("Запрос: ")

        msg = chain.invoke({
            "question": question,
            "history": history  # обязательно передаем
        })
        


        session.messages.append(
            TypeMessage(
                type='human',
                content=question
            )
        )
        session.messages.append(
            TypeMessage(
                type="ai",
                content=msg.content
            )
        )

        print(msg.content)

        await session.save()






import asyncio

asyncio.run(test())
