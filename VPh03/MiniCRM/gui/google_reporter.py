"""
Логика формирования отчётов и выгрузки в Google Sheets через интеграцию.
"""
import logging
from typing import List, Dict, Any

from google_integration.auth import GoogleAuthManager
from google_integration.drive_client import GoogleDriveClient
from google_integration.sheets_client import GoogleSheetsClient
from gui.api_client import CRMClient

logger = logging.getLogger(__name__)


class GoogleReporter:
    def __init__(
        self,
        api_client: CRMClient,
        auth_manager: GoogleAuthManager,
        folder_id: str,
        use_user_auth: bool = True,
    ):
        self.api = api_client
        self.auth = auth_manager
        self.folder_id = folder_id
        self.use_user_auth = use_user_auth
        self.drive = GoogleDriveClient(auth_manager, use_user_auth)
        self.sheets = GoogleSheetsClient(auth_manager, use_user_auth)

    def export_clients_report(self) -> Dict[str, Any]:
        data = self.api.get_clients()
        total = len(data)
        with_company = sum(1 for c in data if c.get("company"))
        without_company = total - with_company

        title = "Клиенты (отчёт)"
        file_meta = self.drive.create_file(
            name=title,
            mime_type="application/vnd.google-apps.spreadsheet",
            folder_id=self.folder_id,
        )
        spreadsheet_id = file_meta["id"]

        headers = ["Имя", "Email", "Компания", "Телефон", "Статус"]
        rows = [headers]
        for client in data:
            rows.append([
                client.get("name", ""),
                client.get("email", ""),
                client.get("company", ""),
                client.get("phone", ""),
                client.get("status", ""),
            ])
        rows.append([])
        rows.append(["Всего клиентов", total])
        rows.append(["С компанией", with_company])
        rows.append(["Без компании", without_company])

        self.sheets.update_sheet(spreadsheet_id, "A1", rows)

        file_info = self.drive.get_file_metadata(spreadsheet_id)
        return {"file_id": spreadsheet_id, "web_link": file_info.get("webViewLink")}

    def export_deals_report(self) -> Dict[str, Any]:
        data = self.api.get_deals()
        total = len(data)
        total_amount = sum(d.get("amount", 0) for d in data if d.get("amount"))
        avg_amount = total_amount / total if total else 0
        status_counts = {}
        for d in data:
            status = d.get("status", "Неизвестно")
            status_counts[status] = status_counts.get(status, 0) + 1

        title = "Сделки (отчёт)"
        file_meta = self.drive.create_file(
            name=title,
            mime_type="application/vnd.google-apps.spreadsheet",
            folder_id=self.folder_id,
        )
        spreadsheet_id = file_meta["id"]

        headers = ["Название", "Сумма", "Статус", "ID клиента"]
        rows = [headers]
        for deal in data:
            rows.append([
                deal.get("title", ""),
                deal.get("amount", ""),
                deal.get("status", ""),
                deal.get("client_id", ""),
            ])
        rows.append([])
        rows.append(["Всего сделок", total])
        rows.append(["Общая сумма", total_amount])
        rows.append(["Средняя сумма", avg_amount])
        for status, count in status_counts.items():
            rows.append([f"Статус '{status}'", count])

        self.sheets.update_sheet(spreadsheet_id, "A1", rows)
        file_info = self.drive.get_file_metadata(spreadsheet_id)
        return {"file_id": spreadsheet_id, "web_link": file_info.get("webViewLink")}

    def export_tasks_report(self) -> Dict[str, Any]:
        data = self.api.get_tasks()
        total = len(data)
        done = sum(1 for t in data if t.get("is_done") == 1)
        pending = total - done

        title = "Задачи (отчёт)"
        file_meta = self.drive.create_file(
            name=title,
            mime_type="application/vnd.google-apps.spreadsheet",
            folder_id=self.folder_id,
        )
        spreadsheet_id = file_meta["id"]

        headers = ["Название", "Описание", "Срок", "Выполнена", "ID клиента", "ID сделки"]
        rows = [headers]
        for task in data:
            rows.append([
                task.get("title", ""),
                task.get("description", ""),
                task.get("due_date", ""),
                "Да" if task.get("is_done") else "Нет",
                task.get("client_id", ""),
                task.get("deal_id", ""),
            ])
        rows.append([])
        rows.append(["Всего задач", total])
        rows.append(["Выполнено", done])
        rows.append(["Не выполнено", pending])

        self.sheets.update_sheet(spreadsheet_id, "A1", rows)
        file_info = self.drive.get_file_metadata(spreadsheet_id)
        return {"file_id": spreadsheet_id, "web_link": file_info.get("webViewLink")}