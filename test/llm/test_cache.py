import hashlib
import json
import random
import time

from langchain.schema import BaseCache
from langchain_core.outputs.chat_generation import ChatGeneration
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pymongo import MongoClient


class MongoCache(BaseCache):
    def __init__(self, uri="mongodb://localhost:27017", db_name="chat_cache", collection="responses", max_variants=5):
        self.client = MongoClient(uri)
        self.collection = self.client[db_name][collection]
        self.max_variants = max_variants

    def _key(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()

    def lookup(self, prompt: str, llm_string: str | None = None):
        key = self._key(prompt)
        result = self.collection.find_one({"_id": key})
        if result:
            responses = json.loads(result["response"])
            if responses:
                chosen = random.choice(responses)
                return [ChatGeneration(**chosen)]
        return None

    def update(self, prompt: str, llm_string: str | None, response: list):
        key = self._key(prompt)
        # Сериализуем объекты ChatGeneration в JSON
        response_json = [gen.dict() if isinstance(gen, ChatGeneration) else str(gen) for gen in response]
        existing = self.collection.find_one({"_id": key})
        if existing:
            current = json.loads(existing["response"])
            # Добавляем новые варианты без дубликатов
            for r in response_json:
                if r not in current:
                    current.append(r)
            # Ограничиваем количество вариантов
            current = current[-self.max_variants:]
        else:
            current = response_json
        self.collection.update_one(
            {"_id": key},
            {"$set": {"response": json.dumps(current)}},
            upsert=True
        )

    def clear(self):
        self.collection.delete_many({})


# --- Пример запроса к LLM ---
prompt_template = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

# Модель с кэшем
llm_cached = ChatOpenAI(
    model="CrazyMita",
    api_key="lm-studio",
    base_url="http://hour-checking.gl.at.ply.gg:45843/v1",
    temperature=0.7,
    max_completion_tokens=1000,
    cache=MongoCache()
)

# Модель без кэша
llm_no_cache = ChatOpenAI(
    model="CrazyMita",
    api_key="lm-studio",
    base_url="http://hour-checking.gl.at.ply.gg:45843/v1",
    temperature=0.7,
    max_completion_tokens=1000,
    cache=None
)

chain_cached = prompt_template | llm_cached
chain_no_cache = prompt_template | llm_no_cache

question = "Привет, как твои дела?"

print("=== Тест с кэшем ===")
start = time.time()
for i in range(10):
    msg = chain_cached.invoke({"question": question, "history": []})
    print(f"[{i+1}] {msg.content}")
print("Время с кэшем:", time.time() - start)

print("\n=== Тест без кэша ===")
start = time.time()
for i in range(10):
    msg = chain_no_cache.invoke({"question": question, "history": []})
    print(f"[{i+1}] {msg.content}")
print("Время без кэша:", time.time() - start)
