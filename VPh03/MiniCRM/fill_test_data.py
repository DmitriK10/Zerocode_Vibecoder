"""
fill_test_data.py
Генерация реалистичных тестовых данных для CRM.
"""

import requests
import random
from faker import Faker

API_BASE = "http://localhost:8000"
fake = Faker("ru_RU")

CLIENT_STATUSES = ["Активен", "Архив"]
DEAL_STATUSES = ["Новая", "В работе", "Закрыта успешно", "Закрыта без результата"]

def create_clients(n=300):
    print(f"Создание {n} клиентов...")
    for _ in range(n):
        name = fake.name()
        company = fake.company() if random.random() > 0.4 else None
        email = fake.email() if random.random() > 0.3 else None
        phone = fake.phone_number() if random.random() > 0.3 else None
        status = random.choice(CLIENT_STATUSES)
        data = {
            "name": name,
            "company": company,
            "email": email,
            "phone": phone,
            "status": status
        }
        try:
            resp = requests.post(f"{API_BASE}/clients/", json=data)
            resp.raise_for_status()
        except Exception as e:
            print(f"Ошибка при создании клиента: {e}")

def create_deals(client_ids, n=300):
    print(f"Создание {n} сделок...")
    for _ in range(n):
        title = fake.bs()
        amount = round(random.uniform(1000, 500000), 2)
        status = random.choice(DEAL_STATUSES)
        client_id = random.choice(client_ids) if client_ids and random.random() > 0.3 else None
        data = {
            "title": title,
            "amount": amount,
            "status": status,
            "client_id": client_id
        }
        try:
            resp = requests.post(f"{API_BASE}/deals/", json=data)
            resp.raise_for_status()
        except Exception as e:
            print(f"Ошибка при создании сделки: {e}")

def create_tasks(client_ids, deal_ids, n=400):
    print(f"Создание {n} задач...")
    for _ in range(n):
        title = fake.sentence()
        description = fake.text() if random.random() > 0.5 else None
        due_date = fake.date_time_between(start_date="-30d", end_date="+30d").isoformat()
        is_done = random.choice([0, 1])
        client_id = random.choice(client_ids) if client_ids and random.random() > 0.3 else None
        deal_id = random.choice(deal_ids) if deal_ids and random.random() > 0.3 else None
        data = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "is_done": is_done,
            "client_id": client_id,
            "deal_id": deal_id
        }
        try:
            resp = requests.post(f"{API_BASE}/tasks/", json=data)
            resp.raise_for_status()
        except Exception as e:
            print(f"Ошибка при создании задачи: {e}")

def main():
    # Получаем существующих клиентов для связей
    try:
        resp = requests.get(f"{API_BASE}/clients/?limit=1000")
        resp.raise_for_status()
        clients = resp.json()
        client_ids = [c["id"] for c in clients]
    except:
        client_ids = []

    create_clients(300)
    # Обновляем список клиентов
    try:
        resp = requests.get(f"{API_BASE}/clients/?limit=1000")
        resp.raise_for_status()
        clients = resp.json()
        client_ids = [c["id"] for c in clients]
    except:
        client_ids = []

    create_deals(client_ids, 300)

    # Получаем сделки для задач
    try:
        resp = requests.get(f"{API_BASE}/deals/?limit=1000")
        resp.raise_for_status()
        deals = resp.json()
        deal_ids = [d["id"] for d in deals]
    except:
        deal_ids = []

    create_tasks(client_ids, deal_ids, 400)
    print("Генерация данных завершена!")

if __name__ == "__main__":
    main()