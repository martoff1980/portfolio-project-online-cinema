import pytest
from fastapi import HTTPException
from src.security import (
    hash_password,
    verify_password,
    validate_password_complexity
)

def test_password_hashing():
    password = "SecretPassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_password_complexity_valid():
    # Валидный пароль не должен выбрасывать исключений
    assert validate_password_complexity("ValidPass123") is None

@pytest.mark.parametrize("invalid_password", [
    "short1",         # Слишком короткий
    "notuppercase1",  # Нет заглавной буквы
    "NOTLOWERCASE1",  # Нет строчной буквы
    "NoDigitsPass",   # Нет цифр
])
def test_password_complexity_invalid(invalid_password):
    with pytest.raises(HTTPException) as exc_info:
        validate_password_complexity(invalid_password)
    assert exc_info.value.status_code == 400