import unittest
from unittest.mock import patch, MagicMock
from components.message_context import MessageContextManager
from haystack import Document

class TestMessageContext(unittest.TestCase):
    @patch("components.message_context.get_embedder")
    @patch("components.message_context.upsert_documents")
    def test_save_user_message(self, mock_upsert, mock_get_embedder):
        mock_embedder = MagicMock()
        mock_embedder.run.return_value = {"embedding": [0.1, 0.2]}
        mock_get_embedder.return_value = mock_embedder

        mgr = MessageContextManager()
        mgr.save_user_message(123, "hello")

        mock_upsert.assert_called_once()
        docs = mock_upsert.call_args[0][0]
        self.assertEqual(len(docs), 1)
        doc = docs[0]
        self.assertEqual(doc.content, "hello")
        self.assertEqual(doc.embedding, [0.1, 0.2])
        self.assertEqual(doc.meta["user_id"], 123)

    @patch("components.message_context.get_embedder")
    @patch("components.message_context.query_pinecone")
    def test_retrieve_context(self, mock_query, mock_get_embedder):
        mock_embedder = MagicMock()
        mock_embedder.run.return_value = {"embedding": [0.1, 0.2]}
        mock_get_embedder.return_value = mock_embedder

        mock_query.return_value = [
            Document(content="prev message", meta={"user_id": 123})
        ]

        mgr = MessageContextManager()
        result = mgr.retrieve_context(123, "query")
        self.assertEqual(result, ["prev message"])
        mock_query.assert_called_once()
        args, kwargs = mock_query.call_args
        self.assertEqual(kwargs["filters"], {"user_id": 123, "type": "user_message"})

    @patch("components.message_context.get_embedder")
    @patch("components.pinecone_helpers.pinecone_index")  # <-- ИСПРАВЛЕНО
    def test_clear_user_messages(self, mock_index, mock_get_embedder):
        mgr = MessageContextManager()
        mgr.clear_user_messages(123)
        mock_index.delete.assert_called_once_with(
            filter={"user_id": 123},
            namespace=mgr.namespace
        )