import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    VK_TOKEN = os.getenv("VK_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")
    
    # Полный URL для эндпоинта chat completions
    OPENAI_CHAT_URL = f"{OPENAI_BASE_URL}/chat/completions"