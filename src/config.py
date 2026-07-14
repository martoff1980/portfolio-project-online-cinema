import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Переменные окружения для базы данных
    POSTGRES_USER: str = "cinema_admin"
    POSTGRES_PASSWORD: str = "cinema_secure_pass"
    POSTGRES_DB: str = "online_cinema_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    
    # URL для SQLAlchemy (формируется автоматически, если не задан вручную)
    DATABASE_URL: Optional[str] = None

    # Настройки JWT
    SECRET_KEY: str = "super_secret_jwt_key_for_online_cinema_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Настройки Redis и Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Настройки Stripe (если ключи отсутствуют, приложение работает через заглушку)
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    BASE_URL: str = "http://localhost:8000"

    # Настройки безопасности Swagger документации
    DOCS_USERNAME: str = "admin"
    DOCS_PASSWORD: str = "supersecure_docs_password_2026"

    # Настройки почтового сервера (для активации аккаунтов через Celery)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = "your_email@gmail.com"
    SMTP_PASSWORD: str = "your_app_password"

    # Загрузка настроек из .env файла
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        """Возвращает асинхронный URL для подключения к PostgreSQL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"


# Инициализируем глобальный объект настроек
settings = Settings()