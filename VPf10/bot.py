import asyncio
import logging
import os
import base64
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from utils.ai_processor import process_dialog_with_ai, generate_product_card_data
from utils.pdf_generator import generate_pdf
from utils.image_generator import generate_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния FSM
class ReportStates(StatesGroup):
    choosing_report_type = State()
    waiting_for_dialog_text = State()
    waiting_for_product_info = State()

# Инициализация бота
bot = Bot(token=Config.BOT_TOKEN, base_url=Config.TELEGRAM_API_BASE_URL)
dp = Dispatcher()

# ---------- Вспомогательная функция показа выбора типа ----------
async def show_report_type_choice(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Клиентский отчёт", callback_data="report_client")
    builder.button(text="🎨 Дизайн сайта", callback_data="report_design")
    builder.button(text="🛒 Карточка товара", callback_data="report_product")
    builder.adjust(1)
    await message.answer("Выберите тип отчёта:", reply_markup=builder.as_markup())
    await state.set_state(ReportStates.choosing_report_type)

# ---------- Команда /start ----------
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤖 Привет! Я бот для генерации отчётов по диалогам с клиентами.\n"
        "Выберите тип отчёта, отправьте текст диалога, и я создам PDF-отчёт.\n"
        "Для карточки товара можно отправить до 10 товаров (каждый с новой строки, формат: 'Название, цена').\n"
        "Используйте /help для справки."
    )
    await show_report_type_choice(message, state)

# ---------- Команда /help ----------
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🤖 Бот для генерации отчётов по диалогам.\n"
        "Команды:\n"
        "/start - начать работу, выбрать тип отчёта\n"
        "/help - справка\n"
        "/cancel - отменить текущее действие\n"
        "После выбора типа отправьте текст диалога или файл .txt.\n"
        "Для карточки товара введите название и цену через запятую (можно несколько строк, до 10 товаров)."
    )

# ---------- Команда /cancel ----------
@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено. Начните заново /start.")

# ---------- Обработка выбора типа отчёта ----------
@dp.callback_query(StateFilter(ReportStates.choosing_report_type), F.data.startswith("report_"))
async def process_report_type(callback: CallbackQuery, state: FSMContext):
    report_type = callback.data.split("_")[1]
    await state.update_data(report_type=report_type)
    await callback.answer()
    if report_type == "product":
        await callback.message.answer(
            "Введите товары (каждый с новой строки) в формате:\n"
            "Название, цена\n"
            "Например:\n"
            "Ноутбук, 50000\n"
            "Телефон, 30000\n"
            "Можно до 10 товаров."
        )
        await state.set_state(ReportStates.waiting_for_product_info)
    else:
        await callback.message.answer("Отправьте текст диалога (или пришлите текстовый файл .txt):")
        await state.set_state(ReportStates.waiting_for_dialog_text)
    await callback.message.delete()

# ---------- Обработка текста диалога (для client и design) - ВОССТАНОВЛЕНА ----------
@dp.message(StateFilter(ReportStates.waiting_for_dialog_text))
async def handle_dialog_text(message: Message, state: FSMContext):
    text = None
    # Проверяем, пришёл ли файл
    if message.document:
        if message.document.mime_type == "text/plain" and message.document.file_name.endswith(".txt"):
            file = await bot.get_file(message.document.file_id)
            file_content = await bot.download_file(file.file_path)
            text = file_content.read().decode("utf-8")
        else:
            await message.answer("Пожалуйста, отправьте текстовый файл .txt или просто текст.")
            return
    elif message.text:
        text = message.text
    else:
        await message.answer("Пожалуйста, отправьте текстовое сообщение или файл .txt.")
        return

    if not text:
        await message.answer("Текст не получен. Попробуйте ещё раз.")
        return

    data = await state.get_data()
    report_type = data.get("report_type")
    if not report_type:
        await message.answer("Ошибка: тип отчёта не выбран. Начните заново /start.")
        await state.clear()
        return

    await message.answer("⏳ Обрабатываю диалог с помощью ИИ...")

    try:
        # Получаем структурированные данные от LLM
        extracted_data = process_dialog_with_ai(text, report_type)
        logger.info(f"Извлечены данные: {extracted_data}")
        extracted_data["date"] = datetime.now().strftime("%d.%m.%Y")

        # Для дизайн-отчёта генерируем изображение и встраиваем в base64
        if report_type == "design":
            image_prompt = extracted_data.get("image_prompt", "")
            if image_prompt:
                await message.answer("🎨 Генерирую пример дизайна...")
                try:
                    image_bytes = await generate_image(image_prompt, width=512, height=512)
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    extracted_data["image_base64"] = image_base64
                except Exception as e:
                    logger.error(f"Ошибка генерации изображения: {e}")
                    await message.answer("⚠️ Не удалось сгенерировать изображение. Продолжаю без него.")
                    extracted_data["image_base64"] = ""
            else:
                extracted_data["image_base64"] = ""

        # Выбор шаблона
        template_map = {
            "client": "client_report.html",
            "design": "design_report.html"
        }
        template = template_map.get(report_type)
        if not template:
            await message.answer("Ошибка: неизвестный тип отчёта.")
            return

        # Генерируем PDF
        pdf_path = generate_pdf(extracted_data, template)
        await message.answer("✅ Отчёт готов!")

        pdf_file = FSInputFile(pdf_path)
        await bot.send_document(
            chat_id=message.chat.id,
            document=pdf_file,
            caption="📄 Ваш отчёт в PDF."
        )

        await state.clear()
        await show_report_type_choice(message, state)

    except Exception as e:
        logger.error(f"Ошибка при генерации отчёта: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()
        await show_report_type_choice(message, state)

# ---------- Обработка для карточки товара (множественные товары) ----------
@dp.message(StateFilter(ReportStates.waiting_for_product_info))
async def handle_product_info(message: Message, state: FSMContext):
    text = message.text
    if not text:
        await message.answer("Пожалуйста, введите товары.")
        return

    # Разбиваем на строки и фильтруем пустые
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        await message.answer("Не найдено ни одной строки с товаром.")
        return

    # Ограничение до 10 товаров
    if len(lines) > 10:
        await message.answer(f"⚠️ Обнаружено {len(lines)} товаров. Будет обработано только первые 10.")
        lines = lines[:10]

    await message.answer(f"⏳ Генерирую карточки для {len(lines)} товаров...")

    product_data_list = []
    errors = []

    for i, line in enumerate(lines, start=1):
        if ',' not in line:
            errors.append(f"Строка {i}: '{line}' — пропущена (нет запятой).")
            continue

        parts = line.split(',', 1)
        if len(parts) != 2:
            errors.append(f"Строка {i}: '{line}' — неверный формат, пропущена.")
            continue

        product_name = parts[0].strip()
        price = parts[1].strip()

        if not product_name or not price:
            errors.append(f"Строка {i}: '{line}' — пустое название или цена, пропущена.")
            continue

        try:
            product_data = generate_product_card_data(product_name, price)
            logger.info(f"Товар {i}: {product_data}")

            image_prompt = product_data.get("image_prompt", "")
            if image_prompt:
                try:
                    image_bytes = await generate_image(image_prompt, width=512, height=512)
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    product_data["image_base64"] = image_base64
                except Exception as e:
                    logger.error(f"Ошибка генерации изображения для {product_name}: {e}")
                    product_data["image_base64"] = ""
            else:
                product_data["image_base64"] = ""

            product_data["date"] = datetime.now().strftime("%d.%m.%Y")
            product_data_list.append(product_data)

        except Exception as e:
            logger.error(f"Ошибка обработки товара '{line}': {e}")
            errors.append(f"Товар '{line}' не удалось обработать: {str(e)}")

    if not product_data_list:
        await message.answer("❌ Не удалось сгенерировать ни одной карточки. Проверьте формат ввода.")
        if errors:
            await message.answer("\n".join(errors[:5]))
        return

    try:
        context = {
            "products": product_data_list,
            "date": datetime.now().strftime("%d.%m.%Y")
        }
        pdf_path = generate_pdf(context, "multiple_product_cards.html")

        pdf_file = FSInputFile(pdf_path)
        await bot.send_document(
            chat_id=message.chat.id,
            document=pdf_file,
            caption=f"🛒 Сгенерировано {len(product_data_list)} карточек товаров."
        )

        if errors:
            error_text = "⚠️ При обработке некоторых товаров возникли ошибки:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                error_text += f"\n... и ещё {len(errors)-5} ошибок."
            await message.answer(error_text)

        await state.clear()
        await show_report_type_choice(message, state)

    except Exception as e:
        logger.error(f"Ошибка при генерации PDF с карточками: {e}")
        await message.answer(f"❌ Произошла ошибка при создании PDF: {str(e)}")
        await state.clear()
        await show_report_type_choice(message, state)


# ---------- Запуск ----------
async def main():
    Config.validate()
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())