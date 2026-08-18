import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    VK_TOKEN: str
    DESIGNER_PHONE: str = "+7-900-123-45-67"
    DESIGNER_EMAIL: str = "designer@example.com"
    PORTFOLIO_LINK: str = "https://www.behance.net/yourportfolio"

def get_config() -> Config:
    """Загружает конфигурацию из .env и возвращает объект Config."""
    token = os.getenv("VK_TOKEN")
    if not token:
        raise ValueError("VK_TOKEN не задан в .env")
    return Config(
        VK_TOKEN=token,
        DESIGNER_PHONE=os.getenv("DESIGNER_PHONE", "+7-900-123-45-67"),
        DESIGNER_EMAIL=os.getenv("DESIGNER_EMAIL", "designer@example.com"),
        PORTFOLIO_LINK=os.getenv("PORTFOLIO_LINK", "https://www.behance.net/yourportfolio"),
    )