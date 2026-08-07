import unittest
from unittest.mock import patch, MagicMock
from bot.telegram_bot import index_document, generate_summary, search_documents
from haystack import Document

class TestTelegramBot(unittest.TestCase):
    @patch("bot.telegram_bot.DoclingConverterComponent")
    @patch("bot.telegram_bot.DocumentSplitter")
    @patch("bot.telegram_bot.OpenAI")
    @patch("bot.telegram_bot.upsert_documents")
    @patch("bot.telegram_bot.bot")  # мокаем bot для отправки сообщений
    def test_index_document(self, mock_bot, mock_upsert, mock_openai, mock_splitter, mock_converter):
        # Мокаем конвертер
        mock_converter_instance = MagicMock()
        mock_converter_instance.run.return_value = {
            "documents": [Document(content="Full text", meta={})]
        }
        mock_converter.return_value = mock_converter_instance

        # Мокаем сплиттер
        mock_splitter_instance = MagicMock()
        mock_splitter_instance.run.return_value = {
            "documents": [
                Document(content="chunk1", meta={}),
                Document(content="chunk2", meta={}),
            ]
        }
        mock_splitter.return_value = mock_splitter_instance

        # Мокаем OpenAI embeddings
        mock_client = MagicMock()
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [
            MagicMock(embedding=[0.1, 0.2]),
            MagicMock(embedding=[0.3, 0.4]),
        ]
        mock_client.embeddings.create.return_value = mock_embedding_response
        mock_openai.return_value = mock_client

        # Мокаем bot.send_message
        mock_bot.send_message = MagicMock()

        result = index_document("/fake/path.pdf", 12345)
        self.assertEqual(result, "Full text")

        # Проверяем, что upsert вызван
        mock_upsert.assert_called_once()
        # Проверяем, что сплиттер получил документ
        mock_splitter_instance.run.assert_called_once()
        # Проверяем, что эмбеддинги были установлены
        docs = mock_upsert.call_args[0][0]
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].embedding, [0.1, 0.2])
        self.assertEqual(docs[1].embedding, [0.3, 0.4])

    @patch("bot.telegram_bot.generate_response")
    def test_generate_summary(self, mock_generate):
        mock_generate.return_value = "Summary text"
        result = generate_summary("Some long text")
        self.assertEqual(result, "Summary text")
        mock_generate.assert_called_once()
        prompt = mock_generate.call_args[0][0]
        self.assertIn("Кратко опиши содержание", prompt)
        self.assertIn("Some long text", prompt)

    @patch("bot.telegram_bot.doc_embedder")
    @patch("bot.telegram_bot.query_pinecone")
    def test_search_documents(self, mock_query, mock_embedder):
        mock_embedder.run.return_value = {"embedding": [0.1, 0.2]}
        mock_query.return_value = [
            Document(content="doc1", meta={}),
            Document(content="doc2", meta={}),
        ]
        result = search_documents("test query")
        self.assertEqual(result, ["doc1", "doc2"])