import os
import sys
import logging
from dotenv import load_dotenv
from pathlib import Path

# Добавляем текущую папку в путь для импорта
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

from src.prompt_loader import PromptLoader
from src.openai_client import OpenAIClient
from src.prompt_processor import PromptProcessor
from src.chain import run_chain
from src.config import Config

# Настройка логирования
log_level = Config.LOG_LEVEL
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    load_dotenv()  # загружаем .env (Config уже загрузил, но оставим)
    Config.validate()
    api_key = Config.OPENAI_API_KEY
    model = Config.OPENAI_MODEL
    logger.info(f"Используемая модель: {model}")

    # Загружаем промпты (если есть)
    prompts_dir = os.path.join(base_dir, "prompts")
    loader = PromptLoader(prompts_dir)
    all_prompts = loader.load_all_prompts()

    # Если промптов нет – сразу переходим в режим цепочки
    if not all_prompts:
        logger.warning("Папка prompts пуста или отсутствует. Переход в режим генерации статьи.")
        print("Не найдено JSON-файлов с промптами. Будет запущен режим цепочки (генерация статьи).")
        topic = input("\nВведите тему статьи: ").strip()
        if not topic:
            print("Тема не может быть пустой.")
            return
        out_dir = Path(base_dir) / "output"
        try:
            result_path = run_chain(topic, out_dir)
            print(f"\nСтатья успешно сгенерирована: {result_path}")
        except Exception as e:
            logger.error(f"Ошибка при генерации статьи: {e}", exc_info=True)
            print(f"Ошибка: {e}")
        return

    # Если промпты есть – показываем меню
    print("Доступные кейс-промпты:")
    items = list(all_prompts.items())
    for idx, (filename, data) in enumerate(items, start=1):
        name = data.get("name", filename)
        print(f"{idx}. {name} ({filename})")
    chain_idx = len(items) + 1
    print(f"{chain_idx}. [Спец. режим] Генерация статьи через цепочку (chain)")

    choice = input("\nВыберите номер кейса (или 'q' для выхода): ").strip()
    if choice.lower() == 'q':
        logger.info("Выход по запросу пользователя")
        return

    # Режим цепочки
    if choice == str(chain_idx):
        topic = input("\nВведите тему статьи: ").strip()
        if not topic:
            print("Тема не может быть пустой.")
            return
        out_dir = Path(base_dir) / "output"
        try:
            result_path = run_chain(topic, out_dir)
            print(f"\nСтатья успешно сгенерирована: {result_path}")
        except Exception as e:
            logger.error(f"Ошибка при генерации статьи: {e}", exc_info=True)
            print(f"Ошибка: {e}")
        return

    # Обычный режим работы с промптами
    try:
        idx = int(choice) - 1
        selected_filename = list(all_prompts.keys())[idx]
        selected_prompt = all_prompts[selected_filename]
        logger.info(f"Выбран кейс: {selected_filename}")
    except (ValueError, IndexError):
        logger.warning(f"Неверный выбор: {choice}")
        print("Неверный выбор.")
        return

    print("\nВведите текст/задачу для обработки (для завершения ввода введите 'END' в новой строке):")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    user_input = "\n".join(lines).strip()
    if not user_input:
        logger.warning("Пользователь ввёл пустой текст")
        print("Ввод не может быть пустым.")
        return

    temp_str = input("\nВведите температуру (0.0 - 2.0, по умолчанию 0.7): ").strip()
    temperature = 0.7
    if temp_str:
        try:
            temperature = float(temp_str)
            if temperature < 0.0 or temperature > 2.0:
                print("Температура должна быть от 0.0 до 2.0. Использую 0.7.")
                temperature = 0.7
        except ValueError:
            print("Неверное значение. Использую 0.7.")

    stream_choice = input("\nВыводить ответ по частям (streaming)? (y/n, по умолчанию n): ").strip().lower()
    use_stream = stream_choice == 'y'

    client = OpenAIClient(api_key, model=model)
    processor = PromptProcessor(client)

    print("\nОбработка запроса...")
    full_response = ""
    try:
        if use_stream:
            print("\n" + "="*50)
            print("ПОТОКОВЫЙ ОТВЕТ:")
            print("="*50)
            for chunk in processor.process_stream(selected_prompt, user_input, temperature):
                print(chunk, end="")
                full_response += chunk
            print("\n" + "="*50)
        else:
            result = processor.process(selected_prompt, user_input, temperature)
            full_response = result
            print("\n" + "="*50)
            print("РЕЗУЛЬТАТ:")
            print("="*50)
            print(result)
            print("="*50)
        logger.info("Ответ успешно получен")
    except Exception as e:
        logger.error(f"Ошибка при обработке: {e}", exc_info=True)
        print(f"Произошла ошибка: {e}")
        return

    save_choice = input("\nСохранить результат в файл? (y/n, по умолчанию n): ").strip().lower()
    if save_choice == 'y':
        filename = input("Введите имя файла (по умолчанию result.txt): ").strip()
        if not filename:
            filename = "result.txt"
        if not os.path.isabs(filename):
            filename = os.path.join(base_dir, filename)
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(full_response)
            logger.info(f"Результат сохранён в {filename}")
            print(f"Результат сохранён в {filename}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла: {e}", exc_info=True)
            print(f"Не удалось сохранить файл: {e}")

if __name__ == "__main__":
    main()