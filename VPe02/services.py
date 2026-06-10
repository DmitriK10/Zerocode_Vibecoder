"""Модуль бизнес-логики приложения."""

from abc import ABC, abstractmethod


class CalculatorInterface(ABC):
    """Абстрактный интерфейс калькулятора (принцип инверсии зависимостей)."""

    @abstractmethod
    def calculate(self, a: float, b: float, operation: str) -> float:
        """Выполнить операцию над a и b."""
        pass


class SimpleCalculator(CalculatorInterface):
    """Реализация калькулятора (принцип подстановки Барбары Лисков)."""

    def calculate(self, a: float, b: float, operation: str) -> float:
        if operation == 'add':
            return a + b
        elif operation == 'subtract':
            return a - b
        elif operation == 'multiply':
            return a * b
        elif operation == 'divide':
            if b == 0:
                raise ValueError("Деление на ноль")
            return a / b
        else:
            raise ValueError(f"Неизвестная операция: {operation}")