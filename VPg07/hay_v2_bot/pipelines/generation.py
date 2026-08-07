from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from openai import OpenAI

def generate_response(query: str, context: list[str]) -> str:
    """Генерирует ответ на запрос с учётом контекста, используя OpenAI напрямую."""
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    context_str = "\n".join(context) if context else "Нет контекста."
    prompt = f"""
Ты — полезный ассистент. Отвечай на вопрос пользователя, используя предоставленный контекст.
Если контекст пуст, используй свои знания.

Контекст:
{context_str}

Вопрос: {query}
Ответ:
"""
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content