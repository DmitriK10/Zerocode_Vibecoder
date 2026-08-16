import json
import os
from datetime import datetime
from typing import List, Dict

# Абсолютный путь к папке с данными
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
APPOINTMENTS_FILE = os.path.join(DATA_DIR, "appointments.json")

class AppointmentManager:
    def __init__(self):
        self._ensure_data_dir()
        self._ensure_file()

    def _ensure_data_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def _ensure_file(self):
        if not os.path.exists(APPOINTMENTS_FILE):
            with open(APPOINTMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load(self) -> List[Dict]:
        with open(APPOINTMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: List[Dict]):
        with open(APPOINTMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_appointment(self, user_id: int, user_name: str, topic: str,
                           date_time: str, contact: str) -> Dict:
        appointments = self._load()
        new_record = {
            "id": len(appointments) + 1,
            "user_id": user_id,
            "user_name": user_name,
            "topic": topic,
            "date_time": date_time,
            "contact": contact,
            "created_at": datetime.now().isoformat()
        }
        appointments.append(new_record)
        self._save(appointments)
        return new_record

    def get_appointments_by_user(self, user_id: int) -> List[Dict]:
        appointments = self._load()
        return [a for a in appointments if a["user_id"] == user_id]

    def get_all_appointments(self) -> List[Dict]:
        return self._load()