"""
Модуль управления векторной базой данных Pinecone.
Реализует запись, поиск, проверку на дубликаты через косинусное сходство.
"""

import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI


class PineconeManager:
    """
    Класс для операций с Pinecone: создание эмбеддингов, запись, поиск,
    автоматическая фильтрация дубликатов на основе косинусного сходства.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        openai_embedding_model: str = "text-embedding-3-small",
        similarity_threshold: float = 0.5,
    ):
        """
        Инициализация менеджера.

        Args:
            api_key: API ключ Pinecone (если None, берётся из .env)
            environment: Окружение Pinecone
            index_name: Имя индекса
            openai_api_key: API ключ OpenAI (или прокси)
            openai_base_url: Базовый URL для OpenAI (прокси)
            openai_embedding_model: Модель для эмбеддингов
            similarity_threshold: Порог косинусного сходства (0..1)
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME")
        self.similarity_threshold = similarity_threshold or float(
            os.getenv("SIMILARITY_THRESHOLD", "0.5")
        )

        if not self.api_key:
            raise ValueError("PINECONE_API_KEY не найден.")
        if not self.index_name:
            raise ValueError("PINECONE_INDEX_NAME не найден.")

        # Инициализация клиента Pinecone
        self.pc = Pinecone(api_key=self.api_key)

        # Инициализация OpenAI (с поддержкой base_url)
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_base_url = openai_base_url or os.getenv("OPENAI_BASE_URL")
        self.openai_embedding_model = openai_embedding_model

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY не найден.")

        self.openai_client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.openai_base_url or None,  # если None, используется стандартный
        )

        # Подключение к индексу
        self.index = self.pc.Index(self.index_name)

    def create_embedding(self, text: str) -> List[float]:
        """Создаёт эмбеддинг для текста через OpenAI."""
        response = self.openai_client.embeddings.create(
            model=self.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    def _check_similarity(self, vector: List[float]) -> Optional[Dict[str, Any]]:
        """
        Проверяет, есть ли в индексе вектор с косинусным сходством >= порога.
        Возвращает словарь с id и score, если найден, иначе None.
        """
        try:
            result = self.index.query(
                vector=vector,
                top_k=1,
                include_metadata=False,
            )
            if result.matches:
                best = result.matches[0]
                if best.score >= self.similarity_threshold:
                    return {"id": best.id, "score": best.score}
        except Exception as e:
            print(f"Ошибка при проверке сходства: {e}")
        return None

    def upsert_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        check_similarity: bool = True,
    ) -> Dict[str, Any]:
        """
        Запись вектора в Pinecone с проверкой на дубликаты.

        Args:
            vector_id: Уникальный ID вектора
            vector: Вектор (эмбеддинг)
            metadata: Метаданные (опционально)
            check_similarity: Проверять ли сходство перед записью

        Returns:
            Словарь с результатом:
            {
                'action': 'inserted' | 'updated' | 'skipped',
                'similarity_score': float | None,
                'existing_id': str | None
            }
        """
        metadata = metadata or {}
        result = {
            "action": "inserted",
            "similarity_score": None,
            "existing_id": None,
        }

        if check_similarity:
            similar = self._check_similarity(vector)
            if similar:
                existing_id = similar["id"]
                result["action"] = "updated"
                result["similarity_score"] = similar["score"]
                result["existing_id"] = existing_id

                # Обновляем существующий вектор (сохраняем тот же ID)
                self.index.upsert(
                    vectors=[
                        {
                            "id": existing_id,
                            "values": vector,
                            "metadata": metadata,
                        }
                    ]
                )
                return result

        # Нет дубликата — вставляем новый
        self.index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": vector,
                    "metadata": metadata,
                }
            ]
        )
        return result

    def upsert_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        check_similarity: bool = True,
    ) -> Dict[str, Any]:
        """
        Запись документа (текст преобразуется в эмбеддинг).
        """
        vector = self.create_embedding(text)
        return self.upsert_vector(doc_id, vector, metadata, check_similarity)

    def query_by_vector(
        self,
        vector: List[float],
        top_k: int = 5,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """Поиск по вектору."""
        result = self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=include_metadata,
        )
        return [{"id": m.id, "score": m.score, "metadata": m.metadata} for m in result.matches]

    def query_by_text(
        self,
        text: str,
        top_k: int = 5,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """Поиск по тексту (автоматически создаётся эмбеддинг)."""
        vector = self.create_embedding(text)
        return self.query_by_vector(vector, top_k, include_metadata)

    def fetch_vectors(self, ids: List[str]) -> Dict[str, Any]:
        """Получение векторов по ID."""
        return self.index.fetch(ids=ids)

    def delete_vector(self, vector_id: str) -> None:
        """Удаление вектора по ID."""
        self.index.delete(ids=[vector_id])

    def delete_by_filter(self, filter_dict: Dict[str, Any]) -> None:
        """Удаление по метаданным."""
        self.index.delete(filter=filter_dict)

    def delete_all(self) -> None:
        """Удаление всех векторов из индекса (осторожно!)."""
        self.index.delete(delete_all=True)

    def describe_index_stats(self) -> Dict[str, Any]:
        """Статистика индекса."""
        return self.index.describe_index_stats()

    def update_metadata(self, vector_id: str, metadata: Dict[str, Any]) -> None:
        """Обновление метаданных существующего вектора."""
        # Сначала получаем текущий вектор (values) и обновляем metadata
        fetch_result = self.index.fetch(ids=[vector_id])
        if vector_id in fetch_result.vectors:
            vec = fetch_result.vectors[vector_id]
            self.index.upsert(
                vectors=[
                    {
                        "id": vector_id,
                        "values": vec.values,
                        "metadata": metadata,
                    }
                ]
            )


# ============ Ручной тест (точка входа) ============
if __name__ == "__main__":
    # Этот блок выполняется при прямом запуске файла
    print("Тестирование PineconeManager...")
    try:
        manager = PineconeManager()
        stats = manager.describe_index_stats()
        print(f"Статистика индекса: {stats}")

        # Проверка записи и поиска
        test_text = "Привет, это тестовое сообщение."
        test_id = "test_001"
        result = manager.upsert_document(test_id, test_text)
        print(f"Результат записи: {result}")

        # Поиск
        results = manager.query_by_text("Привет", top_k=2)
        print(f"Результаты поиска: {results}")

        # Очистка
        manager.delete_vector(test_id)
        print("Тест завершён успешно.")
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")