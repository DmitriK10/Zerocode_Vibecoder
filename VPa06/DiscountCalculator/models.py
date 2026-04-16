"""
Модели данных, используемые в приложении.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CalculationInput:
    """Входные данные для расчёта скидки."""

    original_price: float
    discount_percent: int
    fixed_discount: float


@dataclass
class CalculationResult(CalculationInput):
    """Результат расчёта скидки, включая вычисленную финальную цену и временную метку."""

    final_price: float
    timestamp: datetime

    def __str__(self) -> str:
        """Удобочитаемое строковое представление."""
        return (f"Исходная цена: {self.original_price:.2f} ₽, "
                f"скидка: {self.discount_percent}%, "
                f"фикс. скидка: {self.fixed_discount:.2f} ₽ → "
                f"ИТОГО: {self.final_price:.2f} ₽")