import pytest
import json
from src.repository import JsonProjectRepository

@pytest.fixture
def temp_json_file(tmp_path):
    file_path = tmp_path / "projects.json"
    data = {
        "projects": [
            {"title": "Test Project", "description": "A test description."}
        ]
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    return str(file_path)

def test_get_projects_success(temp_json_file):
    repo = JsonProjectRepository(temp_json_file)
    projects = repo.get_projects()
    assert len(projects) == 1
    assert projects[0]["title"] == "Test Project"

def test_get_projects_empty_file(tmp_path):
    file_path = tmp_path / "empty.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({}, f)
    repo = JsonProjectRepository(str(file_path))
    projects = repo.get_projects()
    assert projects == []

def test_get_projects_malformed_json(tmp_path):
    file_path = tmp_path / "malformed.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("not a json")
    repo = JsonProjectRepository(str(file_path))
    projects = repo.get_projects()
    assert projects == []

def test_get_projects_file_not_found(tmp_path):
    non_existent = tmp_path / "non_existent.json"
    repo = JsonProjectRepository(str(non_existent))
    projects = repo.get_projects()
    assert projects == []
