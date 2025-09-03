from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from loguru import logger

from ....prompt import SYSTEM_PROMPT
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
    ) -> BaseMessage:
        if history is None:
            history = []
        system_intro = f"{SYSTEM_PROMPT} Информация о игроке, которого ты любишь: {bio if bio else 'меня зовут игрок'}"
    


        messages = [
            SystemMessage(
                system_intro
            )
        ]

        messages.append(
            MessagesPlaceholder(
                variable_name="history"
            )
        )
        messages.append(
            HumanMessage(
                content=text
            )
        )

        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | self.llm

        try:
            msg = await chain.ainvoke(
                input={
                    "history": history
                }
            )
            return msg
        except Exception as e:
            logger.error(f"Ошибка при получении ответа: {e}")
            raise
