import unittest
from unittest.mock import patch, MagicMock
from haystack import Document
from components.pinecone_helpers import _sanitize_metadata, upsert_documents, query_pinecone

class TestPineconeHelpers(unittest.TestCase):
    def test_sanitize_metadata(self):
        # Тест очистки метаданных
        meta = {
            "_split_overlap": 5,
            "name": "test",
            "tags": ["a", "b"],
            "nested": {"key": "value"},
            "score": 10.5,
            "active": True,
            "none_value": None,
        }
        cleaned = _sanitize_metadata(meta)
        self.assertNotIn("_split_overlap", cleaned)
        self.assertEqual(cleaned["name"], "test")
        self.assertEqual(cleaned["tags"], ["a", "b"])
        self.assertEqual(cleaned["nested"], '{"key": "value"}')
        self.assertEqual(cleaned["score"], 10.5)
        self.assertEqual(cleaned["active"], True)
        self.assertEqual(cleaned["none_value"], "None")  # None преобразуется в строку

    @patch("components.pinecone_helpers.pinecone_index")
    def test_upsert_documents_success(self, mock_index):
        # Мокаем успешный upsert
        doc = Document(
            id="test_id",
            content="text",
            embedding=[0.1, 0.2],
            meta={"user": "alice"}
        )
        upsert_documents([doc], namespace="test_ns")
        mock_index.upsert.assert_called_once()
        args, kwargs = mock_index.upsert.call_args
        vectors = kwargs.get("vectors")
        self.assertEqual(len(vectors), 1)
        vector_id, embedding, meta = vectors[0]
        self.assertEqual(vector_id, "test_id")
        self.assertEqual(embedding, [0.1, 0.2])
        self.assertEqual(meta["user"], "alice")

    @patch("components.pinecone_helpers.pinecone_index")
    def test_upsert_documents_retry(self, mock_index):
        # Мокаем ошибку в первый раз, успех во второй
        mock_index.upsert.side_effect = [Exception("Temp error"), None]
        doc = Document(
            id="test_id",
            content="text",
            embedding=[0.1, 0.2],
            meta={}
        )
        upsert_documents([doc], namespace="test_ns", max_retries=2)
        self.assertEqual(mock_index.upsert.call_count, 2)

    @patch("components.pinecone_helpers.pinecone_index")
    def test_query_pinecone(self, mock_index):
        # Мокаем запрос
        mock_index.query.return_value = {
            "matches": [
                {
                    "id": "1",
                    "score": 0.9,
                    "metadata": {"text": "hello", "source": "file.pdf"},
                    "values": [0.1, 0.2]
                }
            ]
        }
        result = query_pinecone([0.1, 0.2], namespace="test_ns", top_k=1)
        self.assertEqual(len(result), 1)
        doc = result[0]
        self.assertEqual(doc.content, "hello")
        self.assertEqual(doc.meta["source"], "file.pdf")
        self.assertEqual(doc.embedding, [0.1, 0.2])