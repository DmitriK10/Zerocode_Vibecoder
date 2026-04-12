import pytest
import sqlite3
import hashlib
import os
import tempfile
import random
import string
import gc
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet
from password_manager import (
    DatabaseManager,
    EncryptionManager,
    PasswordGenerator,
    PasswordCLI
)


# ========================= ФИКСТУРЫ =========================

@pytest.fixture
def temp_db_path():
    """Временный файл БД, возвращает Path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    path = Path(path)
    yield path
    gc.collect()
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            gc.collect()
            try:
                path.unlink()
            except PermissionError:
                pass


@pytest.fixture
def temp_key_path():
    """Временный файл ключа (перед использованием удаляем), возвращает Path."""
    fd, path = tempfile.mkstemp(suffix=".key")
    os.close(fd)
    path = Path(path)
    if path.exists():
        path.unlink()
    yield path
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            pass


@pytest.fixture
def db_manager(temp_db_path):
    """DatabaseManager с временной БД."""
    return DatabaseManager(db_path=temp_db_path)


@pytest.fixture
def enc_manager(temp_key_path):
    """EncryptionManager с временным ключом."""
    return EncryptionManager(key_path=temp_key_path)


@pytest.fixture
def cli_instance(temp_db_path, temp_key_path):
    """Экземпляр PasswordCLI с временными файлами БД и ключа."""
    cli = PasswordCLI()
    cli.db = DatabaseManager(db_path=temp_db_path)
    cli.crypto = EncryptionManager(key_path=temp_key_path)
    return cli


# ========================= ТЕСТЫ DatabaseManager =========================

def test_database_initialization(db_manager):
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='master_password'")
        assert cursor.fetchone() is not None
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='passwords'")
        assert cursor.fetchone() is not None


def test_set_and_get_master_password(db_manager):
    test_hash = hashlib.sha256(b"testpass").hexdigest()
    db_manager.set_master_password(test_hash)
    retrieved = db_manager.get_master_password_hash()
    assert retrieved == test_hash


def test_add_password(db_manager):
    result = db_manager.add_password("google", "user@example.com", "encrypted_data")
    assert result is True
    result2 = db_manager.add_password("google", "other", "encrypted_data2")
    assert result2 is False


def test_get_password(db_manager):
    db_manager.add_password("github", "my_login", "secret_encrypted")
    row = db_manager.get_password("github")
    assert row is not None
    login, encrypted = row
    assert login == "my_login"
    assert encrypted == "secret_encrypted"
    assert db_manager.get_password("unknown") is None


def test_list_passwords(db_manager):
    db_manager.add_password("a", "login_a", "enc_a")
    db_manager.add_password("b", "login_b", "enc_b")
    records = db_manager.list_passwords()
    assert records == [("a", "login_a"), ("b", "login_b")]


def test_delete_password(db_manager):
    db_manager.add_password("delete_me", "login", "enc")
    assert db_manager.delete_password("delete_me") is True
    assert db_manager.get_password("delete_me") is None
    assert db_manager.delete_password("delete_me") is False


# ========================= ТЕСТЫ EncryptionManager =========================

def test_encryption_manager_key_generation(temp_key_path):
    if temp_key_path.exists():
        temp_key_path.unlink()
    assert not temp_key_path.exists()
    em = EncryptionManager(key_path=temp_key_path)
    assert temp_key_path.exists()
    with open(temp_key_path, "rb") as f:
        key = f.read()
    assert len(key) == 44


def test_encryption_manager_load_existing_key(temp_key_path):
    original_key = Fernet.generate_key()
    with open(temp_key_path, "wb") as f:
        f.write(original_key)
    em = EncryptionManager(key_path=temp_key_path)
    assert em.key == original_key


def test_encrypt_decrypt(enc_manager):
    plain = "MySecretPassword123!"
    encrypted = enc_manager.encrypt(plain)
    assert encrypted != plain
    decrypted = enc_manager.decrypt(encrypted)
    assert decrypted == plain


# ========================= ТЕСТЫ PasswordGenerator =========================

def test_password_generator_default():
    pwd = PasswordGenerator.generate()
    assert len(pwd) == 16
    allowed_chars = (
        string.ascii_uppercase +
        string.ascii_lowercase +
        string.digits +
        "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
    )
    assert all(ch in allowed_chars for ch in pwd)


def test_password_generator_custom_length():
    pwd = PasswordGenerator.generate(length=8)
    assert len(pwd) == 8
    pwd = PasswordGenerator.generate(length=64)
    assert len(pwd) == 64


def test_password_generator_only_uppercase():
    # Исправлено: use_upper вместо use_uppercase
    pwd = PasswordGenerator.generate(use_upper=True, use_lower=False, use_digits=False, use_special=False)
    assert all(ch in string.ascii_uppercase for ch in pwd)


def test_password_generator_only_digits():
    # Исправлено: use_digits=True, остальные False
    pwd = PasswordGenerator.generate(use_upper=False, use_lower=False, use_digits=True, use_special=False)
    assert all(ch in string.digits for ch in pwd)


def test_password_generator_no_char_sets_raises():
    with pytest.raises(ValueError, match="Хотя бы один набор символов должен быть включён"):
        PasswordGenerator.generate(use_upper=False, use_lower=False, use_digits=False, use_special=False)


# ========================= ТЕСТЫ PasswordCLI =========================

def test_setup_master_password_first_run(cli_instance):
    assert cli_instance.db.get_master_password_hash() is None
    with patch.object(cli_instance, '_read_secret', side_effect=["my_pass", "my_pass"]):
        cli_instance.setup_master_password()
    saved_hash = cli_instance.db.get_master_password_hash()
    expected_hash = hashlib.sha256(b"my_pass").hexdigest()
    assert saved_hash == expected_hash


def test_setup_master_password_mismatch(cli_instance):
    with patch.object(cli_instance, '_read_secret', side_effect=["pass1", "pass2"] * 3):
        with pytest.raises(RuntimeError, match="Не удалось установить мастер-пароль"):
            cli_instance.setup_master_password()


def test_authenticate_success(cli_instance):
    test_pass = "correct"
    test_hash = hashlib.sha256(test_pass.encode()).hexdigest()
    cli_instance.db.set_master_password(test_hash)
    with patch.object(cli_instance, '_read_secret', return_value=test_pass):
        assert cli_instance.authenticate() is True


def test_authenticate_failure(cli_instance):
    test_hash = hashlib.sha256(b"real_pass").hexdigest()
    cli_instance.db.set_master_password(test_hash)
    with patch.object(cli_instance, '_read_secret', return_value="wrong"):
        assert cli_instance.authenticate(max_attempts=3) is False


def test_add_password_manual(cli_instance, capsys):
    with patch('builtins.input', side_effect=["test_site", "user123", "n", "mypass123"]):
        cli_instance.add_password()
    result = cli_instance.db.get_password("test_site")
    assert result is not None
    login, encrypted = result
    assert login == "user123"
    decrypted = cli_instance.crypto.decrypt(encrypted)
    assert decrypted == "mypass123"
    captured = capsys.readouterr()
    assert "Запись 'test_site' успешно добавлена" in captured.out


def test_add_password_generated(cli_instance, capsys):
    with patch('password_manager.PasswordGenerator.interactive', return_value="GenPass123!"):
        with patch('builtins.input', side_effect=["generated_site", "gen_login", "y"]):
            cli_instance.add_password()
    result = cli_instance.db.get_password("generated_site")
    assert result is not None
    login, encrypted = result
    assert login == "gen_login"
    decrypted = cli_instance.crypto.decrypt(encrypted)
    assert decrypted == "GenPass123!"


def test_get_password_output(cli_instance, capsys):
    cli_instance.db.add_password("example", "ex_login", cli_instance.crypto.encrypt("ex_pass"))
    with patch('builtins.input', return_value="example"):
        cli_instance.get_password()
    captured = capsys.readouterr()
    assert "Название: example" in captured.out
    assert "Логин: ex_login" in captured.out
    assert "Пароль: ex_pass" in captured.out


def test_get_password_not_found(cli_instance, capsys):
    with patch('builtins.input', return_value="missing"):
        cli_instance.get_password()
    captured = capsys.readouterr()
    assert "Запись 'missing' не найдена" in captured.out


def test_list_passwords(cli_instance, capsys):
    cli_instance.db.add_password("site1", "login1", "enc1")
    cli_instance.db.add_password("site2", "login2", "enc2")
    cli_instance.list_passwords()
    captured = capsys.readouterr()
    assert "- site1 (логин: login1)" in captured.out
    assert "- site2 (логин: login2)" in captured.out


def test_delete_password(cli_instance, capsys):
    cli_instance.db.add_password("to_delete", "some_login", "enc")
    with patch('builtins.input', side_effect=["to_delete", "y"]):
        cli_instance.delete_password()
    assert cli_instance.db.get_password("to_delete") is None
    captured = capsys.readouterr()
    assert "Запись 'to_delete' удалена" in captured.out


def test_delete_password_cancel(cli_instance, capsys):
    cli_instance.db.add_password("keep", "login", "enc")
    with patch('builtins.input', side_effect=["keep", "n"]):
        cli_instance.delete_password()
    assert cli_instance.db.get_password("keep") is not None
    captured = capsys.readouterr()
    assert "Удаление отменено" in captured.out


def test_new_password_generation(cli_instance, capsys):
    with patch('password_manager.PasswordGenerator.interactive', return_value="FakeGenerated"):
        cli_instance.new_password()
    assert True


def test_show_menu(capsys):
    cli = PasswordCLI()
    cli.show_menu()
    captured = capsys.readouterr()
    assert "МЕНЕДЖЕР ПАРОЛЕЙ" in captured.out
    assert "1. Добавить запись" in captured.out
    assert "6. Выход" in captured.out


def test_run_flow_first_time_no_master(cli_instance):
    assert cli_instance.db.get_master_password_hash() is None
    with patch.object(cli_instance, 'setup_master_password') as mock_setup:
        with patch.object(cli_instance, 'authenticate', return_value=True):
            with patch('builtins.input', side_effect=["6"]):
                cli_instance.run()
    mock_setup.assert_called_once()


def test_run_flow_with_master(cli_instance):
    test_hash = hashlib.sha256(b"pass").hexdigest()
    cli_instance.db.set_master_password(test_hash)
    with patch.object(cli_instance, 'authenticate', return_value=True):
        with patch('builtins.input', side_effect=["6"]):
            cli_instance.run()


def test_run_authentication_failure(cli_instance):
    test_hash = hashlib.sha256(b"real").hexdigest()
    cli_instance.db.set_master_password(test_hash)
    with patch.object(cli_instance, 'authenticate', return_value=False):
        with patch('builtins.input') as mock_input:
            mock_input.return_value = ""
            cli_instance.run()
            mock_input.assert_called_once_with("Нажмите Enter для выхода...")


def test_menu_choice_invalid(cli_instance, capsys):
    test_hash = hashlib.sha256(b"pass").hexdigest()
    cli_instance.db.set_master_password(test_hash)
    with patch.object(cli_instance, 'authenticate', return_value=True):
        with patch('builtins.input', side_effect=["7", "", "6"]):
            cli_instance.run()
    captured = capsys.readouterr()
    assert "Неверный выбор. Попробуйте снова." in captured.out


def test_add_password_existing_name(cli_instance, capsys):
    cli_instance.db.add_password("duplicate", "login1", "enc1")
    with patch('builtins.input', side_effect=["duplicate", "login2", "n", "pass2"]):
        cli_instance.add_password()
    captured = capsys.readouterr()
    assert "Ошибка: запись с именем 'duplicate' уже существует" in captured.out


def test_get_password_decryption_error(cli_instance, capsys):
    cli_instance.db.add_password("corrupted", "login", "not_valid_encrypted")
    with patch('builtins.input', return_value="corrupted"):
        cli_instance.get_password()
    captured = capsys.readouterr()
    assert "Ошибка расшифровки" in captured.out


if __name__ == "__main__":
    pytest.main(["-v", __file__])