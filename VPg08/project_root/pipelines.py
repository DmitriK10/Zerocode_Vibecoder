import logging
from typing import List, Optional

from haystack import Pipeline, Document
from haystack.utils import Secret
from haystack_integrations.document_stores.pinecone import PineconeDocumentStore
from haystack_integrations.components.retrievers.pinecone import PineconeEmbeddingRetriever
from haystack.components.embedders import OpenAITextEmbedder, OpenAIDocumentEmbedder
from haystack.components.generators import OpenAIGenerator
from haystack.components.builders import PromptBuilder
from haystack.components.writers import DocumentWriter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import Config
from prompts import SUMMARIZATION_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class DocumentStoreFactory:
    """Фабрика для создания экземпляра PineconeDocumentStore."""

    @staticmethod
    def create(config: Config) -> PineconeDocumentStore:
        """
        Создаёт PineconeDocumentStore с использованием api_key и имени индекса.

        :param config: объект конфигурации.
        :return: экземпляр PineconeDocumentStore.
        """
        return PineconeDocumentStore(
            api_key=Secret.from_token(config.PINECONE_API_KEY),
            index=config.PINECONE_INDEX_NAME,
        )


class IndexingPipeline:
    """
    Пайплайн для индексации документов в Pinecone.
    Преобразует текст в векторное представление с помощью OpenAI и сохраняет в хранилище.
    """

    def __init__(self, document_store: PineconeDocumentStore, config: Config):
        """
        Инициализирует пайплайн индексации.

        :param document_store: хранилище Pinecone.
        :param config: объект конфигурации.
        """
        self.document_store = document_store
        self.config = config
        self.pipeline = self._build()

    def _build(self) -> Pipeline:
        """Строит и возвращает пайплайн Haystack."""
        pipeline = Pipeline()
        embedder = OpenAIDocumentEmbedder(
            api_key=Secret.from_token(self.config.OPENAI_API_KEY),
            api_base_url=self.config.OPENAI_BASE_URL,
            model=self.config.EMBEDDING_MODEL,
        )
        writer = DocumentWriter(document_store=self.document_store)
        pipeline.add_component("embedder", embedder)
        pipeline.add_component("writer", writer)
        pipeline.connect("embedder.documents", "writer.documents")
        return pipeline

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type(Exception))
    def run(self, documents: List[Document]) -> None:
        """
        Запускает индексацию переданных документов.

        :param documents: список документов для индексации.
        :raises Exception: в случае ошибки индексации (будет повторно вызвано).
        """
        if not documents:
            return
        logger.info(f"Indexing {len(documents)} documents")
        self.pipeline.run({"embedder": {"documents": documents}})


class QueryPipeline:
    """
    Пайплайн для поиска релевантных документов по текстовому запросу.
    Использует векторное сходство в Pinecone.
    """

    def __init__(self, document_store: PineconeDocumentStore, config: Config):
        """
        Инициализирует пайплайн поиска.

        :param document_store: хранилище Pinecone.
        :param config: объект конфигурации.
        """
        self.document_store = document_store
        self.config = config
        self.pipeline = self._build()

    def _build(self) -> Pipeline:
        """Строит и возвращает пайплайн Haystack."""
        pipeline = Pipeline()
        text_embedder = OpenAITextEmbedder(
            api_key=Secret.from_token(self.config.OPENAI_API_KEY),
            api_base_url=self.config.OPENAI_BASE_URL,
            model=self.config.EMBEDDING_MODEL,
        )
        retriever = PineconeEmbeddingRetriever(
            document_store=self.document_store,
            top_k=50,
        )
        pipeline.add_component("text_embedder", text_embedder)
        pipeline.add_component("retriever", retriever)
        pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        return pipeline

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type(Exception))
    def run(self, query: str, filters: Optional[dict] = None) -> List[Document]:
        """
        Выполняет поиск по запросу с применением фильтров.

        :param query: текстовый запрос.
        :param filters: структурированный фильтр для Pinecone (опционально).
        :return: список найденных документов.
        :raises Exception: в случае ошибки поиска (будет повторно вызвано).
        """
        run_params = {"text_embedder": {"text": query}}
        if filters:
            run_params["retriever"] = {"filters": filters}
        result = self.pipeline.run(run_params)
        return result.get("retriever", {}).get("documents", [])


class SummarizationPipeline:
    """
    Пайплайн для генерации резюме диалога на основе набора документов.
    Использует OpenAI для генерации текста.
    """

    def __init__(self, config: Config):
        """
        Инициализирует пайплайн суммаризации.

        :param config: объект конфигурации.
        """
        self.config = config
        self.pipeline = self._build()

    def _build(self) -> Pipeline:
        """Строит и возвращает пайплайн Haystack."""
        pipeline = Pipeline()
        prompt_builder = PromptBuilder(template=SUMMARIZATION_PROMPT_TEMPLATE)
        generator = OpenAIGenerator(
            api_key=Secret.from_token(self.config.OPENAI_API_KEY),
            api_base_url=self.config.OPENAI_BASE_URL,
            model=self.config.OPENAI_MODEL,
        )
        pipeline.add_component("prompt_builder", prompt_builder)
        pipeline.add_component("generator", generator)
        pipeline.connect("prompt_builder.prompt", "generator.prompt")
        return pipeline

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type(Exception))
    def run(self, documents: List[Document]) -> str:
        """
        Генерирует резюме на основе переданных документов.

        :param documents: список документов диалога.
        :return: строка с резюме.
        :raises Exception: в случае ошибки генерации (будет повторно вызвано).
        """
        if not documents:
            return "Нет документов для резюмирования."
        result = self.pipeline.run({
            "prompt_builder": {"documents": documents}
        })
        replies = result.get("generator", {}).get("replies", [])
        return replies[0] if replies else "Не удалось сгенерировать резюме."