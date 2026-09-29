import httpx

def check_proxy():
    proxy_url = "http://proxyapi.ru:8080"
    print(f"Проверка доступности прокси: {proxy_url}...")
    try:
        with httpx.Client(proxy=proxy_url, timeout=5.0) as client:
            response = client.get("http://google.com")
            print(f"✅ Прокси работает! Статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Прокси НЕДОСТУПЕН: {e}")

def check_direct():
    print("Проверка прямого доступа к api.openai.com...")
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get("https://api.openai.com/v1/models", headers={"Authorization": "Bearer test"})
            print(f"✅ Прямой доступ есть! Статус: {response.status_code} (401 - норма, значит сервер виден)")
    except Exception as e:
        print(f"❌ Прямой доступ заблокирован или отсутствует: {e}")

if __name__ == "__main__":
    check_proxy()
    check_direct()
