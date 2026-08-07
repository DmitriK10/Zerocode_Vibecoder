import httpx
from haystack import component
from config import WEATHER_API_KEY

@component
class WeatherComponent:
    @component.output_types(weather_report=str)
    def run(self, city: str) -> dict:
        """Получает текущую погоду для указанного города"""
        if not WEATHER_API_KEY:
            return {"weather_report": "API ключ для погоды не настроен."}

        # Нормализация названия города (приведение к именительному падежу)
        city_normalized = self._normalize_city(city)

        try:
            # 1. Получаем координаты через Geocoding API
            geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
            geocode_params = {
                "q": city_normalized,
                "limit": 1,
                "appid": WEATHER_API_KEY
            }
            geo_response = httpx.get(geocode_url, params=geocode_params, timeout=10)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if not geo_data:
                return {
                    "weather_report": (
                        f"Город '{city}' не найден. "
                        "Пожалуйста, пишите название города в именительном падеже, например: Москва, Санкт-Петербург, Новосибирск."
                    )
                }

            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]
            city_name = geo_data[0].get("local_names", {}).get("ru", city_normalized)

            # 2. Запрашиваем погоду по координатам
            weather_url = "https://api.openweathermap.org/data/2.5/weather"
            weather_params = {
                "lat": lat,
                "lon": lon,
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang": "ru"
            }
            weather_response = httpx.get(weather_url, params=weather_params, timeout=10)
            weather_response.raise_for_status()
            data = weather_response.json()

            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            report = f"Погода в {city_name}: {desc}, температура {temp}°C"
            return {"weather_report": report}

        except httpx.HTTPStatusError as e:
            return {"weather_report": f"Ошибка API: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"weather_report": f"Не удалось получить погоду: {str(e)}"}

    def _normalize_city(self, city: str) -> str:
        """
        Приводит название города к именительному падежу.
        Для популярных городов использует словарь, для остальных – простые правила.
        """
        city_lower = city.lower().strip()

        # Словарь исключений (падежная форма → именительный падеж)
        exceptions = {
            "москве": "Москва",
            "москва": "Москва",
            "питере": "Санкт-Петербург",
            "санкт-петербурге": "Санкт-Петербург",
            "спб": "Санкт-Петербург",
            "екатеринбурге": "Екатеринбург",
            "новосибирске": "Новосибирск",
            "казани": "Казань",
            "нижнем новгороде": "Нижний Новгород",
            "ростове": "Ростов-на-Дону",
            "ростове-на-дону": "Ростов-на-Дону",
            "краснодаре": "Краснодар",
            "сочи": "Сочи",
            "владивостоке": "Владивосток",
            "хабаровске": "Хабаровск",
            "иркутске": "Иркутск",
            "кемерово": "Кемерово",
            "томске": "Томск",
            "омске": "Омск",
            "челябинске": "Челябинск",
            "перми": "Пермь",
            "уфе": "Уфа",
            "самаре": "Самара",
            "саратове": "Саратов",
            "волгограде": "Волгоград",
            "воронеже": "Воронеж",
            "калининграде": "Калининград",
            "ярославле": "Ярославль",
            "рязани": "Рязань",
            "красноярске": "Красноярск",
            "барнауле": "Барнаул",
            "ульяновске": "Ульяновск",
            "пензе": "Пенза",
            "ставрополе": "Ставрополь",
            "махачкале": "Махачкала",
            "тюмени": "Тюмень",
            "кирове": "Киров",
            "чебоксарах": "Чебоксары",
            "орле": "Орёл",
        }

        if city_lower in exceptions:
            return exceptions[city_lower]

        # Простая нормализация: если слово заканчивается на типичные падежные окончания,
        # пробуем убрать их (но только если длина > 3, чтобы не испортить короткие названия)
        if len(city) > 3:
            if city.endswith('е'):
                return city[:-1] + 'а'  # Москве → Москва
            elif city.endswith('и'):
                return city[:-1] + 'а'  # приблизительно
            elif city.endswith('у'):
                return city[:-1] + 'а'
            elif city.endswith('ой'):
                return city[:-2] + 'а'
            elif city.endswith('ю'):
                return city[:-1] + 'а'
            elif city.endswith('о'):
                return city[:-1] + 'а'
            elif city.endswith('ё'):
                return city[:-1] + 'а'
        # Если ничего не подошло, возвращаем как есть
        return city