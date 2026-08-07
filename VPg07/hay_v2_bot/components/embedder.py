from haystack.components.embedders import OpenAITextEmbedder
from haystack.utils import Secret
from config import OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL

def get_embedder():
    """Возвращает единый экземпляр OpenAITextEmbedder с таймаутами."""
    return OpenAITextEmbedder(
        model=EMBEDDING_MODEL,
        api_key=Secret.from_token(OPENAI_API_KEY),
        api_base_url=OPENAI_BASE_URL,
        timeout=60.0,
        max_retries=3,
    )