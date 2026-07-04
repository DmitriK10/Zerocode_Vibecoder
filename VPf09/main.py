import asyncio
import logging
import json
import os
import tempfile
from typing import Dict, Any, Callable, Awaitable
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from openai import OpenAI

from config import Config
from memory import Memory
from utils import calculate_cost, generate_image, retry

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotApp:
    """
    Основной класс приложения. Внедряет зависимости через конструктор.
    """
    def __init__(
        self,
        memory: Memory,
        openai_client: OpenAI,
        image_generator: Callable[[str, int, int], Awaitable[bytes]],
        prompts: Dict[str, Any],
        default_prompt: str
    ):
        self.memory = memory
        self.openai_client = openai_client
        self.generate_image = image_generator
        self.prompts = prompts
        self.default_prompt = default_prompt
        self.user_modes: Dict[int, str] = {}
        self.bot = Bot(token=Config.BOT_TOKEN, base_url=Config.TELEGRAM_API_BASE_URL)
        self.dp = Dispatcher()
        self._register_handlers()

    def _register_handlers(self):
        """Регистрирует все обработчики команд и сообщений."""
        dp = self.dp
        bot_app = self  # для доступа из замыканий

        @dp.message(Command("start"))
        async def cmd_start(message: Message):
            await message.answer(
                "🤖 Привет! Я бот с подключенной LLM, генерацией изображений и памятью в SQLite.\n"
                "Команды:\n"
                "/mode – переключить роль\n"
                "/image <описание> – сгенерировать изображение\n"
                "/reset – очистить историю\n"
                "/help – помощь"
            )

        @dp.message(Command("help"))
        async def cmd_help(message: Message):
            await message.answer(
                "Доступные команды:\n"
                "/start – приветствие\n"
                "/mode – переключить роль\n"
                "/image <текст> – генерация изображения (бесплатно)\n"
                "/reset – очистить историю диалога\n"
                "/help – это сообщение"
            )

        @dp.message(Command("reset"))
        async def cmd_reset(message: Message):
            user_id = message.from_user.id
            bot_app.memory.clear(user_id)
            await message.answer("🧹 История диалога очищена.")

        @dp.message(Command("mode"))
        async def cmd_mode(message: Message):
            user_id = message.from_user.id
            current_mode = bot_app.user_modes.get(user_id, bot_app.default_prompt)

            builder = InlineKeyboardBuilder()
            for key, prompt in bot_app.prompts.items():
                label = prompt["name"]
                if key == current_mode:
                    label += " ✅"
                builder.button(text=label, callback_data=f"mode_{key}")
            builder.adjust(2)

            await message.answer(
                "Выберите режим:",
                reply_markup=builder.as_markup()
            )

        @dp.callback_query(lambda c: c.data and c.data.startswith("mode_"))
        async def process_mode_callback(callback_query: types.CallbackQuery):
            user_id = callback_query.from_user.id
            mode = callback_query.data.split("_")[1]
            if mode in bot_app.prompts:
                bot_app.user_modes[user_id] = mode
                await callback_query.answer(f"Режим переключён на '{bot_app.prompts[mode]['name']}'")
                await callback_query.message.edit_text(
                    f"Текущий режим: {bot_app.prompts[mode]['name']}\n"
                    f"Описание: {bot_app.prompts[mode]['description']}"
                )
            else:
                await callback_query.answer("Неизвестный режим", show_alert=True)

        @dp.message(Command("image"))
        async def cmd_image(message: Message):
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.answer("❌ Укажите описание изображения.\nПример: `/image красивый закат`")
                return

            prompt = args[1].strip()
            if not prompt:
                await message.answer("❌ Описание не может быть пустым.")
                return

            status_msg = await message.answer("🎨 Генерирую изображение, подождите...")
            try:
                image_bytes = await bot_app.generate_image(prompt)
                logger.debug(f"Получено {len(image_bytes)} байт изображения")
                if len(image_bytes) < 100:
                    raise ValueError(f"Изображение слишком маленькое ({len(image_bytes)} байт)")

                # Используем tempfile с автоматическим удалением
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(image_bytes)
                    temp_filename = tmp.name

                photo = FSInputFile(temp_filename)
                await bot_app.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo,
                    caption=f"🖼 Ваше изображение по запросу: {prompt}"
                )
                # Удаляем файл после отправки
                try:
                    os.remove(temp_filename)
                except OSError as e:
                    logger.warning(f"Не удалось удалить временный файл {temp_filename}: {e}")
                await status_msg.delete()
            except Exception as e:
                logger.error(f"Ошибка генерации изображения: {e}")
                await status_msg.edit_text(f"❌ Не удалось сгенерировать изображение: {str(e)}")

        @dp.message()
        async def handle_message(message: Message):
            user_id = message.from_user.id
            user_text = message.text

            bot_app.memory.add_message(user_id, "user", user_text)
            system_prompt = bot_app._get_system_prompt(user_id)
            context = bot_app.memory.get_context(user_id)  # уже ограничен CONTEXT_LIMIT

            messages = [{"role": "system", "content": system_prompt}] + context

            @retry(max_attempts=3, delay=1.0)
            async def get_openai_response():
                return bot_app.openai_client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )

            try:
                response = await get_openai_response()
                assistant_reply = response.choices[0].message.content
                usage = response.usage

                bot_app.memory.add_message(user_id, "assistant", assistant_reply)

                cost_info = calculate_cost({
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                })
                logger.info(
                    f"Пользователь {user_id}: токены (вх/вых/общ) = {cost_info['input_tokens']}/{cost_info['output_tokens']}/{cost_info['total_tokens']}, "
                    f"стоимость ~ {cost_info['cost_usd']:.6f} USD ≈ {cost_info['cost_rub']:.2f} RUB"
                )

                reply_text = f"{assistant_reply}\n\n---\n💸 Стоимость: {cost_info['cost_rub']:.2f} RUB (токены: {cost_info['total_tokens']})"
                await message.answer(reply_text)

            except Exception as e:
                logger.error(f"Ошибка обработки сообщения от {user_id}: {e}")
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")

    def _get_system_prompt(self, user_id: int) -> str:
        mode = self.user_modes.get(user_id, self.default_prompt)
        return self.prompts[mode]["system_prompt"]

    async def start_polling(self):
        """Запускает поллинг бота."""
        await self.dp.start_polling(self.bot)


def load_prompts(file_path: str) -> tuple:
    """Загружает промпты из JSON и валидирует структуру."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Ошибка загрузки prompts.json: {e}")
        raise

    required_keys = {"default_prompt", "prompts"}
    if not required_keys.issubset(data.keys()):
        raise ValueError("prompts.json должен содержать ключи 'default_prompt' и 'prompts'")

    default = data["default_prompt"]
    prompts = data["prompts"]
    if default not in prompts:
        raise ValueError(f"default_prompt '{default}' отсутствует в списке prompts")

    for key, prompt in prompts.items():
        if not isinstance(prompt, dict):
            raise ValueError(f"Промпт '{key}' должен быть объектом")
        if "name" not in prompt or "system_prompt" not in prompt:
            raise ValueError(f"Промпт '{key}' должен содержать 'name' и 'system_prompt'")

    return default, prompts


async def main():
    Config.validate()

    # Загрузка промптов
    prompts_file = os.path.join(os.path.dirname(__file__), "prompts.json")
    default_prompt, prompts = load_prompts(prompts_file)

    # Инициализация зависимостей
    memory = Memory()
    openai_client = OpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL
    )

    # Создание приложения
    app = BotApp(
        memory=memory,
        openai_client=openai_client,
        image_generator=generate_image,
        prompts=prompts,
        default_prompt=default_prompt
    )

    logger.info("Бот запускается...")
    await app.start_polling()


if __name__ == "__main__":
    asyncio.run(main())