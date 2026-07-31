import os
import time
from typing import List, Dict, Any, Optional
from pinecone import Pinecone

class PineconeService:
    """
    Сервис для работы с векторной базой Pinecone (SDK версии 3.x).
    """

    def __init__(self, api_key: str = None, index_name: str = None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME", "nemo")

        if not self.api_key:
            raise ValueError("PINECONE_API_KEY не найден в переменных окружения")

        self.pc = Pinecone(api_key=self.api_key)
        self._index = None

    def connect_to_index(self, index_name: str = None) -> None:
        """
        Подключиться к существующему индексу.
        Индекс должен быть создан заранее в веб-интерфейсе Pinecone.
        """
        index_name = index_name or self.index_name
        existing_indexes = self.pc.list_indexes().names()
        if index_name not in existing_indexes:
            raise ValueError(
                f"Индекс '{index_name}' не существует. "
                "Пожалуйста, создайте его вручную через веб-интерфейс Pinecone "
                "с размерностью 1536 и метрикой cosine."
            )
        self._index = self.pc.Index(index_name)
        print(f"Подключен к индексу '{index_name}'")

    @property
    def index(self):
        if self._index is None:
            raise RuntimeError("Не подключен к индексу. Сначала вызовите connect_to_index()")
        return self._index

    def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not vectors:
            return {"upserted_count": 0}
        return self.index.upsert(vectors=vectors)

    def query_vectors(self, query_vector: List[float], top_k: int = 10, filter_dict: Optional[Dict] = None) -> List[Dict]:
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )
        return results['matches']

    def fetch_vectors(self, ids: List[str]) -> Dict[str, Any]:
        return self.index.fetch(ids=ids)

    def delete_vector(self, id: str) -> None:
        self.index.delete(ids=[id])

    def delete_all_vectors(self) -> None:
        self.index.delete(delete_all=True)

    def delete_index(self, index_name: str = None) -> None:
        index_name = index_name or self.index_name
        self.pc.delete_index(index_name)
        print(f"Индекс '{index_name}' удалён")