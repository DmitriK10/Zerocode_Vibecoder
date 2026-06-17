#!/usr/bin/env python3
"""
Эмуляция работы криптовалютного бэкенда с отправкой логов в Loki.
"""
import time
import random
import sys
from loki_logger import LokiLogger


def emulate_crypto_backend(loki: LokiLogger, interval_sec: float = 3.0):
    """
    Генерирует случайные события: цена, ошибки, авторизации.
    """
    levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
    job_names = ["crypto-backend", "price-fetcher", "auth-service"]

    price = 50000.0  # начальная цена BTC

    print("Эмуляция криптовалютного бэкенда запущена. Логи отправляются в Loki...")
    while True:
        # Случайное изменение цены
        delta = random.uniform(-500, 500)
        price += delta
        price = max(10000, price)

        # Лог изменения цены (INFO)
        loki.send(f"Цена BTC: ${price:.2f} (изменение: {delta:+.2f})", level="INFO", job="price-fetcher")

        # С вероятностью 30% генерируем дополнительное событие
        if random.random() < 0.3:
            event_type = random.choice(["order", "auth", "error"])
            if event_type == "order":
                amount = random.uniform(0.01, 2.0)
                side = random.choice(["buy", "sell"])
                loki.send(f"Совершена {side} {amount:.4f} BTC по цене {price:.2f}", level="INFO", job="crypto-backend")
            elif event_type == "auth":
                user = f"user_{random.randint(1,100)}"
                if random.random() < 0.8:
                    loki.send(f"Пользователь {user} успешно авторизован", level="INFO", job="auth-service")
                else:
                    loki.send(f"Ошибка авторизации пользователя {user}: неверный пароль", level="ERROR", job="auth-service")
            else:  # error
                error_msgs = [
                    "Таймаут подключения к бирже",
                    "Неверный формат ответа API",
                    "Недостаточно средств для ордера",
                    "Сетевая ошибка при отправке запроса"
                ]
                err_msg = random.choice(error_msgs)
                level = random.choices(["WARNING", "ERROR"], weights=[0.7, 0.3])[0]
                loki.send(err_msg, level=level, job="crypto-backend")

        # Иногда DEBUG-логи
        if random.random() < 0.1:
            loki.send(f"Отладочная информация: текущая нагрузка {random.randint(10, 95)}%", level="DEBUG", job="crypto-backend")

        time.sleep(interval_sec)


if __name__ == "__main__":
    # Укажите правильный URL Loki (внутри контейнера Docker используйте http://loki:3100)
    LOKI_URL = "http://localhost:3100"  # при запуске на сервере (вне контейнера)
    # Если запускаете на том же хосте, где работает Docker с Loki:
    # LOKI_URL = "http://localhost:3100"
    # Если внутри другого контейнера: "http://loki:3100"

    loki_client = LokiLogger(loki_url=LOKI_URL, default_job="crypto-app")

    try:
        emulate_crypto_backend(loki_client, interval_sec=2.0)
    except KeyboardInterrupt:
        print("\nОстановка эмуляции.")
        sys.exit(0)