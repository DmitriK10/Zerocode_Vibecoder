from typing import List, Dict

class Service:
    def __init__(self, name: str, description: str, price: str):
        self.name = name
        self.description = description
        self.price = price

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "price": self.price,
        }

class Catalog:
    def __init__(self):
        self._services = [
            Service("Фирменный стиль", "Логотип, цветовая схема, шрифты, руководство", "от 15 000 руб."),
            Service("Дизайн сайта", "Главная, внутренние страницы, адаптив", "от 25 000 руб."),
            Service("Презентации", "Дизайн слайдов для бизнес-презентаций", "от 5 000 руб."),
            Service("Рекламные материалы", "Баннеры, посты для соцсетей", "от 3 000 руб."),
        ]

    def get_all(self) -> List[Service]:
        return self._services

    def get_prices(self) -> List[str]:
        return [f"{s.name}: {s.price}" for s in self._services]