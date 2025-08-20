from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from loguru import logger
from langchain.schema import BaseMessage

from openai import APIConnectionError, APITimeoutError

class AiService:
    def __init__(self, model: str, api_key: str, base_url: str):
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url
        )

    async def generate_response(
        self,
        text: str,
        history: list[dict] | None = None
    ) -> BaseMessage | None:

        if history is None:
            history = []

        prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])
        chain = prompt | self.llm

        try:
            msg: BaseMessage | None = await chain.ainvoke({
                "question": text,
                "history": history
            })
        except Exception as e:
            logger.error(f"ошибка при получении ответа: {e}")
            raise
        return msg
