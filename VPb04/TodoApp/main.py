"""
Система управления задачами (Todo-лист)
Реализация с соблюдением принципов SOLID.
"""

import json
import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, List, Optional


# ==================== Абстрактные базовые классы ====================
class Serializable(ABC):
    """Интерфейс для объектов, поддерживающих сериализацию в словарь."""
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass


class Identifiable(ABC):
    """Интерфейс для объектов, имеющих уникальный идентификатор."""
    @property
    @abstractmethod
    def id(self) -> uuid.UUID:
        pass


# ==================== Класс Task ====================
class Task(Serializable, Identifiable):
    """
    Отдельная задача.
    SRP: отвечает только за данные и поведение одной задачи.
    """

    def __init__(
        self,
        title: str,
        description: str = "",
        due_date: Optional[str] = None,
        is_completed: bool = False,
        task_id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None
    ) -> None:
        """
        :param title: Название задачи.
        :param description: Описание.
        :param due_date: Срок выполнения в формате 'YYYY-MM-DD'.
        :param is_completed: Статус выполнения.
        :param task_id: Уникальный идентификатор (если None, генерируется автоматически).
        :param created_at: Дата создания (если None, устанавливается текущая).
        """
        self._title = title
        self._description = description
        self._is_completed = is_completed
        self._due_date: Optional[date] = None
        if due_date:
            self.set_due_date(due_date)
        self._task_id = task_id or uuid.uuid4()
        self._created_at = created_at or datetime.now()

    # --- Свойства (геттеры) ---
    @property
    def id(self) -> uuid.UUID:
        return self._task_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    @property
    def is_completed(self) -> bool:
        return self._is_completed

    @property
    def due_date(self) -> Optional[date]:
        return self._due_date

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # --- Методы управления состоянием ---
    def mark_completed(self) -> None:
        """Отметить задачу выполненной."""
        self._is_completed = True

    def mark_incomplete(self) -> None:
        """Снять отметку выполнения."""
        self._is_completed = False

    def update_description(self, new_description: str) -> None:
        """Изменить описание задачи."""
        self._description = new_description

    def set_due_date(self, date_str: str) -> None:
        """
        Установить или изменить срок выполнения.
        :param date_str: Строка в формате 'YYYY-MM-DD'.
        :raises ValueError: Если формат неверный.
        """
        try:
            self._due_date = date.fromisoformat(date_str)
        except ValueError:
            raise ValueError("Неверный формат даты. Ожидается YYYY-MM-DD.")

    # --- Сериализация ---
    def to_dict(self) -> Dict[str, Any]:
        """Возвращает словарь с данными задачи (для сохранения в JSON)."""
        return {
            "task_id": str(self._task_id),
            "title": self._title,
            "description": self._description,
            "is_completed": self._is_completed,
            "due_date": self._due_date.isoformat() if self._due_date else None,
            "created_at": self._created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Создаёт объект Task из словаря."""
        return cls(
            title=data["title"],
            description=data["description"],
            due_date=data.get("due_date"),
            is_completed=data["is_completed"],
            task_id=uuid.UUID(data["task_id"]),
            created_at=datetime.fromisoformat(data["created_at"])
        )

    def __str__(self) -> str:
        status = "✓" if self._is_completed else "✗"
        due = f", срок: {self._due_date}" if self._due_date else ""
        return f"[{status}] {self._title}{due}"


# ==================== Класс Project ====================
class Project(Serializable, Identifiable):
    """
    Проект (список задач).
    SRP: управляет коллекцией задач.
    """

    def __init__(
        self,
        name: str,
        tasks: Optional[List[Task]] = None,
        project_id: Optional[uuid.UUID] = None
    ) -> None:
        self._name = name
        self._tasks = tasks if tasks is not None else []
        self._project_id = project_id or uuid.uuid4()

    @property
    def id(self) -> uuid.UUID:
        return self._project_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def tasks(self) -> List[Task]:
        return self._tasks

    # --- Методы управления задачами ---
    def add_task(self, task: Task) -> None:
        """Добавить задачу в проект."""
        self._tasks.append(task)

    def remove_task(self, task_id: uuid.UUID) -> bool:
        """
        Удалить задачу по ID.
        :return: True, если задача была удалена, иначе False.
        """
        for task in self._tasks:
            if task.id == task_id:
                self._tasks.remove(task)
                return True
        return False

    def get_task(self, task_id: uuid.UUID) -> Optional[Task]:
        """Получить задачу по ID."""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def get_incomplete_tasks(self) -> List[Task]:
        """Вернуть список незавершённых задач."""
        return [task for task in self._tasks if not task.is_completed]

    def get_completed_tasks(self) -> List[Task]:
        """Вернуть список завершённых задач."""
        return [task for task in self._tasks if task.is_completed]

    # --- Сериализация ---
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": str(self._project_id),
            "name": self._name,
            "tasks": [task.to_dict() for task in self._tasks]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        project = cls(
            name=data["name"],
            project_id=uuid.UUID(data["project_id"])
        )
        for task_data in data.get("tasks", []):
            project.add_task(Task.from_dict(task_data))
        return project

    def __str__(self) -> str:
        return f"Проект '{self._name}' (задач: {len(self._tasks)})"


# ==================== Класс User ====================
class User(Serializable, Identifiable):
    """
    Пользователь системы.
    SRP: отвечает за управление проектами.
    """

    def __init__(
        self,
        username: str,
        email: str,
        projects: Optional[List[Project]] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> None:
        self._username = username
        self._email = email
        self._projects = projects if projects is not None else []
        self._user_id = user_id or uuid.uuid4()

    @property
    def id(self) -> uuid.UUID:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> str:
        return self._email

    @property
    def projects(self) -> List[Project]:
        return self._projects

    # --- Управление проектами ---
    def create_project(self, name: str) -> Project:
        """Создать новый проект и добавить его пользователю."""
        project = Project(name)
        self._projects.append(project)
        return project

    def delete_project(self, project_id: uuid.UUID) -> bool:
        """Удалить проект по ID."""
        for project in self._projects:
            if project.id == project_id:
                self._projects.remove(project)
                return True
        return False

    def get_project(self, project_id: uuid.UUID) -> Optional[Project]:
        """Найти проект по ID."""
        for project in self._projects:
            if project.id == project_id:
                return project
        return None

    # --- Сериализация ---
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": str(self._user_id),
            "username": self._username,
            "email": self._email,
            "projects": [project.to_dict() for project in self._projects]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        user = cls(
            username=data["username"],
            email=data["email"],
            user_id=uuid.UUID(data["user_id"])
        )
        for proj_data in data.get("projects", []):
            user._projects.append(Project.from_dict(proj_data))
        return user

    def __str__(self) -> str:
        return f"Пользователь: {self._username} ({self._email}), проектов: {len(self._projects)}"


# ==================== Демонстрация работы ====================
def main() -> None:
    """Пример использования системы."""
    print("=== Демонстрация системы управления задачами ===\n")

    # 1. Создаём пользователя
    user = User(username="alex", email="alex@example.com")
    print(user)

    # 2. Создаём проекты
    work = user.create_project("Работа")
    personal = user.create_project("Личное")
    print(f"Созданы проекты: {work.name}, {personal.name}")

    # 3. Добавляем задачи в проект "Работа"
    task1 = Task(
        title="Закончить отчёт",
        description="Подготовить квартальный отчёт для руководства",
        due_date="2026-04-30"
    )
    task2 = Task(
        title="Созвон с командой",
        description="Еженедельный митинг в Zoom"
    )
    work.add_task(task1)
    work.add_task(task2)

    # 4. Добавляем задачи в проект "Личное"
    task3 = Task(
        title="Купить продукты",
        description="Молоко, хлеб, яблоки",
        due_date="2026-04-21"
    )
    personal.add_task(task3)

    # 5. Отметим одну задачу выполненной
    task1.mark_completed()
    print(f"\nЗадача '{task1.title}' отмечена выполненной.")

    # 6. Выведем информацию о проектах и задачах
    print("\n--- Проекты пользователя ---")
    for project in user.projects:
        print(f"\n{project}")
        print("  Задачи:")
        for task in project.tasks:
            print(f"    {task}")

    # 7. Покажем незавершённые задачи в проекте "Работа"
    incomplete = work.get_incomplete_tasks()
    print(f"\nНезавершённые задачи в проекте '{work.name}':")
    for t in incomplete:
        print(f"  - {t.title}")

    # 8. Сериализация в JSON и обратно (демонстрация сохранения/загрузки)
    print("\n--- Сериализация данных пользователя ---")
    data = user.to_dict()
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    print("JSON представление (первые 500 символов):")
    print(json_str[:500] + "...\n")

    # 9. Восстановление объекта из JSON
    restored_user = User.from_dict(data)
    print(f"Пользователь восстановлен: {restored_user}")
    print(f"Количество проектов после восстановления: {len(restored_user.projects)}")


if __name__ == "__main__":
    main()