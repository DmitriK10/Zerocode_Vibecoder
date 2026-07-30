import logging
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from app.config import Config
from app.openai_client import OpenAIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DoryBot:
    def __init__(self, token: str, openai_client: OpenAIClient, http_client: httpx.AsyncClient = None):
        self.token = token
        self.openai = openai_client
        self.http_client = http_client

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_message = update.message.text
        if not user_message:
            return
        system_prompt = "Ты полезный AI-ассистент. Отвечай по делу.\nОТВЕТ ДОЛЖЕН БЫТЬ В ФОРМАТЕ JSON: {\"theses\": [], \"message\": \"...\"}"
        response = self.openai.generate_response(
            system_prompt=system_prompt,
            user_message=user_message,
            history=None
        )
        await update.message.reply_text(response.message)

    def run(self):
        app = Application.builder().token(self.token).build()
        if self.http_client is not None:
            app.set_http_client(self.http_client)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.run_polling()