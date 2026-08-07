import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from tools.cat_fact import CatFactComponent
from tools.dog_image import DogImageComponent
from tools.weather import WeatherComponent

class TestTools(unittest.TestCase):
    """Тесты для инструментов (кошки, собаки, погода)."""

    @patch('tools.cat_fact.httpx.get')
    def test_cat_fact_success(self, mock_get):
        """Проверяет, что CatFactComponent корректно получает факт о кошках."""
        print("\n🔍 Тест: получение факта о кошках")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"fact": "Cats are cute."}
        mock_get.return_value = mock_response

        comp = CatFactComponent()
        result = comp.run()
        self.assertEqual(result["fact"], "Cats are cute.")
        print("✅ Факт о кошках получен успешно")

    @patch('tools.dog_image.httpx.get')
    def test_dog_image_success(self, mock_get):
        """Проверяет, что DogImageComponent корректно получает URL изображения собаки."""
        print("\n🔍 Тест: получение изображения собаки")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "dog123.jpg"
        mock_get.return_value = mock_response

        comp = DogImageComponent()
        result = comp.run()
        self.assertEqual(result["image_url"], "https://random.dog/dog123.jpg")
        print("✅ URL изображения собаки получен")

    @patch('tools.weather.httpx.get')
    def test_weather_success(self, mock_get):
        """Проверяет, что WeatherComponent корректно получает погоду для города."""
        print("\n🔍 Тест: получение погоды")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {"temp": 20.5},
            "weather": [{"description": "ясно"}]
        }
        mock_get.return_value = mock_response

        comp = WeatherComponent()
        result = comp.run("Moscow")
        self.assertIn("Погода в Moscow", result["weather_report"])
        print("✅ Погода получена успешно")

if __name__ == '__main__':
    unittest.main()