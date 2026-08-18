import time
import logging
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.exceptions import ApiError
from bot.config import get_config

logger = logging.getLogger(__name__)

class VKClient:
    """Клиент для работы с VK API и LongPoll."""

    def __init__(self):
        config = get_config()
        self.vk = vk_api.VkApi(token=config.VK_TOKEN)
        self.longpoll = VkLongPoll(self.vk)

    def send_message(self, user_id: int, message: str, keyboard=None):
        """Отправляет сообщение пользователю с обработкой ошибок."""
        try:
            self.vk.method(
                "messages.send",
                {
                    "user_id": user_id,
                    "message": message,
                    "random_id": 0,
                    "keyboard": keyboard.get_keyboard() if keyboard else None,
                },
            )
        except ApiError as e:
            logger.error(f"Ошибка VK API при отправке: {e}")

    def listen_events(self, handler):
        """Слушает события LongPoll и обрабатывает сообщения с автоматическим переподключением."""
        while True:
            try:
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        handler(event.user_id, event.text)
            except Exception as e:
                # Здесь мы ловим любую ошибку (включая разрыв соединения)
                logger.error(f"Ошибка LongPoll: {e}. Переподключение через 5 секунд...")
                time.sleep(5)
                continue