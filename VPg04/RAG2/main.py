"""
Модуль RAG-агента с подключением к Pinecone, обработкой URL и API-запросами.
Соблюдены принципы SRP и DIP: каждый класс отвечает за одну задачу,
зависимости внедряются через конструкторы.
"""

import os
import re
import warnings
from pathlib import Path
from typing import List

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain.agents import create_agent
from pinecone import Pinecone, ServerlessSpec

# Отключаем предупреждения о небезопасных HTTPS-запросах
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# --------------------------- Загрузка .env из папки проекта ---------------------------
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# --------------------------- Конфигурация ---------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://proxypi.ru/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")

# Проверка наличия обязательных переменных
if not all([OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME]):
    raise EnvironmentError(
        "Отсутствуют необходимые переменные окружения. Проверьте .env файл."
    )

# Очистка имени индекса
PINECONE_INDEX_NAME = PINECONE_INDEX_NAME.strip()
if len(PINECONE_INDEX_NAME) > 45:
    raise ValueError(f"Имя индекса '{PINECONE_INDEX_NAME}' длиннее 45 символов.")

# --------------------------- SRP: Классы ---------------------------

class EmbeddingProvider:
    """Провайдер эмбеддингов"""
    def __init__(self, api_key: str, base_url: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._embeddings = None

    def get_embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                model=self.model,
            )
        return self._embeddings


class VectorStoreManager:
    """Управление векторным хранилищем Pinecone"""
    def __init__(self, api_key: str, index_name: str, environment: str, embedding_provider: EmbeddingProvider):
        self.api_key = api_key
        self.index_name = index_name.strip()
        self.environment = environment
        self.embedding_provider = embedding_provider
        self._vector_store = None

    def _init_pinecone(self) -> Pinecone:
        pc = Pinecone(api_key=self.api_key)
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        if self.index_name not in existing_indexes:
            if len(self.index_name) > 45:
                raise ValueError(f"Имя индекса '{self.index_name}' слишком длинное (>45 символов).")
            pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=self.environment)
            )
            print(f"✅ Индекс '{self.index_name}' создан.")
        else:
            print(f"✅ Индекс '{self.index_name}' уже существует.")
        return pc

    def get_vector_store(self) -> PineconeVectorStore:
        if self._vector_store is None:
            pc = self._init_pinecone()
            index = pc.Index(self.index_name)
            embeddings = self.embedding_provider.get_embeddings()
            self._vector_store = PineconeVectorStore(
                index=index,
                embedding=embeddings,
                text_key="text"
            )
        return self._vector_store


class URLProcessor:
    """Обработка URL: загрузка, парсинг, разбиение на чанки (использует httpx)"""
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
            length_function=len,
        )
        # Создаём клиент httpx с отключённой проверкой SSL
        self.client = httpx.Client(verify=False, timeout=15.0)

    def fetch_and_chunk(self, url: str) -> List[Document]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            }
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator="\n", strip=True)
            text = re.sub(r"\n\s*\n", "\n\n", text)
            doc = Document(page_content=text, metadata={"source": url})
            chunks = self.splitter.split_documents([doc])
            return chunks
        except Exception as e:
            raise RuntimeError(f"Ошибка обработки URL {url}: {e}")


class Retriever:
    """Поиск релевантных документов в векторном хранилище"""
    def __init__(self, vector_store_manager: VectorStoreManager, k: int = 5):
        self.vector_store_manager = vector_store_manager
        self.k = k

    def retrieve(self, query: str) -> List[Document]:
        store = self.vector_store_manager.get_vector_store()
        docs = store.similarity_search(query, k=self.k)
        return docs


class Generator:
    """Генерация ответа на основе найденных документов и запроса"""
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._llm = None

    def get_llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                model=self.model,
                temperature=0.3,
            )
        return self._llm

    def generate(self, query: str, context_docs: List[Document]) -> str:
        if not context_docs:
            return "Не найдено релевантных документов для ответа."
        context = "\n\n".join([doc.page_content for doc in context_docs])
        prompt = f"""
        Используй следующий контекст для ответа на вопрос. Если ответа нет в контексте, скажи об этом честно.
        Контекст:
        {context}

        Вопрос: {query}
        Ответ:
        """
        llm = self.get_llm()
        response = llm.invoke(prompt)
        return response.content


class APITool:
    """Реализация инструмента для внешних API-запросов (использует httpx)"""
    @staticmethod
    @tool(description="Возвращает случайный факт о котах")
    def get_cat_fact() -> str:
        try:
            with httpx.Client(verify=False, timeout=5.0) as client:
                response = client.get("https://catfact.ninja/fact")
                response.raise_for_status()
                data = response.json()
                return f"🐱 Факт о котах: {data.get('fact', 'Неизвестный факт')}"
        except Exception as e:
            return f"Не удалось получить факт о котах: {e}"


class RAGAgent:
    """
    Главный класс агента, объединяющий все компоненты.
    Следует DIP: зависимости внедряются через конструктор.
    """
    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        url_processor: URLProcessor,
        vector_store_manager: VectorStoreManager,
    ):
        self.retriever = retriever
        self.generator = generator
        self.url_processor = url_processor
        self.vector_store_manager = vector_store_manager
        self._agent = None

    def _build_agent(self):
        tools = [APITool.get_cat_fact]
        system_prompt = "Ты полезный ассистент. Используй инструменты, когда это необходимо."
        llm = self.generator.get_llm()
        self._agent = create_agent(llm, tools, system_prompt=system_prompt)

    def query(self, question: str, use_rag: bool = True) -> str:
        if use_rag:
            docs = self.retriever.retrieve(question)
            return self.generator.generate(question, docs)
        else:
            llm = self.generator.get_llm()
            response = llm.invoke(question)
            return response.content

    def add_url_to_knowledge(self, url: str) -> str:
        try:
            chunks = self.url_processor.fetch_and_chunk(url)
            if not chunks:
                return f"Не удалось извлечь текст из {url}."
            store = self.vector_store_manager.get_vector_store()
            store.add_documents(chunks)
            return f"Успешно добавлено {len(chunks)} чанков из {url}."
        except Exception as e:
            return f"Ошибка при добавлении URL: {e}"

    def run_agent_with_tool(self, user_input: str) -> str:
        if self._agent is None:
            self._build_agent()
        result = self._agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        messages = result["messages"]
        final_message = messages[-1]
        return final_message.content


# --------------------------- Точка входа для тестирования ---------------------------
if __name__ == "__main__":
    print("Инициализация RAG-агента...")

    embed_provider = EmbeddingProvider(OPENAI_API_KEY, OPENAI_BASE_URL)
    vector_manager = VectorStoreManager(
        api_key=PINECONE_API_KEY,
        index_name=PINECONE_INDEX_NAME,
        environment=PINECONE_ENVIRONMENT,
        embedding_provider=embed_provider
    )
    retriever = Retriever(vector_manager, k=5)
    generator = Generator(OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
    url_processor = URLProcessor()
    agent = RAGAgent(retriever, generator, url_processor, vector_manager)

    test_question = "Что такое RAG?"
    print(f"\nТестовый запрос: '{test_question}'")
    answer = agent.query(test_question, use_rag=True)
    print(f"Ответ: {answer}")

    test_url = "https://en.wikipedia.org/wiki/RAG"
    print(f"\nДобавление URL: {test_url}")
    result = agent.add_url_to_knowledge(test_url)
    print(result)

    print("\nПовторный запрос после добавления:")
    answer2 = agent.query(test_question, use_rag=True)
    print(f"Ответ: {answer2}")

    print("\nПроверка API-инструмента (случайный факт о котах):")
    tool_result = agent.run_agent_with_tool("Дай случайный факт о котах")
    print(tool_result)