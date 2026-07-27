import pytest
from pydantic import ValidationError

from src.schemas.auth import UserCreate, UserLogin


class TestAuthValidation:
    """
    Validation of incoming data for authentication and profiles.
    """

    def test_user_create_schema_valid(self):
        """
        Verification of the successful validation of valid user data.
        """
        data = {
            "email": "valid.user@cinema.com",
            "password": "StrongPassword123!",
            "first_name": "John",
            "last_name": "Doe"
        }
        schema = UserCreate(**data)
        assert schema.email == "valid.user@cinema.com"
        assert schema.password == "StrongPassword123!"

    @pytest.mark.parametrize("invalid_email", [
        "not-an-email",
        "user@",
        "@cinema.com",
        "user@cinema",
        "user..name@cinema.com"
    ])
    def test_user_create_schema_invalid_email(self, invalid_email):
        """
        Verification of invalid email address rejection.
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email=invalid_email,
                password="StrongPassword123!"
            )
        assert "email" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_password", [
        "short",
        "nopassword123!",
        "NOLOWERCASE123!",
        "NoDigitsHere!",
    ])
    def test_user_create_schema_invalid_password(self, invalid_password):
        """
        Password complexity policy check.
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@cinema.com",
                password=invalid_password
            )
        assert "password" in str(exc_info.value)


class TestUserLoginValidation:
    """
    Validation of incoming system login data (UserLogin).
    """

    def test_user_login_schema_valid(self):
        """
        Verification of successful validation of a valid email and password.
        """
        data = {
            "email": "user@cinema.com",
            "password": "MySecretPassword123!"
        }
        schema = UserLogin(**data)
        assert schema.email == "user@cinema.com"
        assert schema.password == "MySecretPassword123!"

    @pytest.mark.parametrize("invalid_email", [
        "not-an-email",
        "plainaddress",
        "@missingusername.com",
        "user@.com",
    ])
    def test_user_login_schema_invalid_email(self, invalid_email):
        """
        Checking the validation error when submitting an invalid email format.
        """
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(
                email=invalid_email,
                password="ValidPassword123!"
            )
        assert "email" in str(exc_info.value)

    def test_user_login_schema_empty_password(self):
        """
        Verification of empty password rejection during login.
        """
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(
                email="user@cinema.com",
                password=""
            )
        assert "password" in str(exc_info.value)
