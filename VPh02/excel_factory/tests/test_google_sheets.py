"""
test_google_sheets.py
Тесты для модуля google_sheets с использованием моков.
"""

import sys
from pathlib import Path
# Добавляем корневую папку проекта в sys.path для корректного импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, patch
from google_sheets import CredentialsProvider, SheetsClient
from googleapiclient.errors import HttpError


@pytest.fixture
def mock_credentials_provider():
    """Фикстура для провайдера учётных данных (замоканы)."""
    provider = Mock(spec=CredentialsProvider)
    provider.get_credentials.return_value = Mock()
    return provider


@pytest.fixture
def sheets_client(mock_credentials_provider):
    """Создаёт экземпляр SheetsClient с замоканным провайдером."""
    client = SheetsClient(mock_credentials_provider, "test_spreadsheet_id")
    # Подменяем внутренний _service и _sheets_api, чтобы не делать реальные запросы
    client._service = Mock()
    client._sheets_api = Mock()
    return client


def test_read_range(sheets_client):
    """Проверка чтения диапазона."""
    mock_values = {'values': [['a', 'b'], ['c', 'd']]}
    # Правильная настройка мока: get вызывается только при фактическом вызове
    sheets_client._sheets_api.values().get.return_value.execute.return_value = mock_values

    result = sheets_client.read_range("Sheet1!A1:B2")
    assert result == [['a', 'b'], ['c', 'd']]
    sheets_client._sheets_api.values().get.assert_called_once_with(
        spreadsheetId="test_spreadsheet_id",
        range="Sheet1!A1:B2"
    )


def test_read_range_http_error(sheets_client):
    """Проверка обработки ошибки HTTP при чтении."""
    sheets_client._sheets_api.values().get().execute.side_effect = HttpError(
        resp=Mock(status=404), content=b'Not Found'
    )
    with pytest.raises(RuntimeError, match="Ошибка чтения диапазона"):
        sheets_client.read_range("Sheet1!A1")


def test_get_sheet_names(sheets_client):
    """Проверка получения списка листов."""
    mock_response = {
        'sheets': [
            {'properties': {'title': 'Лист1'}},
            {'properties': {'title': 'Лист2'}}
        ]
    }
    sheets_client._sheets_api.get().execute.return_value = mock_response

    names = sheets_client.get_sheet_names()
    assert names == ['Лист1', 'Лист2']


def test_write_range(sheets_client):
    """Проверка записи данных."""
    values = [['x', 'y'], ['z', 'w']]
    sheets_client.write_range("Sheet1!A1", values, "USER_ENTERED")
    sheets_client._sheets_api.values().update.assert_called_once_with(
        spreadsheetId="test_spreadsheet_id",
        range="Sheet1!A1",
        valueInputOption="USER_ENTERED",
        body={'values': values}
    )


def test_add_sheet(sheets_client):
    """Проверка создания нового листа."""
    sheets_client.add_sheet("Новый лист")
    call_args = sheets_client._sheets_api.batchUpdate.call_args
    assert call_args is not None
    kwargs = call_args[1]
    assert kwargs['spreadsheetId'] == "test_spreadsheet_id"
    requests = kwargs['body']['requests']
    assert len(requests) == 1
    assert 'addSheet' in requests[0]
    assert requests[0]['addSheet']['properties']['title'] == "Новый лист"


def test_set_cell_format(sheets_client):
    """Проверка установки формата ячеек."""
    # Мокаем get_sheet_id_by_name
    sheets_client.get_sheet_id_by_name = Mock(return_value=123)
    sheets_client.set_cell_format(
        sheet_name="Лист1",
        start_row=1, end_row=2,
        start_col=1, end_col=3,
        format_dict={'textFormat': {'bold': True}}
    )
    call_args = sheets_client._sheets_api.batchUpdate.call_args
    assert call_args is not None
    requests = call_args[1]['body']['requests']
    assert len(requests) == 1
    repeat_cell = requests[0]['repeatCell']
    assert repeat_cell['range']['sheetId'] == 123
    assert repeat_cell['range']['startRowIndex'] == 0
    assert repeat_cell['range']['endRowIndex'] == 2
    assert repeat_cell['range']['startColumnIndex'] == 0
    assert repeat_cell['range']['endColumnIndex'] == 3
    assert repeat_cell['cell']['userEnteredFormat'] == {'textFormat': {'bold': True}}
    assert repeat_cell['fields'] == 'userEnteredFormat'


def test_merge_cells(sheets_client):
    """Проверка объединения ячеек."""
    sheets_client.get_sheet_id_by_name = Mock(return_value=456)
    sheets_client.merge_cells(
        sheet_name="Лист1",
        start_row=2, end_row=4,
        start_col=3, end_col=5
    )
    call_args = sheets_client._sheets_api.batchUpdate.call_args
    requests = call_args[1]['body']['requests']
    assert len(requests) == 1
    merge = requests[0]['mergeCells']
    assert merge['range']['sheetId'] == 456
    assert merge['range']['startRowIndex'] == 1
    assert merge['range']['endRowIndex'] == 4
    assert merge['range']['startColumnIndex'] == 2
    assert merge['range']['endColumnIndex'] == 5
    assert merge['mergeType'] == 'MERGE_ALL'


def test_set_column_width(sheets_client):
    """Проверка установки ширины столбца."""
    sheets_client.get_sheet_id_by_name = Mock(return_value=789)
    sheets_client.set_column_width("Лист1", 3, 200)
    call_args = sheets_client._sheets_api.batchUpdate.call_args
    requests = call_args[1]['body']['requests']
    assert len(requests) == 1
    update_dim = requests[0]['updateDimensionProperties']
    assert update_dim['range']['sheetId'] == 789
    assert update_dim['range']['dimension'] == 'COLUMNS'
    assert update_dim['range']['startIndex'] == 2
    assert update_dim['range']['endIndex'] == 3
    assert update_dim['properties']['pixelSize'] == 200
    assert update_dim['fields'] == 'pixelSize'


def test_credentials_provider_file_not_found():
    """Проверка, что провайдер выбрасывает исключение, если файл не найден."""
    with pytest.raises(FileNotFoundError):
        CredentialsProvider("non_existent.json")


@patch('google_sheets.Credentials.from_service_account_file')
def test_credentials_provider_get_credentials(mock_from_file):
    """Проверка, что провайдер корректно вызывает from_service_account_file."""
    # Мокаем Path.exists, чтобы он всегда возвращал True и не мешал созданию
    with patch('pathlib.Path.exists', return_value=True):
        provider = CredentialsProvider("fake_path.json")
        provider.get_credentials(['scope1'])
    mock_from_file.assert_called_once_with("fake_path.json", scopes=['scope1'])