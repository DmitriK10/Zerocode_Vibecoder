import pytest
from unittest.mock import MagicMock, patch
from bot.handlers import MessageHandler
from bot.config import Config, get_config

# Фикстура для подмены конфигурации (чтобы не зависеть от .env)
@pytest.fixture(autouse=True)
def mock_config():
    with patch('bot.handlers.get_config') as mock_get_config:
        mock_get_config.return_value = Config(
            VK_TOKEN="fake_token",
            DESIGNER_PHONE="+7-900-123-45-67",
            DESIGNER_EMAIL="designer@example.com",
            PORTFOLIO_LINK="https://www.behance.net/yourportfolio"
        )
        yield

@pytest.fixture
def mock_vk():
    return MagicMock()

@pytest.fixture
def handler(mock_vk):
    # Создаём обработчик и очищаем состояние перед каждым тестом
    handler = MessageHandler(mock_vk)
    handler.storage._awaiting_phone.clear()
    # Заменяем _save на пустую заглушку, чтобы не писать в файлы
    handler.storage._save = MagicMock()
    return handler

# Параметризованный тест для проверки нескольких команд
@pytest.mark.parametrize("command,expected", [
    ("каталог", "Мои услуги"),
    ("💰 Прайс-лист", "Прайс-лист"),
    ("портфолио", Config.PORTFOLIO_LINK),
])
def test_commands(handler, mock_vk, command, expected):
    """Проверяет, что команды 'каталог', 'прайс-лист', 'портфолио' вызывают соответствующие методы и отправляют правильные сообщения."""
    handler.handle(123, command)
    mock_vk.send_message.assert_called_once()
    msg = mock_vk.send_message.call_args[0][1]
    assert expected in msg

def test_welcome(handler, mock_vk):
    """Проверяет, что команда 'начать' отправляет приветственное сообщение и главное меню."""
    handler.handle(123, "начать")
    mock_vk.send_message.assert_called_once()
    args = mock_vk.send_message.call_args[0]
    assert args[0] == 123
    assert "помощник дизайнера" in args[1]

def test_catalog(handler, mock_vk):
    """Проверяет, что команда 'каталог' отправляет список услуг с описаниями."""
    handler.handle(123, "каталог")
    mock_vk.send_message.assert_called_once()
    msg = mock_vk.send_message.call_args[0][1]
    assert "Мои услуги" in msg
    assert "Фирменный стиль" in msg

def test_prices(handler, mock_vk):
    """Проверяет, что команда 'прайс' отправляет прайс-лист с ценами."""
    handler.handle(123, "прайс")
    mock_vk.send_message.assert_called_once()
    msg = mock_vk.send_message.call_args[0][1]
    assert "Прайс-лист" in msg
    assert "15 000 руб." in msg

def test_portfolio(handler, mock_vk):
    """Проверяет, что команда 'портфолио' отправляет ссылку на портфолио."""
    handler.handle(123, "портфолио")
    mock_vk.send_message.assert_called_once()
    msg = mock_vk.send_message.call_args[0][1]
    assert Config.PORTFOLIO_LINK in msg

def test_contacts(handler, mock_vk):
    """Проверяет, что команда 'связаться' отправляет контактные данные (телефон и email)."""
    handler.handle(123, "связаться")
    mock_vk.send_message.assert_called_once()
    msg = mock_vk.send_message.call_args[0][1]
    assert Config.DESIGNER_PHONE in msg
    assert Config.DESIGNER_EMAIL in msg

def test_lead_request(handler, mock_vk):
    """Проверяет, что команда 'заявка' переводит пользователя в состояние ожидания номера телефона и отправляет запрос."""
    handler.handle(123, "заявка")
    assert 123 in handler.storage._awaiting_phone
    mock_vk.send_message.assert_called_once()
    msg = mock_vk.send_message.call_args[0][1]
    assert "Оставьте свой номер" in msg

@patch("builtins.open", create=True)
def test_lead_save(mock_open, handler, mock_vk):
    """Проверяет, что после ввода номера телефона заявка сохраняется в файл leads.txt и пользователь получает подтверждение."""
    handler.storage.add_awaiting_phone(123)
    handler.handle(123, "+7 900 111 22 33")
    # Ищем вызов с нужными аргументами среди всех вызовов
    calls = [
        call for call in mock_open.call_args_list
        if call[0] == ("leads.txt", "a") and call[1] == {"encoding": "utf-8"}
    ]
    assert len(calls) == 1
    # Проверяем, что в файл записана правильная строка
    handle = mock_open.return_value.__enter__.return_value
    handle.write.assert_any_call("User ID: 123, Phone: +7 900 111 22 33\n")
    mock_vk.send_message.assert_called_once()
    msg = mock_vk.send_message.call_args[0][1]
    assert "Спасибо" in msg
    assert 123 not in handler.storage._awaiting_phone

def test_validation_fail(handler, mock_vk):
    """Проверяет, что при вводе некорректного номера телефона пользователь получает сообщение об ошибке и состояние не снимается."""
    handler.storage.add_awaiting_phone(123)
    handler.handle(123, "not a phone")
    mock_vk.send_message.assert_called_once()
    msg = mock_vk.send_message.call_args[0][1]
    assert "корректный номер" in msg
    assert 123 in handler.storage._awaiting_phone

def test_unknown(handler, mock_vk):
    """Проверяет, что при неизвестной команде отправляется сообщение об ошибке."""
    # Гарантируем, что пользователь не находится в состоянии ожидания
    handler.storage.remove_awaiting_phone(123)
    handler.handle(123, "что-то")
    mock_vk.send_message.assert_called_once()
    msg = mock_vk.send_message.call_args[0][1]
    assert "Я не понял команду" in msg