import os
import time
from pinecone import Pinecone, ServerlessSpec
from haystack.components.embedders import OpenAITextEmbedder
from haystack.utils import Secret
from config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL,
    PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX,
    PINECONE_HOST, TOP_K_RESULTS
)

class ContextManager:
    def __init__(self):
        # Инициализация Pinecone через класс Pinecone
        self.pc = Pinecone(api_key=PINECONE_API_KEY)

        # Проверяем, существует ли индекс, если нет – создаём
        existing_indexes = self.pc.list_indexes().names()
        if PINECONE_INDEX not in existing_indexes:
            # Определяем облако и регион из environment
            if PINECONE_ENVIRONMENT.startswith('gcp-'):
                cloud = 'gcp'
                region = PINECONE_ENVIRONMENT.replace('gcp-', '')
            else:
                cloud = 'aws'
                region = PINECONE_ENVIRONMENT
            spec = ServerlessSpec(cloud=cloud, region=region)
            self.pc.create_index(
                name=PINECONE_INDEX,
                dimension=1536,   # для text-embedding-3-small
                metric='cosine',
                spec=spec,
                metadata_config={'indexed': ['user_id', 'type']}
            )
            # Ждём готовности индекса (несколько секунд)
            time.sleep(5)

        # Подключаемся к индексу
        if PINECONE_HOST:
            self.index = self.pc.Index(PINECONE_INDEX, host=PINECONE_HOST)
        else:
            self.index = self.pc.Index(PINECONE_INDEX)
        self.namespace = "user_messages"

        # Эмбеддер OpenAI (через прокси)
        self.embedder = OpenAITextEmbedder(
            model=EMBEDDING_MODEL,
            api_key=Secret.from_token(OPENAI_API_KEY),
            api_base_url=OPENAI_BASE_URL
        )

    def _get_embedding(self, text: str) -> list[float]:
        # В Haystack 3.0 OpenAITextEmbedder.run() принимает параметр 'text' (строка)
        result = self.embedder.run(text=text)
        # Возвращает словарь с ключом 'embedding' (один вектор)
        return result['embedding']

    def save_user_message(self, user_id: int, text: str):
        embedding = self._get_embedding(text)
        doc_id = f"user_{user_id}_{hash(text) % 1000000}"
        metadata = {"user_id": user_id, "type": "user_message", "text": text}
        self.index.upsert(
            vectors=[(doc_id, embedding, metadata)],
            namespace=self.namespace
        )

    def retrieve_context(self, user_id: int, query: str) -> list[str]:
        query_embedding = self._get_embedding(query)
        filter_dict = {"user_id": user_id, "type": "user_message"}
        results = self.index.query(
            vector=query_embedding,
            top_k=TOP_K_RESULTS,
            namespace=self.namespace,
            filter=filter_dict,
            include_metadata=True
        )
        return [match["metadata"]["text"] for match in results["matches"]]