"""
Точка входа в приложение. Оркестрирует работу калькулятора, БД и интерфейса.
"""

from price_calculator import SimpleDiscountCalculator
from database import SQLiteCalculationRepository
from cli import ConsoleUserInterface
from interfaces import IPriceCalculator, ICalculationRepository, IUserInterface


class DiscountCalculatorApp:
    """
    Основной класс приложения, связывающий компоненты через интерфейсы
    (внедрение зависимостей).
    """

    def __init__(self, calculator: IPriceCalculator,
                 repository: ICalculationRepository,
                 ui: IUserInterface):
        self.calculator = calculator
        self.repository = repository
        self.ui = ui

    def run(self) -> None:
        """Запуск главного цикла приложения."""
        self.ui.show_message("🛒 КАЛЬКУЛЯТОР СКИДОК (с историей)")
        self.ui.show_message("=" * 40)

        while True:
            choice = self.ui.get_menu_choice()

            if choice == '1':
                self._do_calculation()
            elif choice == '2':
                self._show_history()
            elif choice == '3':
                self.ui.show_message("👋 До свидания!")
                break

    def _do_calculation(self) -> None:
        """Выполнить один расчёт и сохранить результат."""
        self.ui.show_message("\n--- Новый расчёт ---")

        original_price = self.ui.get_float_input(
            "Введите исходную цену товара (руб.): ", min_value=0.01
        )
        discount_percent = self.ui.get_int_input(
            "Введите процент скидки (0-100): ", min_value=0, max_value=100
        )
        fixed_discount = self.ui.get_float_input(
            "Введите фиксированную скидку по промокоду (руб., 0 если нет): ",
            min_value=0.0
        )

        result = self.calculator.calculate(original_price, discount_percent, fixed_discount)

        self.repository.save(result)
        self.ui.show_calculation_result(result)

    def _show_history(self) -> None:
        """Отобразить историю расчётов."""
        history = self.repository.get_all()
        self.ui.show_history(history)


def main() -> None:
    """Создание зависимостей и запуск приложения."""
    # Внедрение зависимостей (Dependency Injection)
    calculator = SimpleDiscountCalculator()
    repository = SQLiteCalculationRepository(
        db_path=r"C:\Users\ADATA\Documents\Zerocode_Vibecoder\VPa06\DiscountCalculator\calculations.db"
    )
    ui = ConsoleUserInterface()

    app = DiscountCalculatorApp(calculator, repository, ui)
    app.run()


if __name__ == "__main__":
    main()