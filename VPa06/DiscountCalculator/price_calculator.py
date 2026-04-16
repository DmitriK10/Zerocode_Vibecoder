"""
Реализация калькулятора скидок.
"""

from interfaces import IPriceCalculator
from models import CalculationInput, CalculationResult
from datetime import datetime


class SimpleDiscountCalculator(IPriceCalculator):
    """
    Простой калькулятор, применяющий процентную и фиксированную скидки.
    Может быть легко расширен путём наследования и переопределения метода calculate.
    """

    def calculate(self, original_price: float, discount_percent: int,
                  fixed_discount: float = 0.0) -> CalculationResult:
        """
        Рассчитать финальную цену по формуле:
        final_price = max(0, original_price * (1 - discount_percent/100) - fixed_discount)
        """
        price_after_percent = original_price * (1 - discount_percent / 100)
        final_price = max(0.0, price_after_percent - fixed_discount)

        input_data = CalculationInput(
            original_price=original_price,
            discount_percent=discount_percent,
            fixed_discount=fixed_discount
        )
        return CalculationResult(
            **input_data.__dict__,
            final_price=final_price,
            timestamp=datetime.now()
        )