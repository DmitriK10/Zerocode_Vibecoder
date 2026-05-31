"""
Telegram-бот "Финансовый помощник для путешествий"
Использует API exchangerate.host для конвертации валют,
хранит данные в SQLite, поддерживает множественные путешествия.
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import os
import logging
from current_api import CurrencyAPI, get_currency_by_country
from database import Database

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

# Инициализация бота и зависимостей
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")

bot = telebot.TeleBot(TOKEN)
currency_api = CurrencyAPI()
db = Database()

# ---------- Вспомогательные функции ----------
def get_main_keyboard():
    """Главная клавиатура с кнопками (inline-меню)"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✈️ Создать путешествие", callback_data="new_trip"),
        InlineKeyboardButton("📋 Мои путешествия", callback_data="my_trips"),
        InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        InlineKeyboardButton("📜 История расходов", callback_data="history"),
        InlineKeyboardButton("🔄 Изменить курс", callback_data="set_rate")
    )
    return markup

def show_active_trip_info(user_id: int, chat_id: int):
    """Показать информацию об активном путешествии"""
    active = db.get_active_trip(user_id)
    if not active:
        bot.send_message(chat_id, "У вас нет активного путешествия. Создайте новое командой /newtrip или через меню.")
        return
    text = (f"🗺 *Активное путешествие:* {active['name']}\n"
            f"💱 {active['home_currency']} → {active['travel_currency']}  Курс: {active['exchange_rate']}\n"
            f"💰 Остаток: {active['home_balance']} {active['home_currency']} = "
            f"{active['travel_balance']} {active['travel_currency']}")
    bot.send_message(chat_id, text, parse_mode="Markdown")

# ---------- Обработчики команд ----------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    db.register_user(user_id)
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я финансовый помощник для путешествий.\n"
        "Я помогу вести бюджет в поездках, конвертировать валюты и отслеживать расходы.\n\n"
        "Используй меню ниже или команды:\n"
        "/newtrip - создать путешествие\n"
        "/switch - выбрать путешествие\n"
        "/balance - показать баланс\n"
        "/history - история расходов\n"
        "/setrate - изменить курс вручную",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(commands=['newtrip'])
def new_trip_command(message):
    user_id = message.from_user.id
    db.register_user(user_id)
    msg = bot.send_message(message.chat.id, "Введите название путешествия (например, 'Поездка в Париж'):")
    bot.register_next_step_handler(msg, process_trip_name, user_id)

def process_trip_name(message, user_id):
    trip_name = message.text.strip()
    if not trip_name:
        bot.send_message(message.chat.id, "Название не может быть пустым. Попробуйте снова /newtrip")
        return
    # Запрос страны отправления
    msg = bot.send_message(message.chat.id, "Введите страну отправления (например, Россия, США):")
    bot.register_next_step_handler(msg, process_home_country, user_id, trip_name)

def process_home_country(message, user_id, trip_name):
    home_country = message.text.strip()
    home_currency = get_currency_by_country(home_country)
    if not home_currency:
        # Если страна не найдена, просим вручную ввести код валюты
        msg = bot.send_message(message.chat.id, f"Не удалось определить валюту для '{home_country}'. Введите код валюты (например, RUB, USD):")
        bot.register_next_step_handler(msg, lambda m: process_home_currency_manual(m, user_id, trip_name, home_country))
        return
    # Запрос страны назначения
    msg = bot.send_message(message.chat.id, f"Валюта отправления: {home_currency}. Теперь введите страну назначения:")
    bot.register_next_step_handler(msg, process_travel_country, user_id, trip_name, home_currency)

def process_home_currency_manual(message, user_id, trip_name, home_country):
    home_currency = message.text.strip().upper()
    if len(home_currency) != 3:
        bot.send_message(message.chat.id, "Неверный код валюты. Используйте /newtrip для повторной попытки.")
        return
    msg = bot.send_message(message.chat.id, f"Валюта отправления: {home_currency}. Теперь введите страну назначения:")
    bot.register_next_step_handler(msg, process_travel_country, user_id, trip_name, home_currency)

def process_travel_country(message, user_id, trip_name, home_currency):
    travel_country = message.text.strip()
    travel_currency = get_currency_by_country(travel_country)
    if not travel_currency:
        msg = bot.send_message(message.chat.id, f"Не удалось определить валюту для '{travel_country}'. Введите код валюты назначения (например, EUR):")
        bot.register_next_step_handler(msg, lambda m: process_travel_currency_manual(m, user_id, trip_name, home_currency, travel_country))
        return
    # Получение курса через API
    try:
        rate = currency_api.get_exchange_rate(home_currency, travel_currency)
        bot.send_message(message.chat.id, f"Текущий курс: 1 {home_currency} = {rate} {travel_currency}")
        # Спрашиваем, устраивает ли курс
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Да", callback_data=f"rate_accept_{home_currency}_{travel_currency}_{rate}_{trip_name}"),
            InlineKeyboardButton("❌ Нет, введу вручную", callback_data=f"rate_manual_{home_currency}_{travel_currency}_{trip_name}")
        )
        bot.send_message(message.chat.id, "Этот курс подходит?", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ошибка получения курса: {e}")
        bot.send_message(message.chat.id, "Не удалось получить курс от API. Введите курс вручную (число):")
        bot.register_next_step_handler(message, lambda m: process_manual_rate(m, user_id, trip_name, home_currency, travel_currency))

def process_travel_currency_manual(message, user_id, trip_name, home_currency, travel_country):
    travel_currency = message.text.strip().upper()
    if len(travel_currency) != 3:
        bot.send_message(message.chat.id, "Неверный код валюты. Используйте /newtrip для повторной попытки.")
        return
    try:
        rate = currency_api.get_exchange_rate(home_currency, travel_currency)
        bot.send_message(message.chat.id, f"Текущий курс: 1 {home_currency} = {rate} {travel_currency}")
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Да", callback_data=f"rate_accept_{home_currency}_{travel_currency}_{rate}_{trip_name}"),
            InlineKeyboardButton("❌ Нет, введу вручную", callback_data=f"rate_manual_{home_currency}_{travel_currency}_{trip_name}")
        )
        bot.send_message(message.chat.id, "Этот курс подходит?", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ошибка получения курса: {e}")
        bot.send_message(message.chat.id, "Не удалось получить курс от API. Введите курс вручную (число):")
        bot.register_next_step_handler(message, lambda m: process_manual_rate(m, user_id, trip_name, home_currency, travel_currency))

def process_manual_rate(message, user_id, trip_name, home_currency, travel_currency):
    try:
        rate = float(message.text.replace(',', '.'))
        if rate <= 0:
            raise ValueError
        # Запрашиваем начальную сумму
        msg = bot.send_message(message.chat.id, f"Курс установлен: 1 {home_currency} = {rate} {travel_currency}\n"
                                               f"Введите начальную сумму в {home_currency}:")
        bot.register_next_step_handler(msg, lambda m: process_initial_amount(m, user_id, trip_name, home_currency, travel_currency, rate))
    except:
        bot.send_message(message.chat.id, "Некорректное число. Попробуйте снова /newtrip")

@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_accept_'))
def rate_accept_callback(call):
    _, _, home_curr, travel_curr, rate_str, trip_name = call.data.split('_', 5)
    rate = float(rate_str)
    msg = bot.send_message(call.message.chat.id, f"Курс подтверждён. Введите начальную сумму в {home_curr}:")
    bot.register_next_step_handler(msg, lambda m: process_initial_amount(m, call.from_user.id, trip_name, home_curr, travel_curr, rate))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_manual_'))
def rate_manual_callback(call):
    _, _, home_curr, travel_curr, trip_name = call.data.split('_', 4)
    msg = bot.send_message(call.message.chat.id, f"Введите желаемый курс (1 {home_curr} = X {travel_curr}):")
    bot.register_next_step_handler(msg, lambda m: process_manual_rate(m, call.from_user.id, trip_name, home_curr, travel_curr))
    bot.answer_callback_query(call.id)

def process_initial_amount(message, user_id, trip_name, home_currency, travel_currency, rate):
    try:
        amount_home = float(message.text.replace(',', '.'))
        if amount_home <= 0:
            raise ValueError
        # Конвертация в валюту назначения
        amount_travel = round(amount_home * rate, 2)
        # Создаём путешествие в БД
        trip_id = db.create_trip(
            user_id=user_id,
            name=trip_name,
            home_currency=home_currency,
            travel_currency=travel_currency,
            exchange_rate=rate,
            home_balance=amount_home,
            travel_balance=amount_travel
        )
        bot.send_message(message.chat.id, f"✅ Путешествие *{trip_name}* создано!\n"
                                         f"Начальный баланс: {amount_home} {home_currency} = {amount_travel} {travel_currency}",
                                         parse_mode="Markdown")
        # Показываем главное меню
        bot.send_message(message.chat.id, "Что делаем дальше?", reply_markup=get_main_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите положительное число. Попробуйте снова /newtrip")

@bot.message_handler(commands=['switch'])
def switch_trip(message):
    user_id = message.from_user.id
    trips = db.get_user_trips(user_id)
    if not trips:
        bot.send_message(message.chat.id, "У вас нет путешествий. Создайте командой /newtrip")
        return
    markup = InlineKeyboardMarkup(row_width=1)
    for trip in trips:
        markup.add(InlineKeyboardButton(trip['name'], callback_data=f"select_trip_{trip['id']}"))
    bot.send_message(message.chat.id, "Выберите путешествие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_trip_'))
def select_trip_callback(call):
    trip_id = int(call.data.split('_')[2])
    user_id = call.from_user.id
    db.set_active_trip(user_id, trip_id)
    trip = db.get_trip_by_id(trip_id)
    bot.answer_callback_query(call.id, f"Активно: {trip['name']}")
    bot.send_message(call.message.chat.id, f"Теперь активно путешествие *{trip['name']}*", parse_mode="Markdown")
    show_active_trip_info(user_id, call.message.chat.id)

@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = message.from_user.id
    active = db.get_active_trip(user_id)
    if not active:
        bot.send_message(message.chat.id, "Нет активного путешествия. Создайте /newtrip или выберите /switch")
    else:
        text = (f"🏦 *Баланс в путешествии {active['name']}*\n"
                f"{active['home_currency']}: {active['home_balance']}\n"
                f"{active['travel_currency']}: {active['travel_balance']}")
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['history'])
def history(message):
    user_id = message.from_user.id
    active = db.get_active_trip(user_id)
    if not active:
        bot.send_message(message.chat.id, "Нет активного путешествия.")
        return
    expenses = db.get_expenses(active['id'])
    if not expenses:
        bot.send_message(message.chat.id, "История расходов пуста.")
        return
    text = f"📜 *История расходов ({active['name']})*\n"
    for exp in expenses:
        text += f"• {exp['amount_travel']} {active['travel_currency']} = {exp['amount_home']} {active['home_currency']}  ({exp['created_at'][:16]})\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['setrate'])
def set_rate_command(message):
    user_id = message.from_user.id
    active = db.get_active_trip(user_id)
    if not active:
        bot.send_message(message.chat.id, "Нет активного путешествия.")
        return
    msg = bot.send_message(message.chat.id, f"Текущий курс: 1 {active['home_currency']} = {active['exchange_rate']} {active['travel_currency']}\nВведите новый курс (число):")
    bot.register_next_step_handler(msg, lambda m: update_rate(m, active['id']))

def update_rate(message, trip_id):
    try:
        new_rate = float(message.text.replace(',', '.'))
        if new_rate <= 0:
            raise ValueError
        db.update_exchange_rate(trip_id, new_rate)
        trip = db.get_trip_by_id(trip_id)
        # Пересчитываем travel_balance на основе home_balance и нового курса
        new_travel_balance = round(trip['home_balance'] * new_rate, 2)
        db.update_balances(trip_id, trip['home_balance'], new_travel_balance)
        bot.send_message(message.chat.id, f"Курс обновлён. Новый баланс: {trip['home_balance']} {trip['home_currency']} = {new_travel_balance} {trip['travel_currency']}")
    except:
        bot.send_message(message.chat.id, "Некорректное число. Курс не изменён.")

@bot.message_handler(func=lambda m: True)
def handle_expense(message):
    """Обработка сообщений с числом – воспринимаем как расход в валюте назначения"""
    user_id = message.from_user.id
    active = db.get_active_trip(user_id)
    if not active:
        bot.send_message(message.chat.id, "Нет активного путешествия. Используйте /newtrip или /switch")
        return
    try:
        amount_travel = float(message.text.replace(',', '.'))
        if amount_travel <= 0:
            raise ValueError
        # Конвертируем расход в домашнюю валюту
        amount_home = round(amount_travel / active['exchange_rate'], 2)
        # Предлагаем подтвердить расход
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_expense_{active['id']}_{amount_travel}_{amount_home}"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_expense")
        )
        bot.send_message(message.chat.id, f"Расход: {amount_travel} {active['travel_currency']} = {amount_home} {active['home_currency']}\nУчесть как расход?", reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число для расхода или используйте команды меню.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_expense_'))
def confirm_expense_callback(call):
    _, _, trip_id_str, amount_travel_str, amount_home_str = call.data.split('_')
    trip_id = int(trip_id_str)
    amount_travel = float(amount_travel_str)
    amount_home = float(amount_home_str)
    user_id = call.from_user.id
    # Получаем текущие балансы
    trip = db.get_trip_by_id(trip_id)
    if not trip:
        bot.answer_callback_query(call.id, "Путешествие не найдено")
        return
    new_home_balance = trip['home_balance'] - amount_home
    new_travel_balance = trip['travel_balance'] - amount_travel
    if new_home_balance < 0 or new_travel_balance < 0:
        bot.answer_callback_query(call.id, "Недостаточно средств! Расход не учтён.")
        return
    db.update_balances(trip_id, new_home_balance, new_travel_balance)
    db.add_expense(trip_id, amount_travel, amount_home, description="")
    bot.answer_callback_query(call.id, "Расход учтён ✅")
    bot.send_message(call.message.chat.id, f"Расход учтён. Остаток: {new_home_balance} {trip['home_currency']} = {new_travel_balance} {trip['travel_currency']}")

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_expense')
def cancel_expense_callback(call):
    bot.answer_callback_query(call.id, "Расход отменён")
    bot.send_message(call.message.chat.id, "Расход не учтён.")

# ---------- Обработчики inline-меню ----------
@bot.callback_query_handler(func=lambda call: call.data == "new_trip")
def inline_new_trip(call):
    new_trip_command(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "my_trips")
def inline_my_trips(call):
    user_id = call.from_user.id
    trips = db.get_user_trips(user_id)
    if not trips:
        bot.send_message(call.message.chat.id, "У вас нет путешествий. Создайте новое.")
    else:
        markup = InlineKeyboardMarkup(row_width=1)
        for trip in trips:
            markup.add(InlineKeyboardButton(trip['name'], callback_data=f"select_trip_{trip['id']}"))
        bot.send_message(call.message.chat.id, "Ваши путешествия:", reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "balance")
def inline_balance(call):
    balance(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "history")
def inline_history(call):
    history(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "set_rate")
def inline_set_rate(call):
    set_rate_command(call.message)
    bot.answer_callback_query(call.id)

# ---------- Запуск бота ----------
if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.infinity_polling()