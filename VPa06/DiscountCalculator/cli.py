"""
Реализация пользовательского интерфейса через консоль.
"""

from typing import List
from interfaces import IUserInterface
from models import CalculationResult


class ConsoleUserInterface(IUserInterface):
    """Консольный интерфейс взаимодействия с пользователем."""

    def show_message(self, message: str) -> None:
        print(message)

    def show_calculation_result(self, result: CalculationResult) -> None:
        print("\n" + "=" * 50)
        print(f"✅ Расчёт выполнен: {result}")
        print(f"   Время: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50 + "\n")

    def show_history(self, history: List[CalculationResult]) -> None:
        if not history:
            print("\n📭 История расчётов пуста.\n")
            return

        print("\n" + "=" * 70)
        print("                         ИСТОРИЯ РАСЧЁТОВ")
        print("=" * 70)
        for i, item in enumerate(history, 1):
            print(f"{i}. {item}  ({item.timestamp.strftime('%d.%m.%Y %H:%M')})")
        print("=" * 70 + "\n")

    def get_float_input(self, prompt: str, min_value: float = 0.0) -> float:
        while True:
            try:
                value = float(input(prompt))
                if value < min_value:
                    print(f"❌ Значение должно быть не менее {min_value}. Попробуйте снова.")
                    continue
                return value
            except ValueError:
                print("❌ Некорректный ввод. Пожалуйста, введите число.")

    def get_int_input(self, prompt: str, min_value: int = 0, max_value: int = 100) -> int:
        while True:
            try:
                value = int(input(prompt))
                if not (min_value <= value <= max_value):
                    print(f"❌ Значение должно быть в диапазоне [{min_value}, {max_value}]. Попробуйте снова.")
                    continue
                return value
            except ValueError:
                print("❌ Некорректный ввод. Пожалуйста, введите целое число.")

    def get_menu_choice(self) -> str:
        print("\n" + "-" * 30)
        print("ГЛАВНОЕ МЕНЮ")
        print("-" * 30)
        print("1. Выполнить новый расчёт")
        print("2. Показать историю расчётов")
        print("3. Выход")
        while True:
            choice = input("Ваш выбор (1/2/3): ").strip()
            if choice in ('1', '2', '3'):
                return choice
            print("❌ Неверный ввод. Введите 1, 2 или 3.")