import os
import sys
import logging
from dotenv import load_dotenv

# Настройка логирования
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем корневую папку в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.prompt_loader import PromptLoader
from src.openai_client import OpenAIClient
from src.prompt_processor import PromptProcessor

def main():
    # Загрузка переменных окружения
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Не задан OPENAI_API_KEY в .env")
        print("Ошибка: не задан OPENAI_API_KEY в .env")
        return

    # Чтение модели из окружения
    model = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")
    logger.info(f"Используемая модель: {model}")

    # Путь к папке с промптами
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")
    loader = PromptLoader(prompts_dir)
    
    # Загружаем все промпты
    all_prompts = loader.load_all_prompts()
    if not all_prompts:
        logger.error("Не найдено ни одного JSON-файла с промптами.")
        print("Не найдено ни одного JSON-файла с промптами.")
        return

    # Выводим список доступных кейсов
    print("Доступные кейс-промпты:")
    for idx, (filename, data) in enumerate(all_prompts.items(), start=1):
        name = data.get("name", filename)
        print(f"{idx}. {name} ({filename})")
    
    # Выбор пользователя
    choice = input("\nВыберите номер кейса (или 'q' для выхода): ").strip()
    if choice.lower() == 'q':
        logger.info("Выход по запросу пользователя")
        return
    try:
        idx = int(choice) - 1
        selected_filename = list(all_prompts.keys())[idx]
        selected_prompt = all_prompts[selected_filename]
        logger.info(f"Выбран кейс: {selected_filename}")
    except (ValueError, IndexError):
        logger.warning(f"Неверный выбор: {choice}")
        print("Неверный выбор.")
        return

    # Запрос пользовательского ввода
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

    # Запрос температуры
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

    # Потоковый режим?
    stream_choice = input("\nВыводить ответ по частям (streaming)? (y/n, по умолчанию n): ").strip().lower()
    use_stream = stream_choice == 'y'

    # Создаём клиент и процессор
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

    # Сохранение в файл
    save_choice = input("\nСохранить результат в файл? (y/n, по умолчанию n): ").strip().lower()
    if save_choice == 'y':
        filename = input("Введите имя файла (по умолчанию result.txt): ").strip()
        if not filename:
            filename = "result.txt"
        # Если путь относительный, сохраняем в корень проекта
        if not os.path.isabs(filename):
            filename = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename)
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