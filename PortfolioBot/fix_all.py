import os
from pathlib import Path

BASE = Path(r'C:\Users\ADATA\Documents\__Reps\Zerocoder_Vibecoder\PortfolioBot')

# 1. Создаем отсутствующий src/github_service.py
github_service = '''import httpx
from typing import List, Dict, Any

class GitHubApiClient:
    def __init__(self, username: str):
        self._username = username
        self._base_url = f\"https://api.github.com/users/{username}/repos\"
        self._client = httpx.Client(headers={\"User-Agent\": \"PortfolioBot/1.0\"}, timeout=10.0)

    def get_top_repos(self, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            params = {\"sort\": \"updated\", \"per_page\": limit, \"type\": \"owner\"}
            response = self._client.get(self._base_url, params=params)
            response.raise_for_status()
            
            repos = response.json()
            result = []
            for repo in repos:
                if repo.get(\"fork\"):
                    continue
                result.append({
                    \"name\": repo.get(\"name\"),
                    \"description\": repo.get(\"description\") or \"Описание отсутствует\",
                    \"url\": repo.get(\"html_url\"),
                    \"language\": repo.get(\"language\") or \"Python\",
                    \"stars\": repo.get(\"stargazers_count\", 0)
                })
            return result[:limit]
        except httpx.HTTPError:
            return []
'''
(BASE / 'src' / 'github_service.py').write_text(github_service, encoding='utf-8')

# 2. Исправляем main.py
main_py = '''import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Абсолютный путь к корню проекта
BASE_DIR = Path(r\"C:\\Users\\ADATA\\Documents\\__Reps\\Zerocoder_Vibecoder\\PortfolioBot\").resolve()
sys.path.append(str(BASE_DIR))

# 2. Загрузка переменных окружения из .env
load_dotenv(BASE_DIR / \".env\")

from aiogram import Bot, Dispatcher
from src.repository import JsonProjectRepository
from src.ai_service import ProxyOpenAIClient
from src.bot_handlers import PortfolioBotHandlers, router

async def main():
    json_path = BASE_DIR / \"projects.json\"
    repository = JsonProjectRepository(str(json_path))
    
    api_key = os.getenv(\"OPENAI_API_KEY\", \"dummy_key_for_local_run\")
    ai_client = ProxyOpenAIClient(api_key=api_key)
    
    handlers = PortfolioBotHandlers(repository, ai_client)
    handlers.register_handlers(router)
    
    bot_token = os.getenv(\"BOT_TOKEN\")
    if not bot_token:
        raise ValueError(\"Критическая ошибка: BOT_TOKEN не найден в .env\")
        
    print(f\"DEBUG: Инициализация бота с токеном: {repr(bot_token)}\")
    
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    
    print(\"✅ Бот успешно инициализирован! Запускаю polling...\")
    await dp.start_polling(bot)

if __name__ == \"__main__\":
    asyncio.run(main())
'''
(BASE / 'main.py').write_text(main_py, encoding='utf-8')

# 3. Исправляем test_network.py
test_network = '''import httpx

def check_proxy():
    proxy_url = \"http://proxyapi.ru:8080\"
    print(f\"Проверка доступности прокси: {proxy_url}...\")
    try:
        with httpx.Client(proxy=proxy_url, timeout=5.0) as client:
            response = client.get(\"http://google.com\")
            print(f\"✅ Прокси работает! Статус: {response.status_code}\")
    except Exception as e:
        print(f\"❌ Прокси НЕДОСТУПЕН: {e}\")

def check_direct():
    print(\"Проверка прямого доступа к api.openai.com...\")
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(\"https://api.openai.com/v1/models\", headers={\"Authorization\": \"Bearer test\"})
            print(f\"✅ Прямой доступ есть! Статус: {response.status_code} (401 - норма, значит сервер виден)\")
    except Exception as e:
        print(f\"❌ Прямой доступ заблокирован или отсутствует: {e}\")

if __name__ == \"__main__\":
    check_proxy()
    check_direct()
'''
(BASE / 'test_network.py').write_text(test_network, encoding='utf-8')

# 4. Исправляем projects.json (убираем пробелы в ключах)
projects_json = '''{
  \"projects\": [
    {
      \"title\": \"Zerocode_Vibecoder (Портфолио-хаб)\",
      \"role\": \"Fullstack Python Developer\",
      \"description\": \"Комплексное решение для презентации навыков. Связка из минималистичного сайта и Telegram-бота, работающих на единой базе данных.\",
      \"stack\": [\"Python\", \"Aiogram 3\", \"Flask\", \"HTML/CSS/JS\", \"LLM Integration\"],
      \"features\": [
        \"Единый source of truth (JSON) для сайта и бота\",
        \"Интеграция с LLM через корпоративный прокси\",
        \"Архитектура с соблюдением принципов SRP и DIP\",
        \"Адаптивная верстка с плавными анимациями\"
      ],
      \"link\": \"https://github.com/DmitriK10/Zerocode_Vibecoder\",
      \"status\": \"✅ Завершён и задеплоен\"
    },
    {
      \"title\": \"LeadSync: Telegram -> amoCRM\",
      \"role\": \"Backend / Integrations\",
      \"description\": \"Webhook-сервис для автоматизации отдела продаж. Мгновенная передача лидов из Telegram прямо в воронку amoCRM.\",
      \"stack\": [\"FastAPI\", \"PostgreSQL\", \"Redis\", \"amoCRM API v4\"],
      \"features\": [
        \"Обработка очередей с retry-механикой при сбоях API\",
        \"Двусторонняя синхронизация статусов сделок\",
        \"Защита от дублей и умный маппинг полей\"
      ],
      \"link\": \"https://github.com/DmitriK10/Zerocode_Vibecoder\",
      \"status\": \"✅ В проде\"
    },
    {
      \"title\": \"Marketplace Analytics Parser\",
      \"role\": \"Data Engineer\",
      \"description\": \"Асинхронный краулер для сбора аналитики с маркетплейсов. Парсит цены, остатки и отзывы с обходом базовых защит.\",
      \"stack\": [\"Asyncio\", \"aiohttp\", \"BeautifulSoup\", \"Pandas\"],
      \"features\": [
        \"Сбор 100k+ SKU за сессию без блокировок\",
        \"Автоматическое построение отчетов по динамике цен\",
        \"Экспорт в CSV для BI-систем\"
      ],
      \"link\": \"https://github.com/DmitriK10/Zerocode_Vibecoder\",
      \"status\": \"🚧 Активно дорабатывается\"
    }
  ]
}
'''
(BASE / 'projects.json').write_text(projects_json, encoding='utf-8')

# 5. Исправляем test_bot_handlers.py (убираем пробелы в тестовых данных)
test_handlers = '''import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message
from src.bot_handlers import PortfolioBotHandlers
from src.interfaces import ProjectRepositoryInterface, LLMAssistantInterface

class MockRepo(ProjectRepositoryInterface):
    def __init__(self, data):
        self._data = data
    def get_projects(self):
        return self._data

class MockAI(LLMAssistantInterface):
    def ask(self, prompt: str) -> str:
        return \"AI Mock Response\"

@pytest.fixture
def mock_message():
    msg = MagicMock(spec=Message)
    msg.answer = AsyncMock()
    return msg

@pytest.mark.asyncio
async def test_cmd_projects_empty(mock_message):
    repo = MockRepo([])
    ai = MockAI()
    handlers = PortfolioBotHandlers(repo, ai)
    
    await handlers.cmd_projects(mock_message)
    mock_message.answer.assert_called_once_with(\"⚠️ Пока нет загруженных проектов.\")

@pytest.mark.asyncio
async def test_cmd_projects_renders_markdown(mock_message):
    data = [{
        \"title\": \"Test Bot\", \"role\": \"Dev\", \"description\": \"Desc\", 
        \"stack\": [\"Python\"], \"features\": [\"Fast\"], \"link\": \"http://test\", \"status\": \"Done\"
    }]
    repo = MockRepo(data)
    ai = MockAI()
    handlers = PortfolioBotHandlers(repo, ai)
    
    await handlers.cmd_projects(mock_message)
    
    call_args = mock_message.answer.call_args
    assert call_args.kwargs[\"parse_mode\"] == \"Markdown\"
    assert \"Test Bot\" in call_args.args[0]
    assert \"\`Python\`\" in call_args.args[0]
'''
(BASE / 'tests' / 'test_bot_handlers.py').write_text(test_handlers, encoding='utf-8')

# 6. Исправляем test_repository.py (убираем жестко закодированный путь)
test_repo = '''import pytest
import json
from src.repository import JsonProjectRepository

@pytest.fixture
def temp_json_file(tmp_path):
    file_path = tmp_path / \"projects.json\"
    data = {
        \"projects\": [
            {\"title\": \"Test Project\", \"description\": \"A test description.\"}
        ]
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    return str(file_path)

def test_get_projects_success(temp_json_file):
    repo = JsonProjectRepository(temp_json_file)
    projects = repo.get_projects()
    assert len(projects) == 1
    assert projects[0][\"title\"] == \"Test Project\"

def test_get_projects_empty_file(tmp_path):
    file_path = tmp_path / \"empty.json\"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({}, f)
    repo = JsonProjectRepository(str(file_path))
    projects = repo.get_projects()
    assert projects == []

def test_get_projects_malformed_json(tmp_path):
    file_path = tmp_path / \"malformed.json\"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(\"not a json\")
    repo = JsonProjectRepository(str(file_path))
    projects = repo.get_projects()
    assert projects == []

def test_get_projects_file_not_found(tmp_path):
    non_existent = tmp_path / \"non_existent.json\"
    repo = JsonProjectRepository(str(non_existent))
    projects = repo.get_projects()
    assert projects == []
'''
(BASE / 'tests' / 'test_repository.py').write_text(test_repo, encoding='utf-8')

print('✅ Все файлы успешно исправлены!')
