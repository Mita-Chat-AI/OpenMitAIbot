from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage

class AiService:
    def __init__(self, model: str, api_key: str, base_url: str):
        # теперь полностью независимый от UserService
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

        msg: BaseMessage | None = await chain.ainvoke({
            "question": text,
            "history": history
        })
        print(msg)

        return msg
