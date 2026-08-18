from bot.vk_client import VKClient
from bot.handlers import MessageHandler

def main():
    client = VKClient()
    handler = MessageHandler(client)

    print("Бот запущен. Для остановки нажмите Ctrl+C.")
    try:
        client.listen_events(handler.handle)
    except KeyboardInterrupt:
        print("\nОстановка бота...")
    finally:
        print("Бот остановлен.")

if __name__ == "__main__":
    main()