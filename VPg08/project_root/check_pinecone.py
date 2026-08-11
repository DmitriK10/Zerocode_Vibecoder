import os
from dotenv import load_dotenv
from haystack.utils import Secret
from haystack_integrations.document_stores.pinecone import PineconeDocumentStore

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

if not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
    print("Ошибка: переменные PINECONE_API_KEY и PINECONE_INDEX_NAME должны быть заданы в .env")
    exit(1)

doc_store = PineconeDocumentStore(
    api_key=Secret.from_token(PINECONE_API_KEY),
    index=PINECONE_INDEX_NAME,
)

try:
    all_docs = doc_store.filter_documents(filters={})
except Exception as e:
    print(f"Ошибка при получении документов: {e}")
    exit(1)

print(f"Всего документов в индексе: {len(all_docs)}")

print("\n=== Первые 5 документов ===")
for i, doc in enumerate(all_docs[:5]):
    print(f"\n--- Документ {i+1} ---")
    print(f"ID: {doc.id}")
    print(f"Content: {doc.content[:80]}...")
    print(f"Meta: {doc.meta}")
    print(f"Есть поле is_mention? {'is_mention' in doc.meta}")
    if 'is_mention' in doc.meta:
        print(f"is_mention = {doc.meta['is_mention']}")

mention_count = sum(1 for d in all_docs if d.meta.get('is_mention') is True)
no_mention_count = sum(1 for d in all_docs if not d.meta.get('is_mention', False))
print(f"\nДокументы с is_mention=True: {mention_count}")
print(f"Документы с is_mention=False: {no_mention_count}")
print(f"Документы без поля is_mention: {len(all_docs) - mention_count - no_mention_count}")