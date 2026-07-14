# Ипользуем официальный образ Python
FROM python:3.11-slim

# Установка системных зависимостей для сборки некоторых Python-пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка переменной окружения для Poetry
ENV POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="$POETRY_HOME/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Установка Poetry через официальный скрипт
RUN curl -sSL https://install.python-poetry.org | python3 -

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем файлы конфигурации зависимостей
COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости без разработки (без dev-зависимостей)
RUN poetry install --no-interaction --no-ansi --no-root

# Копируем исходный код приложения
COPY . .

# Открываем порт для FastAPI
EXPOSE 8000

# Команда по умолчанию (будет переопределяться в docker-compose под каждый сервис)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]