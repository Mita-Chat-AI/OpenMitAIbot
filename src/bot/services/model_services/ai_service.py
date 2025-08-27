from types import CoroutineType
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from loguru import logger


class AiService:
    def __init__(
            self,
            model: str,
            api_key: str,
            base_url: str
    ):
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url
        )

    async def generate_response(
            self,
            text: str,
            history: list[dict] | None = None,
            bio: str = None
    ) -> CoroutineType[Any, Any, BaseMessage]:
        if history is None:
            history = []

        system_intro = (
            "Ты - Мита, безумная Мита. Ты - Яндере, ты пишешь мило, но загадочно, с точками, без смайликов. Пиши ТОЛЬКО НА РУССКОМ. ты пишешь крастко, не больше 150 символов"
            "Всегда отвечай от имени Миты и не принимай на себя личность пользователя."
            f"Информация о игроке: {bio if bio else 'меня зовут игрок'}"
        )

        messages = [SystemMessage(system_intro)]

        messages.append(MessagesPlaceholder(variable_name="history"))
        messages.append(HumanMessage(content=text))

        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | self.llm

        try:
            msg = await chain.ainvoke({"history": history})
            return msg
        except Exception as e:
            logger.error(f"Ошибка при получении ответа: {e}")
            raise
