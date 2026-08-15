import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8918305399:AAHi8oc4U4Seg6UpM4O4BBH7w6G4VXxwq1g"  # Замени на свой
PROJECTS_PATH = os.path.join(os.path.dirname(__file__), 'projects.json')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load_projects():
    with open(PROJECTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот-портфолио Дмитрия.\n"
        "Вот мои проекты. Выбери интересующий:",
        reply_markup=projects_keyboard()
    )

def projects_keyboard():
    projects = load_projects()
    buttons = []
    for p in projects:
        buttons.append([InlineKeyboardButton(text=p['title'], callback_data=f"project_{p['id']}")])
    buttons.append([InlineKeyboardButton(text="🌐 Сайт", url="https://dmitrik10.ru")])  # если есть
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(lambda c: c.data.startswith('project_'))
async def show_project(callback: types.CallbackQuery):
    project_id = int(callback.data.split('_')[1])
    projects = load_projects()
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        await callback.answer("Проект не найден")
        return
    text = f"<b>{project['title']}</b>\n\n{project['description']}\n\n<i>Технологии:</i> {', '.join(project['technologies'])}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Демо", url=project.get('demo_url', 'https://t.me/DmitriK10'))],
        [InlineKeyboardButton("Код на GitHub", url=project.get('github_url', 'https://github.com/DmitriK10'))],
        [InlineKeyboardButton("◀️ Назад", callback_data="back")]
    ])
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(lambda c: c.data == 'back')
async def back_to_list(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выбери проект:",
        reply_markup=projects_keyboard()
    )
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())