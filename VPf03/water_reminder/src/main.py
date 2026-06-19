import os
from loader import PlanLoader
from formatter import ConsoleFormatter
from notifier import WinToastNotifier   # или ConsoleNotifier, если хотите
from scheduler import Scheduler

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'plan.json')

    loader = PlanLoader(data_path)
    formatter = ConsoleFormatter()
    notifier = WinToastNotifier()   # используем всплывающие уведомления

    plan = loader.load()

    # Покажем план при старте
    print(formatter.format(plan))

    scheduler = Scheduler(plan, notifier)
    scheduler.schedule_all()
    scheduler.run_forever()

if __name__ == "__main__":
    main()