import time
import json
import hashlib
from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX, PINECONE_HOST
from haystack import Document

pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index(PINECONE_INDEX, host=PINECONE_HOST)

def _sanitize_metadata(meta: dict) -> dict:
    """
    Преобразует метаданные в допустимый для Pinecone формат.
    """
    cleaned = {}
    for key, value in meta.items():
        if key.startswith('_'):
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        elif isinstance(value, list):
            if all(isinstance(v, str) for v in value):
                cleaned[key] = value
            else:
                cleaned[key] = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, dict):
            cleaned[key] = json.dumps(value, ensure_ascii=False)
        else:
            cleaned[key] = str(value)
    return cleaned

def upsert_documents(docs: list[Document], namespace: str, max_retries: int = 3):
    """
    Сохраняет документы в Pinecone с повторными попытками при ошибках.
    """
    vectors = []
    for doc in docs:
        doc_id = doc.id or hashlib.md5(doc.content.encode()).hexdigest()[:16]
        meta = _sanitize_metadata(doc.meta or {})
        if 'text' not in meta:
            meta['text'] = doc.content[:1000]
        vectors.append((doc_id, doc.embedding, meta))

    for attempt in range(max_retries):
        try:
            pinecone_index.upsert(vectors=vectors, namespace=namespace)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            time.sleep(wait_time)

def query_pinecone(query_embedding: list[float], namespace: str, top_k: int = 5, filters: dict = None) -> list[Document]:
    results = pinecone_index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace=namespace,
        filter=filters,
        include_metadata=True
    )
    docs = []
    for match in results["matches"]:
        doc = Document(
            content=match["metadata"].get("text", ""),
            meta=match["metadata"],
            embedding=match.get("values")
        )
        docs.append(doc)
    return docs