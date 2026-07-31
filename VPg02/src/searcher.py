from typing import List, Dict
from embedding_service import EmbeddingService
from pinecone_service import PineconeService

class Searcher:
    def __init__(self, embedding_service: EmbeddingService, pinecone_service: PineconeService):
        self.embedding_service = embedding_service
        self.pinecone_service = pinecone_service

    def search(self, query_text: str, top_k: int = 5, filter_dict: Dict = None) -> List[Dict]:
        query_vector = self.embedding_service.get_embedding(query_text)
        return self.pinecone_service.query_vectors(query_vector, top_k=top_k, filter_dict=filter_dict)

    def print_results(self, results: List[Dict]) -> None:
        print("\nРезультаты поиска (отсортированы по убыванию релевантности):")
        for i, match in enumerate(results, 1):
            score = match.get('score', 0)
            metadata = match.get('metadata', {})
            text = metadata.get('text', 'Нет текста')
            category = metadata.get('category', 'без категории')
            print(f"{i}. ID: {match['id']} | Релевантность: {score:.4f}")
            print(f"   Текст: {text}")
            print(f"   Категория: {category}\n")