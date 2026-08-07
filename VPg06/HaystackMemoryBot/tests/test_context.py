import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from context_manager import ContextManager

class TestContextManager(unittest.TestCase):
    """Тесты для управления контекстом (Pinecone + эмбеддинги)."""

    @patch('context_manager.Pinecone')
    @patch('context_manager.OpenAITextEmbedder')
    def test_save_user_message(self, mock_embedder_cls, mock_pinecone_cls):
        """Проверяет сохранение сообщения пользователя в Pinecone с эмбеддингом."""
        print("\n🔍 Тест: сохранение сообщения пользователя в Pinecone")
        mock_pc = MagicMock()
        mock_pinecone_cls.return_value = mock_pc
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index

        mock_embedder = MagicMock()
        mock_embedder.run.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_embedder_cls.return_value = mock_embedder

        cm = ContextManager()
        cm.save_user_message(123, "Hello")

        mock_index.upsert.assert_called_once()
        call_args = mock_index.upsert.call_args[1]
        vectors = call_args['vectors']
        self.assertEqual(len(vectors), 1)
        doc_id, embedding, metadata = vectors[0]
        self.assertEqual(metadata["user_id"], 123)
        self.assertEqual(metadata["text"], "Hello")
        self.assertEqual(embedding, [0.1, 0.2, 0.3])
        print("✅ Сообщение сохранено с правильными метаданными и эмбеддингом")

    @patch('context_manager.Pinecone')
    @patch('context_manager.OpenAITextEmbedder')
    def test_retrieve_context(self, mock_embedder_cls, mock_pinecone_cls):
        """Проверяет поиск контекста по запросу с фильтром по user_id."""
        print("\n🔍 Тест: поиск контекста в Pinecone")
        mock_pc = MagicMock()
        mock_pinecone_cls.return_value = mock_pc
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index

        mock_embedder = MagicMock()
        mock_embedder.run.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_embedder_cls.return_value = mock_embedder

        mock_index.query.return_value = {
            "matches": [
                {"metadata": {"text": "Hello"}},
                {"metadata": {"text": "World"}}
            ]
        }

        cm = ContextManager()
        result = cm.retrieve_context(123, "test")

        self.assertEqual(result, ["Hello", "World"])
        mock_index.query.assert_called_once_with(
            vector=[0.1, 0.2, 0.3],
            top_k=5,
            namespace="user_messages",
            filter={"user_id": 123, "type": "user_message"},
            include_metadata=True
        )
        print("✅ Контекст найден и извлечён корректно")

if __name__ == '__main__':
    unittest.main()