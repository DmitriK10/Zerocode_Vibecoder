import hashlib
from haystack import Document
from config import PINECONE_NAMESPACE_MESSAGES, TOP_K_RESULTS
from .pinecone_helpers import upsert_documents, query_pinecone
from .embedder import get_embedder

class MessageContextManager:
    def __init__(self):
        self.embedder = get_embedder()
        self.namespace = PINECONE_NAMESPACE_MESSAGES
        self.top_k = TOP_K_RESULTS

    def _get_embedding(self, text: str):
        return self.embedder.run(text=text)["embedding"]

    def save_user_message(self, user_id: int, text: str):
        embedding = self._get_embedding(text)
        doc_id = f"user_{user_id}_{hashlib.md5(text.encode()).hexdigest()[:8]}"
        doc = Document(
            id=doc_id,
            content=text,
            embedding=embedding,
            meta={"user_id": user_id, "type": "user_message", "text": text}
        )
        upsert_documents([doc], namespace=self.namespace)

    def retrieve_context(self, user_id: int, query: str) -> list[str]:
        query_embedding = self._get_embedding(query)
        filters = {"user_id": user_id, "type": "user_message"}
        docs = query_pinecone(query_embedding, namespace=self.namespace, top_k=self.top_k, filters=filters)
        return [doc.content for doc in docs]

    def clear_user_messages(self, user_id: int):
        from .pinecone_helpers import pinecone_index
        pinecone_index.delete(filter={"user_id": user_id}, namespace=self.namespace)