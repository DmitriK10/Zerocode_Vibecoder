import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(
    api_key=os.getenv("PROXY_API_KEY"),
    base_url="https://api.proxyapi.ru/anthropic"
)
try:
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Привет"}],
        max_tokens=100
    )
    print("Успех! Ответ:", response.content[0].text)
except Exception as e:
    print("Ошибка:", e)