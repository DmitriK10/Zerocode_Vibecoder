import re
import schedule
import time
from typing import Dict, Any, List, Tuple
from notifier import Notifier

class Scheduler:
    """Планирует отправку напоминаний на основе шагов из плана."""

    def __init__(self, plan: Dict[str, Any], notifier: Notifier):
        self.plan = plan
        self.notifier = notifier
        self.scheduled_tasks = []
        self._parse_times()

    def _parse_times(self) -> List[Tuple[str, str]]:
        """Извлекает из шагов время в формате (ЧЧ:ММ) и соответствующий текст."""
        time_pattern = re.compile(r'(\d{2}:\d{2})')  # ищем "ЧЧ:ММ"
        for step in self.plan['steps']:
            matches = time_pattern.findall(step)  # найдём все времена в шаге
            for time_str in matches:
                self.scheduled_tasks.append((time_str, step))
        return self.scheduled_tasks

    def _send_reminder(self, step_text: str) -> None:
        """Отправляет напоминание через нотификатор."""
        message = f"💧 Напоминание: {step_text}"
        self.notifier.send(message)

    def schedule_all(self) -> None:
        """Регистрирует все задачи в библиотеке schedule."""
        for time_str, step_text in self.scheduled_tasks:
            # Прямой вызов: каждый день в указанное время
            schedule.every().day.at(time_str).do(self._send_reminder, step_text)
            print(f"⏰ Запланировано напоминание на {time_str}: {step_text[:50]}...")

    def run_forever(self) -> None:
        """Запускает бесконечный цикл проверки расписания."""
        print("\n🕒 Планировщик запущен. Напоминания будут приходить в указанное время.")
        print("Для остановки нажмите Ctrl+C.\n")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Планировщик остановлен пользователем.")