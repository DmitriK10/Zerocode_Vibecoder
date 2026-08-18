from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bot.constants import (
    BTN_CATALOG, BTN_PRICE, BTN_PORTFOLIO,
    BTN_CONTACT, BTN_ORDER, BTN_BACK
)

COLOR_PRIMARY = VkKeyboardColor.PRIMARY
COLOR_SECONDARY = VkKeyboardColor.SECONDARY
COLOR_POSITIVE = VkKeyboardColor.POSITIVE
COLOR_NEGATIVE = VkKeyboardColor.NEGATIVE

def main_menu_keyboard() -> VkKeyboard:
    """Клавиатура главного меню."""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_CATALOG, color=COLOR_PRIMARY)
    keyboard.add_button(BTN_PRICE, color=COLOR_PRIMARY)
    keyboard.add_line()
    keyboard.add_button(BTN_PORTFOLIO, color=COLOR_SECONDARY)
    keyboard.add_button(BTN_CONTACT, color=COLOR_POSITIVE)
    keyboard.add_line()
    keyboard.add_button(BTN_ORDER, color=COLOR_NEGATIVE)
    return keyboard

def back_keyboard() -> VkKeyboard:
    """Клавиатура с кнопкой возврата в меню."""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_BACK, color=COLOR_NEGATIVE)
    return keyboard

def contact_keyboard() -> VkKeyboard:
    """Клавиатура для контактов (только кнопка назад)."""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_BACK, color=COLOR_NEGATIVE)
    return keyboard