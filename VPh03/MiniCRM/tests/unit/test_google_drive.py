"""
tests/unit/test_google_drive.py
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from google_integration.google_drive import GoogleDrive

@pytest.fixture
def mock_google_drive():
    # Мокаем discovery.build, чтобы он не обращался к сети
    with patch('google_integration.google_drive.build') as mock_build:
        mock_build.return_value = Mock()
        with patch('google_integration.google_drive.InstalledAppFlow') as mock_flow:
            mock_creds = Mock()
            mock_creds.valid = True
            mock_flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_creds
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=b'')):
                    with patch('pickle.load', return_value=None):
                        with patch('pickle.dump'):
                            drive = GoogleDrive("fake_client_secret.json", "fake_token.pickle")
                            drive._service = Mock()
                            return drive

def test_list_files(mock_google_drive):
    mock_response = {
        "files": [{"id": "1", "name": "file1", "mimeType": "type"}]
    }
    mock_google_drive._service.files().list().execute.return_value = mock_response
    files = mock_google_drive.list_files("folder_id")
    assert len(files) == 1
    assert files[0]["id"] == "1"

def test_create_spreadsheet(mock_google_drive):
    mock_google_drive._service.files().create().execute.return_value = {"id": "new_id"}
    file_id = mock_google_drive.create_google_spreadsheet("Test", "parent")
    assert file_id == "new_id"

def test_delete_file(mock_google_drive):
    mock_google_drive.delete_file("file_id")
    mock_google_drive._service.files().delete.assert_called_once_with(fileId="file_id")