import pytest
from unittest.mock import MagicMock
from haystack.dataclasses import Document
from pipelines import QueryPipeline


class TestPipelines:
    """Набор тестов для пайплайнов."""

    def test_indexing_pipeline_run(self, indexing_pipeline):
        """Проверяет, что пайплайн индексации вызывает pipeline.run с правильными аргументами."""
        docs = [Document(content="test")]
        indexing_pipeline.pipeline = MagicMock()
        indexing_pipeline.run(docs)
        indexing_pipeline.pipeline.run.assert_called_once_with(
            {"embedder": {"documents": docs}}
        )

    def test_indexing_pipeline_empty_docs(self, indexing_pipeline):
        """Проверяет, что при пустом списке документов pipeline.run не вызывается."""
        indexing_pipeline.pipeline = MagicMock()
        indexing_pipeline.run([])
        indexing_pipeline.pipeline.run.assert_not_called()

    def test_query_pipeline_run_with_filters(self):
        """Проверяет, что метод run QueryPipeline вызывается с правильными параметрами (структурированный фильтр)."""
        qp = MagicMock(spec=QueryPipeline)
        qp.run.return_value = []
        expected_filters = {"field": "chat_id", "operator": "==", "value": 123}
        result = qp.run("query", filters=expected_filters)
        qp.run.assert_called_once_with("query", filters=expected_filters)
        assert result == []

    def test_query_pipeline_run_without_filters(self):
        """Проверяет, что метод run QueryPipeline работает без фильтров."""
        qp = MagicMock(spec=QueryPipeline)
        qp.run.return_value = []
        result = qp.run("query")
        qp.run.assert_called_once_with("query")  # filters не передаётся
        assert result == []

    def test_summarization_pipeline_run(self, summarization_pipeline):
        """Проверяет, что пайплайн суммаризации возвращает корректный результат."""
        summarization_pipeline.pipeline = MagicMock()
        summarization_pipeline.pipeline.run.return_value = {
            "generator": {"replies": ["summary"]}
        }
        docs = [Document(content="test")]
        result = summarization_pipeline.run(docs)
        assert result == "summary"
        summarization_pipeline.pipeline.run.assert_called_once_with({
            "prompt_builder": {"documents": docs}
        })

    def test_summarization_pipeline_empty_docs(self, summarization_pipeline):
        """Проверяет, что при пустом списке документов возвращается соответствующее сообщение."""
        result = summarization_pipeline.run([])
        assert result == "Нет документов для резюмирования."

    def test_summarization_pipeline_no_replies(self, summarization_pipeline):
        """Проверяет, что если генератор не вернул ответов, возвращается сообщение об ошибке."""
        summarization_pipeline.pipeline = MagicMock()
        summarization_pipeline.pipeline.run.return_value = {"generator": {"replies": []}}
        docs = [Document(content="test")]
        result = summarization_pipeline.run(docs)
        assert result == "Не удалось сгенерировать резюме."