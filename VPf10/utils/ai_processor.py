import json
import logging
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)

def get_llm_client():
    return OpenAI(api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL)

def process_dialog_with_ai(text: str, report_type: str) -> dict:
    """
    Отправляет текст диалога в LLM и возвращает структурированный JSON.
    report_type: 'client', 'design', 'product'
    """
    client = get_llm_client()

    # Системные промпты для каждого типа
    if report_type == 'client':
        system_prompt = """Ты — ассистент, который извлекает структурированную информацию из диалога с клиентом.
Извлеки следующие поля и верни их в формате JSON:
{
    "client_name": "имя клиента",
    "topic": "тема разговора",
    "main_request": "основной запрос клиента",
    "mood": "настроение клиента (позитивное/нейтральное/негативное)",
    "next_steps": "рекомендованные следующие шаги",
    "desired_timeline": "желаемые сроки",
    "budget": "стоимость/бюджет (если упоминается)",
    "key_features": "ключевые пожелания к продукту (список или строка)"
}
Если какое-то поле отсутствует, укажи пустую строку или null. Ответ должен быть только JSON, без лишнего текста."""
    elif report_type == 'design':
        system_prompt = """Ты — ассистент, который извлекает требования к дизайну сайта из диалога с клиентом.
Извлеки следующие поля и верни их в формате JSON:
{
    "client_name": "имя клиента",
    "project_description": "краткое описание проекта",
    "color_scheme": "предпочтительная цветовая гамма",
    "style": "стиль дизайна (например, минимализм, современный, классический)",
    "target_audience": "целевая аудитория",
    "image_prompt": "промпт для генерации изображения-примера дизайна (на основе требований)"
}
Если какое-то поле отсутствует, укажи пустую строку. Ответ должен быть только JSON."""
    elif report_type == 'product':
        system_prompt = """Ты — ассистент, который создает карточку товара для маркетплейса.
Из текста, содержащего название товара и его цену, сгенерируй реалистичное, детальное описание товара и промпт для генерации качественного изображения.

Требования к описанию:
- Укажи ключевые характеристики, типичные для данного типа товара (например, для велосипеда: возраст, вес, материал рамы, тип тормозов, колёса; для электроники: процессор, память, экран, батарея; для бытовой техники: мощность, функции).
- Описание должно быть объёмом 100–200 символов, информативным и привлекательным.

Требования к промпту для изображения:
- Промпт должен быть подробным, на английском языке (так как pollinations.ai лучше понимает английский).
- Укажи фон (белый, студийный), освещение (профессиональное, естественное), ракурс (спереди, сбоку, изометрия), детализацию (крупный план, изолированный объект).
- Добавь слова 'high quality', 'realistic', 'product photography', 'isolated on white background' для лучшего результата.

Верни ответ в формате JSON:
{
    "product_name": "название товара (извлеки из текста)",
    "price": "цена (извлеки из текста)",
    "description": "сгенерированное описание на русском языке",
    "image_prompt": "подробный промпт для генерации изображения на английском языке"
}
Ответ должен быть только JSON, без лишнего текста."""
    else:
        raise ValueError(f"Неизвестный тип отчёта: {report_type}")

    try:
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=Config.OPENAI_TEMPERATURE,
            max_tokens=1000
        )
        content = response.choices[0].message.content.strip()
        logger.debug(f"Ответ LLM: {content}")
        # Очистка от маркеров JSON
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        data = json.loads(content)
        return data
    except Exception as e:
        logger.error(f"Ошибка при обработке диалога: {e}")
        raise

def generate_product_card_data(product_name: str, price: str) -> dict:
    """Упрощённый вызов для карточки товара."""
    text = f"Название товара: {product_name}, Цена: {price}"
    return process_dialog_with_ai(text, 'product')