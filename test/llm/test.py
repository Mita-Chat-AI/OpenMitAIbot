


from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_openai import ChatOpenAI
from pymongo import MongoClient

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
