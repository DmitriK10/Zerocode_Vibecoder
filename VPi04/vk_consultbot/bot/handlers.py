import re
import threading
from bot.catalog import Catalog
from bot.keyboards import main_menu_keyboard, back_keyboard, contact_keyboard
from bot.config import get_config
from bot.storage import FSMStorage
from bot.constants import (
    CMD_START, CMD_MENU, CMD_CATALOG, CMD_PRICE,
    CMD_PORTFOLIO, CMD_CONTACT, CMD_ORDER, CMD_BACK
)

LEAD_LOCK = threading.Lock()
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-()]{10,20}$")

class MessageHandler:
    """Обработчик сообщений с поддержкой состояний и валидацией."""

    def __init__(self, vk_client):
        self.vk = vk_client
        self.catalog = Catalog()
        self.storage = FSMStorage()
        self.config = get_config()

    def handle(self, user_id: int, text: str):
        """
        Обрабатывает входящее сообщение.

        Args:
            user_id: ID пользователя ВКонтакте.
            text: Текст сообщения.
        """
        text_lower = text.lower().strip()

        # Обработка состояния ожидания номера телефона
        if self.storage.is_awaiting_phone(user_id):
            if self._validate_phone(text):
                self._save_lead(user_id, text)
                self.storage.remove_awaiting_phone(user_id)
            else:
                self.vk.send_message(
                    user_id,
                    "❌ Пожалуйста, введите корректный номер телефона (например, +7 900 123-45-67)"
                )
            return

        # Основные команды
        if text_lower in CMD_START:
            self._send_welcome(user_id)
        elif text_lower in CMD_MENU:
            self._send_menu(user_id)
        elif text_lower in CMD_CATALOG:
            self._send_catalog(user_id)
        elif text_lower in CMD_PRICE:
            self._send_prices(user_id)
        elif text_lower in CMD_PORTFOLIO:
            self._send_portfolio(user_id)
        elif text_lower in CMD_CONTACT:
            self._send_contacts(user_id)
        elif text_lower in CMD_ORDER:
            self._ask_phone(user_id)
        elif text_lower == CMD_BACK:
            self._send_menu(user_id)
        else:
            self._send_unknown(user_id)

    def _validate_phone(self, phone: str) -> bool:
        """Проверяет, является ли строка допустимым номером телефона."""
        return bool(PHONE_REGEX.match(phone.strip()))

    def _send_welcome(self, user_id: int):
        msg = ("👋 Привет! Я бот-помощник дизайнера.\n"
               "Я покажу каталог услуг, прайс, портфолио и помогу связаться.\n"
               "Используй меню для навигации.")
        self.vk.send_message(user_id, msg, main_menu_keyboard())

    def _send_menu(self, user_id: int):
        self.vk.send_message(user_id, "Главное меню:", main_menu_keyboard())

    def _send_catalog(self, user_id: int):
        services = self.catalog.get_all()
        lines = ["📋 Мои услуги:\n"]
        for s in services:
            lines.append(f"• {s.name}\n  {s.description}")
        msg = "\n".join(lines)
        self.vk.send_message(user_id, msg, back_keyboard())

    def _send_prices(self, user_id: int):
        prices = self.catalog.get_prices()
        msg = "💰 Прайс-лист:\n" + "\n".join(prices)
        self.vk.send_message(user_id, msg, back_keyboard())

    def _send_portfolio(self, user_id: int):
        link = self.config.PORTFOLIO_LINK
        msg = f"🖼 Моё портфолио:\n{link}"
        self.vk.send_message(user_id, msg, back_keyboard())

    def _send_contacts(self, user_id: int):
        phone = self.config.DESIGNER_PHONE
        email = self.config.DESIGNER_EMAIL
        msg = f"📞 Телефон: {phone}\n📧 Email: {email}\n\nСвяжитесь со мной в любое время!"
        self.vk.send_message(user_id, msg, contact_keyboard())

    def _ask_phone(self, user_id: int):
        self.storage.add_awaiting_phone(user_id)
        msg = ("📝 Оставьте свой номер телефона в ответном сообщении,\n"
               "и я свяжусь с вами в ближайшее время.\n"
               "Пример: +7 900 123-45-67")
        self.vk.send_message(user_id, msg, None)

    def _save_lead(self, user_id: int, phone_text: str):
        """Сохраняет заявку в файл leads.txt с блокировкой."""
        with LEAD_LOCK:
            with open("leads.txt", "a", encoding="utf-8") as f:
                f.write(f"User ID: {user_id}, Phone: {phone_text}\n")
        self.vk.send_message(
            user_id,
            "✅ Спасибо! Я свяжусь с вами в ближайшее время.",
            main_menu_keyboard()
        )

    def _send_unknown(self, user_id: int):
        msg = "Я не понял команду. Используйте главное меню."
        self.vk.send_message(user_id, msg, main_menu_keyboard())