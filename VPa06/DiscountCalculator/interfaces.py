"""
Абстрактные базовые классы (интерфейсы) для реализации принципа инверсии зависимостей.
"""

from abc import ABC, abstractmethod
from typing import List
from models import CalculationResult


class IPriceCalculator(ABC):
    """Интерфейс калькулятора скидок."""

    @abstractmethod
    def calculate(self, original_price: float, discount_percent: int,
                  fixed_discount: float = 0.0) -> CalculationResult:
        """
        Рассчитать финальную цену с учётом скидок.

        Args:
            original_price: исходная цена товара
            discount_percent: процент скидки (0-100)
            fixed_discount: фиксированная скидка по промокоду

        Returns:
            Объект CalculationResult с результатами расчёта
        """
        pass


class ICalculationRepository(ABC):
    """Интерфейс репозитория для сохранения и получения истории расчётов."""

    @abstractmethod
    def save(self, result: CalculationResult) -> None:
        """
        Сохранить результат расчёта в хранилище.

        Args:
            result: объект с данными расчёта
        """
        pass

    @abstractmethod
    def get_all(self) -> List[CalculationResult]:
        """
        Получить всю историю расчётов.

        Returns:
            Список объектов CalculationResult
        """
        pass


class IUserInterface(ABC):
    """Интерфейс пользовательского ввода-вывода."""

    @abstractmethod
    def show_message(self, message: str) -> None:
        """Показать сообщение пользователю."""
        pass

    @abstractmethod
    def show_calculation_result(self, result: CalculationResult) -> None:
        """Отобразить результат расчёта."""
        pass

    @abstractmethod
    def show_history(self, history: List[CalculationResult]) -> None:
        """Отобразить историю расчётов."""
        pass

    @abstractmethod
    def get_float_input(self, prompt: str, min_value: float = 0.0) -> float:
        """
        Запросить у пользователя число с плавающей точкой.

        Args:
            prompt: текст запроса
            min_value: минимально допустимое значение

        Returns:
            Введённое число
        """
        pass

    @abstractmethod
    def get_int_input(self, prompt: str, min_value: int = 0, max_value: int = 100) -> int:
        """
        Запросить у пользователя целое число.

        Args:
            prompt: текст запроса
            min_value: минимально допустимое значение
            max_value: максимально допустимое значение

        Returns:
            Введённое число
        """
        pass

    @abstractmethod
    def get_menu_choice(self) -> str:
        """
        Показать главное меню и получить выбор пользователя.

        Returns:
            Символ выбора ('1', '2', '3')
        """
        pass