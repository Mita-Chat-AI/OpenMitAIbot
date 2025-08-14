


from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI


from pymongo import MongoClient

from pymongo import MongoClient
from langchain_core.messages import HumanMessage, AIMessage

class SingleDocChatHistory:
    def __init__(self, session_id, connection_string, db_name, collection_name):
        self.session_id = session_id
        self.client = MongoClient(connection_string)
        self.collection = self.client[db_name][collection_name]
        # создаём документ, если его нет
        self.collection.update_one(
            {"session_id": self.session_id},
            {"$setOnInsert": {"messages": []}},
            upsert=True
        )

    @property
    def messages(self):
        doc = self.collection.find_one({"session_id": self.session_id})
        return doc.get("messages", []) if doc else []

    # Этот метод ждёт LangChain
    def add_messages(self, messages):
        # messages — список HumanMessage или AIMessage
        for m in messages:
            if isinstance(m, HumanMessage):
                self.add_message({"type": "human", "content": m.content})
            elif isinstance(m, AIMessage):
                self.add_message({"type": "ai", "content": m.content})

    def add_message(self, message: dict):
        self.collection.update_one(
            {"session_id": self.session_id},
            {"$push": {"messages": message}}
        )

    def clear(self):
        self.collection.update_one(
            {"session_id": self.session_id},
            {"$set": {"messages": []}}
        )




prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

llm = ChatOpenAI(model="gemma-3n-e2b-it:2", base_url="http://192.168.1.106:1234/v1", api_key="lm-studio")

chain = prompt | llm

# Создаём объект истории явно
history = SingleDocChatHistory(
    session_id="12",
    connection_string="mongodb://localhost:27017/",
    db_name="miku",
    collection_name="chat_histories"
)

# Создаём цепочку с историей
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: history,
    input_messages_key="question",
    history_messages_key="history",
)

# Вызываем цепочку
result = chain_with_history.invoke({"question": "Привет! Напиши просто: 1"}, config={"configurable": {"session_id": "12"}})



# Можно вывести и ответ бота
print(result)
