import logging
import uuid
from typing import List, Dict, Any, Optional

import chromadb
import openai

from config import Config

logger = logging.getLogger(__name__)


class VectorMemoryManager:
    """
    Управляет долгой памятью (векторная БД Chroma).
    Использует OpenAI Embeddings для преобразования текста в векторы.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        embed_model: str,
        db_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 100,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.embed_model = embed_model
        self.db_path = db_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size

        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="long_memory",
            metadata={"hnsw:space": "cosine"}
        )

    def _chunk_text(self, text: str) -> List[str]:
        """Разбивает текст на чанки с перекрытием."""
        if not text:
            return []
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == text_len:
                break
            start = max(0, end - self.chunk_overlap)
        return chunks

    def _get_embeddings_batched(self, texts: List[str]) -> List[List[float]]:
        """
        Получает эмбеддинги для списка текстов с батчированием.
        """
        if not texts:
            return []
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.embed_model,
                    input=batch
                )
                all_embeddings.extend([item.embedding for item in response.data])
            except Exception as e:
                logger.error(f"Ошибка получения эмбеддингов для батча: {e}")
                raise
        return all_embeddings

    def add_document(self, user_id: int, text: str, doc_id: Optional[str] = None) -> int:
        """
        Индексирует документ в векторную базу.
        Возвращает количество добавленных чанков.
        """
        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        embeddings = self._get_embeddings_batched(chunks)

        if doc_id is None:
            doc_id = uuid.uuid4().hex

        ids = [f"{user_id}:{doc_id}:{i}:{uuid.uuid4().hex}" for i in range(len(chunks))]
        metadatas = [{"user_id": str(user_id), "doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=chunks
        )
        return len(chunks)

    def retrieve_context(self, user_id: int, query: str, top_k: int = 5) -> List[str]:
        """Ищет релевантные фрагменты документов."""
        if not query.strip():
            return []

        query_embedding = self._get_embeddings_batched([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"user_id": str(user_id)}
        )

        documents = results.get('documents', [[]])
        return documents[0] if documents else []

    def clear_user_data(self, user_id: int):
        """Удаляет все документы пользователя из векторной базы."""
        # Chroma позволяет удалять по where-условию
        try:
            self.collection.delete(where={"user_id": str(user_id)})
            logger.info(f"Удалены все записи для пользователя {user_id} из векторной БД")
        except Exception as e:
            logger.error(f"Ошибка удаления данных пользователя {user_id} из Chroma: {e}")
            raise