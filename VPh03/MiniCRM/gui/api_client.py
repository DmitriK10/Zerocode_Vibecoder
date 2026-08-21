"""
Клиент для отправки HTTP-запросов к FastAPI бэкенду.
"""

import requests
from typing import List, Dict, Any, Optional


class CRMClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    # ---------- Клиенты ----------
    def get_clients(self, params: Optional[Dict] = None) -> List[Dict]:
        return self._request("GET", "/clients", params=params)

    def create_client(self, data: Dict) -> Dict:
        return self._request("POST", "/clients", json=data)

    def update_client(self, client_id: int, data: Dict) -> Dict:
        return self._request("PUT", f"/clients/{client_id}", json=data)

    def delete_client(self, client_id: int) -> Dict:
        return self._request("DELETE", f"/clients/{client_id}")

    # ---------- Сделки ----------
    def get_deals(self, params: Optional[Dict] = None) -> List[Dict]:
        return self._request("GET", "/deals", params=params)

    def create_deal(self, data: Dict) -> Dict:
        return self._request("POST", "/deals", json=data)

    def update_deal(self, deal_id: int, data: Dict) -> Dict:
        return self._request("PUT", f"/deals/{deal_id}", json=data)

    def delete_deal(self, deal_id: int) -> Dict:
        return self._request("DELETE", f"/deals/{deal_id}")

    # ---------- Задачи ----------
    def get_tasks(self, params: Optional[Dict] = None) -> List[Dict]:
        return self._request("GET", "/tasks", params=params)

    def create_task(self, data: Dict) -> Dict:
        return self._request("POST", "/tasks", json=data)

    def update_task(self, task_id: int, data: Dict) -> Dict:
        return self._request("PUT", f"/tasks/{task_id}", json=data)

    def delete_task(self, task_id: int) -> Dict:
        return self._request("DELETE", f"/tasks/{task_id}")