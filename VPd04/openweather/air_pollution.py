"""Air Pollution API – качество воздуха по координатам."""
import aiohttp
from typing import Dict, Any
from exceptions import AirPollutionError
from utils import aqi_description

class AirPollution:
    URL = "http://api.openweathermap.org/data/2.5/air_pollution"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Возвращает данные о загрязнении: AQI, концентрации CO, NO2, PM2.5 и т.д.
        """
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL, params=params) as resp:
                if resp.status != 200:
                    raise AirPollutionError(f"Ошибка получения качества воздуха: HTTP {resp.status}")
                data = await resp.json()

        if not data.get("list"):
            raise AirPollutionError("Нет данных о качестве воздуха")

        first = data["list"][0]
        aqi = first["main"]["aqi"]
        components = first["components"]
        return {
            "aqi": aqi,
            "description": aqi_description(aqi),
            "components": components
        }