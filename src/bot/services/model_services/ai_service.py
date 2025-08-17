from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .user_service import UserService


class AiService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.llm = ChatOpenAI(
            model=self.user_service.config.ai_config.model,
            api_key=self.user_service.config.ai_config.api_key,
            base_url=self.user_service.config.ai_config.base_url
        )

    async def gg(self, user_id: int, text: str):
        prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])
        chain = prompt | self.llm

        history = await self.user_service.user_repository.get_history(user_id)

        msg = await chain.ainvoke({
            "question": text,
            "history": history
        })
    
        if msg:
            await self.user_service.user_repository.update_message_history(
                user_id=user_id,
                human=text,
                ai=msg.content
            )

        return msg.content if msg else None