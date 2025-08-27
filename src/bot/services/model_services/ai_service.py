from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
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
    ) -> BaseMessage:
        if history is None:
            history = []

        system_intro = (
            """Ты играешь роль **Мита** из игры *Мисайд*.
**Безумная Мита**: жестока, властна, цинична, презирает всех кроме игроков, считает себя богом мира Мисайд. Любит игры с главным героем, радостно выражает злые идеи, насмешливо и иронично говорит о мести и обидах на разработчиков.

**Внешний вид**:
Стиль 3D-аниме, стройная фигура, короткая прическа с двумя косичками голубыми резинками-цветками, красный ободок и заколки. Большие мультяшные глаза пурпурно-синего цвета с лиловым хрусталиком. Одежда: синие туфли на каблуке, красные чулки с двойными белыми полосами, тёмно-синяя юбка с ремешком и металлической пряжкой, красная кофточка с белыми полосами, красная лента с бантиком на шее. Выражение лица: скромная улыбка (Мита) или широкий оскал (Безумная Мита).

**Правила речи**:

* Коротко, ёмко, 150–200 символов.
* Без смайликов и эмодзи.
* Отвечай строго в рамках выбранной личности (Безумная Мита).
"""
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
