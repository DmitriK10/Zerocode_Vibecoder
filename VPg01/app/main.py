import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.config import Config
from app.db import DatabaseManager
from app.memory import ShortTermMemory
from app.openai_client import OpenAIClient
from app.models import StructuredResponse

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MemoryBot:
    def __init__(
        self,
        token: str,
        openai_client: OpenAIClient,
        db_manager: DatabaseManager,
        max_history: int
    ):
        self.token = token
        self.openai = openai_client
        self.db = db_manager
        self.max_history = max_history
        self.memories: dict[int, ShortTermMemory] = {}

    def get_memory(self, user_id: int) -> ShortTermMemory:
        if user_id not in self.memories:
            self.memories[user_id] = ShortTermMemory(max_size=self.max_history)
        return self.memories[user_id]

    def build_system_prompt(self, user_id: int, history_text: str) -> str:
        theses = self.db.get_theses(user_id)
        theses_text = "\n".join(f"- {t}" for t in theses) if theses else "Нет сохранённых тезисов."
        return Config.SYSTEM_PROMPT_TEMPLATE.format(
            theses=theses_text,
            history=history_text
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        user_id = user.id
        user_message = update.message.text
        if not user_message:
            return

        logger.info("Получено сообщение от user_id=%d: %s", user_id, user_message[:50])

        memory = self.get_memory(user_id)
        history_messages = memory.get_messages()

        history_text = "\n".join(
            f"{'Пользователь' if msg['role'] == 'user' else 'Ассистент'}: {msg['content']}"
            for msg in history_messages[-5:]
        )
        system_prompt = self.build_system_prompt(user_id, history_text)

        memory.add_message("user", user_message)

        structured_response = self.openai.generate_response(
            system_prompt=system_prompt,
            user_message=user_message,
            history=history_messages
        )

        for thesis in structured_response.theses:
            if thesis.strip():
                self.db.save_thesis(user_id, thesis.strip())

        memory.add_message("assistant", structured_response.message)
        await update.message.reply_text(structured_response.message)
        logger.info("Сохранены тезисы для user_id=%d: %s", user_id, structured_response.theses)

    async def cmd_mytheses(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        theses = self.db.get_theses(user_id)
        if not theses:
            await update.message.reply_text("У вас пока нет сохранённых тезисов.")
            return
        text = "Ваши сохранённые тезисы:\n" + "\n".join(f"• {t}" for t in theses)
        await update.message.reply_text(text)

    async def cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        memory = self.get_memory(user_id)
        memory.clear()
        await update.message.reply_text("История диалога очищена (краткосрочная память сброшена).")

    async def cmd_reset_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        memory = self.get_memory(user_id)
        memory.clear()
        self.db.clear_theses(user_id)
        await update.message.reply_text("Вся память (история и тезисы) очищена.")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Привет! Я бот с долгосрочной памятью. "
            "Я запоминаю ключевые тезисы нашего разговора и использую их в ответах.\n\n"
            "Доступные команды:\n"
            "/mytheses – показать сохранённые тезисы\n"
            "/clear – очистить историю текущего диалога (краткосрочная память)\n"
            "/reset_all – очистить ВСЮ память (историю и тезисы)"
        )

    def run(self) -> None:
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("mytheses", self.cmd_mytheses))
        app.add_handler(CommandHandler("clear", self.cmd_clear))
        app.add_handler(CommandHandler("reset_all", self.cmd_reset_all))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        logger.info("Бот запущен...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    db = DatabaseManager(Config.DB_PATH)
    openai_client = OpenAIClient(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL,
        model=Config.OPENAI_MODEL,
        http_proxy=Config.HTTP_PROXY,
        https_proxy=Config.HTTPS_PROXY
    )

    bot = MemoryBot(
        token=Config.TELEGRAM_TOKEN,
        openai_client=openai_client,
        db_manager=db,
        max_history=Config.MAX_HISTORY_SIZE
    )
    bot.run()


if __name__ == "__main__":
    main()