import sys
import time
from models.base import BaseAIModel
from models.openai_model import OpenAIModel
from models.deepseek_model import DeepSeekReasoningModel
from conversation import ConversationManager
from config import Config

def print_banner():
    """Выводит красивый баннер при запуске."""
    print("=" * 60)
    print("         🤖 УМНЫЙ ТЕКСТОВЫЙ ПОМОЩНИК с ИИ")
    print("=" * 60)
    print("  Команды: /exit - выход, /clear - очистить историю")
    print("           /switch - переключить модель, /info - информация о модели")
    print("=" * 60)

def select_model() -> BaseAIModel:
    """Предлагает пользователю выбрать модель и возвращает экземпляр."""
    print("\nВыберите режим работы:")
    print("1. Обычная модель (gpt-4o-mini, бесплатно)")
    print("2. Думающая модель (DeepSeek R1 с reasoning, бесплатно)")
    
    while True:
        choice = input("Ваш выбор (1/2): ").strip()
        if choice == "1":
            model = OpenAIModel()
            print(f"\n[OK] Выбрана: {model.get_model_info()}")
            return model
        elif choice == "2":
            model = DeepSeekReasoningModel()
            print(f"\n[OK] Выбрана: {model.get_model_info()}")
            return model
        else:
            print("Неверный ввод. Пожалуйста, введите 1 или 2.")

def main():
    """Основной цикл приложения."""
    print_banner()
    
    # Инициализация менеджера истории (автоматически загружает прошлый диалог)
    conv = ConversationManager()
    
    # Выбор модели при старте
    current_model = select_model()
    
    # Главный цикл
    while True:
        try:
            # Ввод пользователя
            user_input = input("\n🧑 Вы: ").strip()
            
            if not user_input:
                continue
            
            # Обработка команд
            if user_input.lower() == "/exit":
                print("👋 До свидания! Сохраняю историю...")
                conv.save_history()
                sys.exit(0)
            elif user_input.lower() == "/clear":
                conv.clear_history()
                print("[OK] История диалога очищена (системный промпт сохранён).")
                continue
            elif user_input.lower() == "/switch":
                print("\n[INFO] Переключение модели...")
                new_model = select_model()
                current_model = new_model
                continue
            elif user_input.lower() == "/info":
                print(f"\n[INFO] Текущая модель: {current_model.get_model_info()}")
                print(f"[INFO] В истории {len(conv.get_messages())} сообщений.")
                continue
            
            # Добавляем сообщение пользователя в историю
            conv.add_user_message(user_input)
            
            # Генерация ответа от выбранной модели
            print("🤖 Ассистент: ", end="", flush=True)
            start_time = time.time()
            
            try:
                response = current_model.generate_response(conv.get_messages())
                elapsed = time.time() - start_time
                print(response)
                print(f"\n[⏱️ Время ответа: {elapsed:.2f} сек]")
                conv.add_assistant_message(response)
                conv.save_history()
            except Exception as e:
                print(f"\n[ERROR] {e}")
                print("[INFO] Попробуйте переключить модель (/switch) или проверить соединение.")
                # Удаляем последнее сообщение пользователя, которое не обработалось
                if conv.messages and conv.messages[-1]["role"] == "user":
                    conv.messages.pop()
                continue
                
        except KeyboardInterrupt:
            print("\n\n[INFO] Прерывание по Ctrl+C. Сохраняю историю и выхожу.")
            conv.save_history()
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] Непредвиденная ошибка: {e}")
            print("[INFO] Продолжаем работу. Введите /exit для выхода.")

if __name__ == "__main__":
    main()