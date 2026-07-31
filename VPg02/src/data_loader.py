from typing import List, Dict, Any
from embedding_service import EmbeddingService
from pinecone_service import PineconeService

class DataLoader:
    def __init__(self, embedding_service: EmbeddingService, pinecone_service: PineconeService):
        self.embedding_service = embedding_service
        self.pinecone_service = pinecone_service

    def load_phrases(self, phrases: List[str], category: str = "auto", start_id: int = 1) -> None:
        vectors = []
        for idx, phrase in enumerate(phrases, start=start_id):
            vector_id = f"vec_{idx}"
            embedding = self.embedding_service.get_embedding(phrase)
            metadata = {
                "text": phrase,
                "category": category,
                "source": "manual"
            }
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            })
            print(f"Обработана фраза #{idx}: {phrase[:50]}...")
        result = self.pinecone_service.upsert_vectors(vectors)
        print(f"Загружено {result.get('upserted_count', 0)} векторов")