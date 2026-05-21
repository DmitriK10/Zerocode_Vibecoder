"""Обработчики сообщений для VK бота."""
import asyncio
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, Text, KeyboardButtonColor
from vkbottle import PhotoMessageUploader

from config import Config
from openweather import OpenWeatherClient
from .keyboards import main_keyboard, cancel_keyboard
from utils import format_timestamp, kelvin_to_celsius, aqi_description

# Инициализация клиента OpenWeather
weather_client = OpenWeatherClient(Config.OPENWEATHER_API_KEY)

# Хранилище состояний пользователей и временных данных (в памяти)
user_states = {}      # user_id -> state ("waiting_city", "waiting_first_city", "waiting_second_city")
user_temp_data = {}   # user_id -> dict с временными данными (город для сравнения)

async def register_handlers(bot: Bot):
    """Регистрация всех хендлеров."""

    @bot.on.message(text=["Начать", "Старт", "/start"])
    async def start_handler(message: Message):
        """Приветственное сообщение и главное меню."""
        await message.answer(
            "Привет! Я погодный бот. Выберите действие:",
            keyboard=main_keyboard()
        )

    @bot.on.message(text="Погода сейчас")
    async def current_weather_prompt(message: Message):
        """Запрашиваем название города."""
        user_states[message.peer_id] = "waiting_city_current"
        await message.answer("Напишите название города:", keyboard=cancel_keyboard())

    @bot.on.message(text="Прогноз на 5 дней")
    async def forecast_prompt(message: Message):
        user_states[message.peer_id] = "waiting_city_forecast"
        await message.answer("Напишите название города для прогноза:", keyboard=cancel_keyboard())

    @bot.on.message(text="Мой город")
    async def my_city(message: Message):
        """Показать погоду для последнего выбранного города (хранится в temp)."""
        last_city = user_temp_data.get(message.peer_id, {}).get("last_city")
        if not last_city:
            await message.answer("Вы ещё не выбирали город. Напишите 'Погода сейчас' и укажите город.")
            return
        try:
            weather = await weather_client.get_weather_by_city(last_city)
            text = format_current_weather(weather, last_city)
            await message.answer(text, keyboard=main_keyboard())
        except Exception as e:
            await message.answer(f"Ошибка: {str(e)}", keyboard=main_keyboard())

    @bot.on.message(text="Геолокация 🌍")
    async def geo_prompt(message: Message):
        """Просим отправить геолокацию."""
        await message.answer("Отправьте вашу геопозицию (кнопка 'Прикрепить' → 'Геопозиция')")

    @bot.on.message(text="Сравнить города")
    async def compare_prompt(message: Message):
        user_states[message.peer_id] = "waiting_first_city"
        await message.answer("Введите первый город для сравнения:", keyboard=cancel_keyboard())

    @bot.on.message(text="Расширенный режим")
    async def extended_mode(message: Message):
        user_states[message.peer_id] = "waiting_city_extended"
        await message.answer("Введите город для получения качества воздуха и детальной погоды:")

    @bot.on.message(text="Отмена")
    async def cancel_handler(message: Message):
        """Сбрасывает текущее состояние."""
        user_states.pop(message.peer_id, None)
        user_temp_data.pop(message.peer_id, None)
        await message.answer("Действие отменено.", keyboard=main_keyboard())

    # Обработка текстовых сообщений (города)
    @bot.on.message()
    async def handle_city_input(message: Message):
        state = user_states.get(message.peer_id)
        if not state:
            # Если нет активного состояния, реагируем на обычный текст как на город (опционально)
            await message.answer("Используйте кнопки меню.", keyboard=main_keyboard())
            return

        city = message.text.strip()
        try:
            if state == "waiting_city_current":
                weather = await weather_client.get_weather_by_city(city)
                # Сохраняем последний город
                user_temp_data.setdefault(message.peer_id, {})["last_city"] = city
                answer = format_current_weather(weather, city)
                await message.answer(answer, keyboard=main_keyboard())
                user_states.pop(message.peer_id)

            elif state == "waiting_city_forecast":
                forecast = await weather_client.get_forecast_by_city(city)
                answer = format_forecast(forecast, city)
                await message.answer(answer, keyboard=main_keyboard())
                user_states.pop(message.peer_id)

            elif state == "waiting_city_extended":
                # Получаем погоду и качество воздуха
                weather = await weather_client.get_weather_by_city(city)
                air = await weather_client.get_air_quality_by_city(city)
                answer = format_extended(weather, city, air)
                await message.answer(answer, keyboard=main_keyboard())
                user_states.pop(message.peer_id)

            elif state == "waiting_first_city":
                user_temp_data.setdefault(message.peer_id, {})["compare_first"] = city
                user_states[message.peer_id] = "waiting_second_city"
                await message.answer(f"Первый город: {city}. Теперь введите второй город:")

            elif state == "waiting_second_city":
                first = user_temp_data[message.peer_id].get("compare_first")
                second = city
                if not first:
                    await message.answer("Ошибка: первый город не найден. Начните заново.", keyboard=main_keyboard())
                    user_states.pop(message.peer_id)
                    return
                # Получаем погоду для обоих городов
                weather1 = await weather_client.get_weather_by_city(first)
                weather2 = await weather_client.get_weather_by_city(second)
                answer = format_comparison(weather1, first, weather2, second)
                await message.answer(answer, keyboard=main_keyboard())
                user_states.pop(message.peer_id)
                user_temp_data.pop(message.peer_id)

        except Exception as e:
            await message.answer(f"⚠️ Ошибка: {str(e)}. Попробуйте другой город или нажмите 'Отмена'.", keyboard=main_keyboard())
            user_states.pop(message.peer_id)

    # Обработка геолокации (VK присылает объект с координатами)
    @bot.on.message(attachment="geo")
    async def handle_geo(message: Message):
        geo = message.attachment[0].geo
        lat = geo.coordinates.latitude
        lon = geo.coordinates.longitude
        try:
            city_name = await weather_client.get_city_by_coords(lat, lon)
            weather = await weather_client.get_weather_by_coords(lat, lon)
            answer = format_current_weather(weather, city_name)
            await message.answer(f"📍 {answer}", keyboard=main_keyboard())
        except Exception as e:
            await message.answer(f"Не удалось определить погоду по геолокации: {str(e)}", keyboard=main_keyboard())

# ========== Функции форматирования ==========

def format_current_weather(weather: dict, city: str) -> str:
    temp = weather["temperature_c"]
    feels = weather["feels_like_c"]
    desc = weather["description"]
    humidity = weather["humidity"]
    wind = weather["wind_speed"]
    return (f"🌍 Погода в городе {city}:\n"
            f"🌡 Температура: {temp}°C (ощущается как {feels}°C)\n"
            f"☁️ {desc.capitalize()}\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Ветер: {wind} м/с")

def format_forecast(forecast: dict, city: str) -> str:
    """Форматирует прогноз (первые 8 записей = 1 день)."""
    lines = [f"📅 Прогноз для {city} на 5 дней (шаг 3 часа):\n"]
    for item in forecast["list"][:8]:  # первые 8 записей – примерно 24 часа
        dt_str = format_timestamp(item["datetime"], 0)
        lines.append(f"{dt_str}: {item['temp_c']}°C, {item['description']}")
    return "\n".join(lines) + "\n... (остальные часы) ..."

def format_extended(weather: dict, city: str, air: dict) -> str:
    base = format_current_weather(weather, city)
    aqi_desc = air["description"]
    components = air["components"]
    comp_str = f"CO: {components.get('co', 'н/д')}, PM2.5: {components.get('pm2_5', 'н/д')}"
    return (base + f"\n\n🌫 Качество воздуха: {aqi_desc}\n"
            f"📊 {comp_str}")

def format_comparison(weather1: dict, city1: str, weather2: dict, city2: str) -> str:
    temp1 = weather1["temperature_c"]
    temp2 = weather2["temperature_c"]
    diff = abs(temp1 - temp2)
    warmer = city1 if temp1 > temp2 else city2
    return (f"🔍 Сравнение погоды:\n{city1}: {temp1}°C, {weather1['description']}\n"
            f"{city2}: {temp2}°C, {weather2['description']}\n"
            f"📊 Разница температур: {diff}°C\n"
            f"🥵 Теплее в городе: {warmer}")