from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from src.interfaces import ProjectRepositoryInterface, LLMAssistantInterface
from src.github_service import GitHubApiClient
import html

router = Router()

def escape_html(text: str) -> str:
    return html.escape(str(text))

class PortfolioBotHandlers:
    def __init__(self, 
                 repository: ProjectRepositoryInterface, 
                 ai_client: LLMAssistantInterface,
                 github_username: str = "DmitriK10"):
        self._repository = repository
        self._ai_client = ai_client
        self._github_client = GitHubApiClient(github_username)

    def register_handlers(self, router: Router):
        router.message.register(self.cmd_start, Command("start"))
        router.message.register(self.cmd_projects, Command("projects"))
        router.message.register(self.cmd_github, Command("github"))
        router.message.register(self.cmd_ask, Command("ask"))

    async def cmd_start(self, message: Message):
        text = (
            "👋 <b>Привет! Я бот-портфолио Дмитрия.</b>\n\n"
            "👇 <b>Доступные команды:</b>\n"
            "/projects — Мои ключевые проекты\n"
            "/github — Мои последние репозитории\n"
            "/ask — Кратко о моем опыте"
        )
        await message.answer(text, parse_mode="HTML")

    async def cmd_projects(self, message: Message):
        projects = self._repository.get_projects()
        if not projects:
            await message.answer("⚠️ Пока нет загруженных проектов.")
            return
        
        for proj in projects:
            stack_str = ", ".join([f"<code>{escape_html(s)}</code>" for s in proj.get("stack", [])])
            features_str = "\n".join([f"• {escape_html(f)}" for f in proj.get("features", [])])
            
            text = (
                f"🚀 <b>{escape_html(proj.get('title', 'Без названия'))}</b>\n"
                f"👤 <i>Роль: {escape_html(proj.get('role', 'Developer'))}</i>\n\n"
                f"📝 <b>Описание:</b>\n{escape_html(proj.get('description', ''))}\n\n"
                f"🛠 <b>Стек:</b> {stack_str}\n\n"
                f"⚡ <b>Ключевые фичи:</b>\n{features_str}\n\n"
                f"🔗 <a href=\"{escape_html(proj.get('link', '#'))}\">Открыть код на GitHub</a>\n"
                f"📊 <b>Статус:</b> {escape_html(proj.get('status', 'Неизвестно'))}"
            )
            await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

    async def cmd_github(self, message: Message):
        await message.answer("⏳ Запрашиваю актуальные данные с GitHub API...")
        repos = self._github_client.get_top_repos(limit=5)
        
        if not repos:
            await message.answer("⚠️ Не удалось получить данные с GitHub.")
            return
            
        text = "💻 <b>Мои актуальные репозитории на GitHub:</b>\n\n"
        for idx, repo in enumerate(repos, 1):
            text += (
                f"{idx}. <a href=\"{escape_html(repo['url'])}\">{escape_html(repo['name'])}</a>\n"
                f"   <i>{escape_html(repo['description'])}</i>\n"
                f"   🗣 <code>{escape_html(repo['language'])}</code> | ⭐️ {repo['stars']}\n\n"
            )
        text += f"👉 <a href=\"https://github.com/{self._github_client._username}\">Перейти в профиль</a>"
        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

    async def cmd_ask(self, message: Message):
        await message.answer("🧠 Анализирую данные из projects.json...")
        try:
            projects = self._repository.get_projects()
            
            # Формируем строгий контекст только из реальных данных
            projects_context = "\n".join([
                f"Проект: {p.get('title')}. Задача: {p.get('description')}. Стек: {', '.join(p.get('stack', []))}." 
                for p in projects
            ])
            
            # ЖЕСТКИЙ ПРОМПТ: запрещаем выдумывать
            prompt = (
                "Ты — это я, разработчик Дмитрий. Сформируй краткий, сухой и нейтральный ответ от первого лица "
                "о моем профессиональном опыте, основываясь СТРОГО и ТОЛЬКО на этом списке:\n\n"
                f"{projects_context}\n\n"
                "ЖЕСТКИЕ ПРАВИЛА:\n"
                "1. Начни ответ сразу с фразы 'Имею опыт:'.\n"
                "2. Используй краткий маркированный список (тире).\n"
                "3. ЗАПРЕЩЕНО добавлять любые технологии, задачи или фразы, которых нет в списке выше.\n"
                "4. ЗАПРЕЩЕНО использовать общие фразы, комплименты, воду или обращения 'Вы обладаете'.\n"
                "5. Отвечай максимально лаконично."
            )
            
            response = self._ai_client.ask(prompt)
            await message.answer(f"🤖 {response}")
            
        except Exception as e:
            await message.answer(f"⚠️ Ошибка при запросе к AI: {str(e)}")