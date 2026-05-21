"""Клавиатуры для бота (обычные и инлайн)."""
from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle import Callback

def main_keyboard() -> Keyboard:
    """Главная клавиатура с кнопками."""
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("Погода сейчас"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("Прогноз на 5 дней"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("Геолокация 🌍"), color=KeyboardButtonColor.POSITIVE)
    keyboard.row()
    keyboard.add(Text("Сравнить города"), color=KeyboardButtonColor.NEGATIVE)
    keyboard.add(Text("Расширенный режим"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("Мой город"), color=KeyboardButtonColor.PRIMARY)
    return keyboard

def cancel_keyboard() -> Keyboard:
    """Клавиатура для отмены действия."""
    keyboard = Keyboard(one_time=False)
    keyboard.add(Text("Отмена"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard