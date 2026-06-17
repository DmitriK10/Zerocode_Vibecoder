"""
Модуль для отправки логов в Loki через HTTP API.
Реализует принцип Single Responsibility: только отправка.
"""
import json
import time
from typing import Dict, Any, Optional, List
import requests


class LokiLogger:
    """
    Абстракция для отправки логов в Loki.
    Позволяет заменить реализацию (Dependency Inversion).
    """

    def __init__(self, loki_url: str = "http://localhost:3100", default_job: str = "python-app"):
        self.loki_url = loki_url.rstrip('/')
        self.push_url = f"{self.loki_url}/loki/api/v1/push"
        self.default_job = default_job

    def _build_payload(self, message: str, level: str, job: str, timestamp_ns: Optional[int] = None) -> Dict[str, Any]:
        """
        Формирует JSON-структуру, ожидаемую Loki.
        """
        if timestamp_ns is None:
            timestamp_ns = int(time.time() * 1_000_000_000)  # наносекунды

        return {
            "streams": [
                {
                    "stream": {
                        "app": job,
                        "level": level
                    },
                    "values": [
                        [str(timestamp_ns), message]
                    ]
                }
            ]
        }

    def send(self, message: str, level: str = "INFO", job: Optional[str] = None) -> bool:
        """
        Отправляет один лог в Loki.
        :return: True если успешно (статус 204), иначе False.
        """
        job_name = job or self.default_job
        payload = self._build_payload(message, level, job_name)
        try:
            response = requests.post(self.push_url, json=payload, timeout=5)
            if response.status_code == 204:
                # Добавленный отладочный вывод
                print(f"[Loki] ✓ Лог отправлен: {message[:50]}... (job={job_name}, level={level})")
                return True
            else:
                print(f"[Loki] ✗ Ошибка {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"[Loki] ✗ Исключение: {e}")
            return False

    def send_batch(self, logs: List[Dict[str, str]], job: Optional[str] = None) -> bool:
        """
        Отправляет несколько логов за раз (один поток с разными временными метками).
        logs: список словарей с ключами 'message', 'level' (опционально).
        """
        job_name = job or self.default_job
        now_ns = int(time.time() * 1_000_000_000)
        values = []
        for idx, log in enumerate(logs):
            ts = now_ns - (len(logs) - idx) * 1_000_000_000  # имитация разных моментов
            level = log.get('level', 'INFO')
            values.append([str(ts), log['message']])

        payload = {
            "streams": [
                {
                    "stream": {
                        "app": job_name,
                        "level": "batch"
                    },
                    "values": values
                }
            ]
        }
        try:
            resp = requests.post(self.push_url, json=payload, timeout=5)
            if resp.status_code == 204:
                print(f"[Loki] ✓ Batch отправлен, {len(logs)} логов")
                return True
            else:
                print(f"[Loki] ✗ Ошибка batch: {resp.status_code}")
                return False
        except Exception as e:
            print(f"[Loki] ✗ Исключение batch: {e}")
            return False


# Для обратной совместимости с заданием (простая функция)
def send_log_to_loki(message: str, job: str = "python-app", level: str = "INFO", loki_url: str = "http://localhost:3100") -> bool:
    """
    Упрощенная функция для отправки одного лога.
    """
    logger = LokiLogger(loki_url=loki_url, default_job=job)
    return logger.send(message, level, job)