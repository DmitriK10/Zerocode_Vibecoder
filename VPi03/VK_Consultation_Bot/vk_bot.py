import logging
from datetime import datetime
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text
from appointment_manager import AppointmentManager
from ai_client import AIClient

logger = logging.getLogger(__name__)

class VKBot:
    def __init__(self, token: str, ai_client: AIClient, app_manager: AppointmentManager):
        self.bot = Bot(token=token)
        self.ai_client = ai_client
        self.app_manager = app_manager
        self._register_handlers()

    def _register_handlers(self):
        @self.bot.on.message(text="Начать")
        async def start_handler(message: Message):
            await self._handle_start(message)

        @self.bot.on.message(text=["Записаться на консультацию", "Записаться"])
        async def appointment_handler(message: Message):
            await self._handle_appointment(message)

        @self.bot.on.message(text="FAQ")
        async def faq_handler(message: Message):
            await self._handle_faq(message)

        @self.bot.on.message(text="Мои записи")
        async def my_appointments_handler(message: Message):
            await self._handle_my_appointments(message)

        @self.bot.on.message(text="Помощь")
        async def help_handler(message: Message):
            await self._handle_help(message)

        @self.bot.on.message()
        async def ai_response_handler(message: Message):
            await self._handle_ai_response(message)

    def _get_main_keyboard(self) -> Keyboard:
        return (
            Keyboard()
            .add(Text("Записаться на консультацию"), color=KeyboardButtonColor.PRIMARY)
            .row()
            .add(Text("FAQ"), color=KeyboardButtonColor.SECONDARY)
            .add(Text("Мои записи"), color=KeyboardButtonColor.SECONDARY)
            .row()
            .add(Text("Помощь"), color=KeyboardButtonColor.NEGATIVE)
        )

    async def _get_user_name(self, user_id: int) -> str:
        try:
            user_info = await self.bot.api.users.get(user_ids=[user_id])
            if user_info:
                return f"{user_info[0].first_name} {user_info[0].last_name}"
        except Exception as e:
            logger.error(f"Ошибка получения имени пользователя {user_id}: {e}")
        return "Пользователь"

    async def _handle_start(self, message: Message):
        user_name = await self._get_user_name(message.from_id)
        await message.answer(
            f"Привет, {user_name}! 👋\nЯ бот для записи на IT-консультации.\nВыбери действие:",
            keyboard=self._get_main_keyboard()
        )

    async def _handle_appointment(self, message: Message):
        await message.answer(
            "Для записи укажи тему консультации, дату и время (например, '2026-08-20 15:00') и контакт для связи (телефон или почта).\n"
            "Отправь сообщение в формате: Тема | Дата | Контакт",
            keyboard=self._get_main_keyboard()
        )

    async def _handle_faq(self, message: Message):
        faq_text = (
            "❓ Часто задаваемые вопросы:\n"
            "1. Как записаться? – Нажми 'Записаться на консультацию' и следуй инструкциям.\n"
            "2. Какие темы консультаций? – Разработка, карьера, архитектура, DevOps, и другое.\n"
            "3. Стоимость? – Первая консультация бесплатна, далее по тарифам.\n"
            "4. Как отменить запись? – Напиши нам в личные сообщения."
        )
        await message.answer(faq_text, keyboard=self._get_main_keyboard())

    async def _handle_my_appointments(self, message: Message):
        user_id = message.from_id
        appointments = self.app_manager.get_appointments_by_user(user_id)
        if not appointments:
            text = "У вас нет активных записей."
        else:
            text = "Ваши записи:\n"
            for app in appointments:
                text += f"🔹 {app['topic']} – {app['date_time']} (контакт: {app['contact']})\n"
        await message.answer(text, keyboard=self._get_main_keyboard())

    async def _handle_help(self, message: Message):
        help_text = (
            "Доступные команды:\n"
            "• Начать – главное меню\n"
            "• Записаться на консультацию – начать запись\n"
            "• FAQ – частые вопросы\n"
            "• Мои записи – посмотреть свои заявки\n"
            "• Помощь – это сообщение"
        )
        await message.answer(help_text, keyboard=self._get_main_keyboard())

    async def _handle_ai_response(self, message: Message):
        user_text = message.text.strip()

        # Проверка на создание записи через формат "Тема | Дата | Контакт"
        if "|" in user_text:
            parts = [p.strip() for p in user_text.split("|") if p.strip()]
            if len(parts) >= 3:
                topic, date_time, contact = parts[0], parts[1], parts[2]

                # Простая проверка формата даты (YYYY-MM-DD HH:MM)
                try:
                    datetime.strptime(date_time, "%Y-%m-%d %H:%M")
                except ValueError:
                    await message.answer(
                        "⚠️ Неверный формат даты. Используйте: 'ГГГГ-ММ-ДД ЧЧ:ММ' (например, 2026-08-20 15:00).\n"
                        "Попробуйте снова в формате: Тема | Дата | Контакт",
                        keyboard=self._get_main_keyboard()
                    )
                    return

                user_name = await self._get_user_name(message.from_id)
                record = self.app_manager.create_appointment(
                    user_id=message.from_id,
                    user_name=user_name,
                    topic=topic,
                    date_time=date_time,
                    contact=contact
                )
                await message.answer(
                    f"✅ Запись создана!\nТема: {topic}\nДата: {date_time}\nКонтакт: {contact}\nНомер заявки: {record['id']}",
                    keyboard=self._get_main_keyboard()
                )
                return
            else:
                await message.answer(
                    "⚠️ Недостаточно данных. Отправьте в формате: Тема | Дата (ГГГГ-ММ-ДД ЧЧ:ММ) | Контакт",
                    keyboard=self._get_main_keyboard()
                )
                return

        # Обычный запрос к AI
        response = await self.ai_client.generate_response(user_text)
        if response:
            await message.answer(response, keyboard=self._get_main_keyboard())
        else:
            logger.warning(f"AI вернул пустой ответ для сообщения: {user_text[:50]}...")
            await message.answer(
                "Извините, произошла ошибка при обращении к AI. Попробуйте позже.",
                keyboard=self._get_main_keyboard()
            )

    async def run(self):
        await self.bot.run_polling()