from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os

from database import TaskRepository
from utils import generate_tasks_csv

router = Router()
repo = TaskRepository()

# --- Определение состояний для FSM (добавление задачи: текст -> статус -> категория) ---
class AddTaskState(StatesGroup):
    waiting_for_text = State()
    waiting_for_status = State()
    waiting_for_category = State()

# Клавиатуры для выбора статуса и категории
status_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Новая"), KeyboardButton(text="В работе")],
        [KeyboardButton(text="Завершена"), KeyboardButton(text="Отложена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

category_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Работа"), KeyboardButton(text="Личное")],
        [KeyboardButton(text="Учеба"), KeyboardButton(text="Дом")],
        [KeyboardButton(text="Общая")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# --- Команда /start ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот для хранения задач.\n\n"
        "Доступные команды:\n"
        "/add - добавить новую задачу (текст, статус, категория)\n"
        "/list - показать все ваши задачи\n"
        "/list_csv - выгрузить все задачи в CSV-файл"
    )

# --- Команда /add (запуск FSM) ---
@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await state.set_state(AddTaskState.waiting_for_text)
    await message.answer("📝 Введите текст задачи:", reply_markup=ReplyKeyboardRemove())

# --- Получение текста задачи ---
@router.message(AddTaskState.waiting_for_text, F.text)
async def process_task_text(message: Message, state: FSMContext):
    task_text = message.text.strip()
    if not task_text:
        await message.answer("❌ Задача не может быть пустой. Попробуйте ещё раз /add")
        await state.clear()
        return
    await state.update_data(text=task_text)
    await state.set_state(AddTaskState.waiting_for_status)
    await message.answer("Выберите статус задачи:", reply_markup=status_keyboard)

# --- Получение статуса ---
@router.message(AddTaskState.waiting_for_status, F.text.in_(["Новая", "В работе", "Завершена", "Отложена"]))
async def process_task_status(message: Message, state: FSMContext):
    status = message.text
    await state.update_data(status=status)
    await state.set_state(AddTaskState.waiting_for_category)
    await message.answer("Выберите категорию:", reply_markup=category_keyboard)

# --- Обработка неверного статуса ---
@router.message(AddTaskState.waiting_for_status)
async def process_invalid_status(message: Message, state: FSMContext):
    await message.answer("⚠️ Пожалуйста, выберите статус из предложенных кнопок.")

# --- Получение категории и сохранение задачи ---
@router.message(AddTaskState.waiting_for_category, F.text.in_(["Работа", "Личное", "Учеба", "Дом", "Общая"]))
async def process_task_category(message: Message, state: FSMContext):
    category = message.text
    data = await state.get_data()
    text = data.get("text")
    status = data.get("status")
    user_id = message.from_user.id

    repo.add_task(text, user_id, status, category)
    await message.answer(
        f"✅ Задача сохранена!\n"
        f"Текст: {text}\n"
        f"Статус: {status}\n"
        f"Категория: {category}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()

# --- Обработка неверной категории ---
@router.message(AddTaskState.waiting_for_category)
async def process_invalid_category(message: Message, state: FSMContext):
    await message.answer("⚠️ Пожалуйста, выберите категорию из предложенных кнопок.")

# --- Команда /list ---
@router.message(Command("list"))
async def cmd_list(message: Message):
    user_id = message.from_user.id
    tasks = repo.get_user_tasks(user_id)  # (id, text, created_at, status, category)

    if not tasks:
        await message.answer("📭 У вас пока нет задач. Добавьте первую через /add")
        return

    response_lines = ["📋 **Ваши задачи:**\n"]
    for idx, (task_id, task_text, created_at, status, category) in enumerate(tasks, start=1):
        formatted_date = created_at.replace("T", " ")[:16]
        response_lines.append(
            f"{idx}. {task_text}\n"
            f"   Статус: {status} | Категория: {category}\n"
            f"   (добавлено: {formatted_date})"
        )
    await message.answer("\n".join(response_lines), parse_mode="Markdown")

# --- Команда /list_csv ---
@router.message(Command("list_csv"))
async def cmd_list_csv(message: Message):
    all_tasks = repo.get_all_tasks()  # (id, text, user_id, created_at, status, category)

    if not all_tasks:
        await message.answer("📭 Нет задач для выгрузки. Добавьте задачи через /add")
        return

    csv_path = generate_tasks_csv(all_tasks)
    document = FSInputFile(csv_path, filename="tasks_export.csv")
    await message.answer_document(document, caption="📊 Экспорт всех задач выполнен.")
    os.remove(csv_path)