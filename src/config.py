from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment variables for the db
    POSTGRES_USER: str = "cinema_admin"
    POSTGRES_PASSWORD: str = "cinema_secure_pass"
    POSTGRES_DB: str = "online_cinema_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    # URL for SQLAlchemy (generated auto if no manual)
    DATABASE_URL: Optional[str] = None

    # Settings JWT
    SECRET_KEY: str = "super_secret_jwt_key_for_online_cinema_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Settings Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Settings Stripe
    # (if keys is empties then application work via mocks)
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    BASE_URL: str = "http://localhost:8000"

    # Settings for Swagger documentation security
    DOCS_USERNAME: str = "admin"
    DOCS_PASSWORD: str = "supersecure_docs_password_2026"

    # Settings post server
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = "your_email@gmail.com"
    SMTP_PASSWORD: str = "your_app_password"

    # Load environment variables from a
    # .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        """
        Returns an asynchronous URL for connecting to PostgreSQL.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.POSTGRES_DB}"
        )


# Init to use settings in other modules
settings = Settings()
