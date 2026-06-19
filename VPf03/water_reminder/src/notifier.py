from abc import ABC, abstractmethod

class Notifier(ABC):
    """Абстрактный интерфейс для отправки уведомлений."""
    @abstractmethod
    def send(self, message: str) -> None:
        pass

class ConsoleNotifier(Notifier):
    """Реализация уведомления через вывод в консоль."""
    def send(self, message: str) -> None:
        print(message)

class WinToastNotifier(Notifier):
    """Реализация уведомления через всплывающие окна Windows (win10toast)."""
    def __init__(self):
        try:
            from win10toast import ToastNotifier
            self.toaster = ToastNotifier()
            self.available = True
        except ImportError:
            print("⚠️ win10toast не установлен. Используется вывод в консоль.")
            self.available = False

    def send(self, message: str) -> None:
        if self.available:
            self.toaster.show_toast(
                "💧 Water Reminder",
                message,
                duration=10,
                threaded=True
            )
        else:
            # fallback на консоль
            print(f"[Уведомление] {message}")