# Use the official Python image as a base image
FROM python:3.11-slim

# Install system dependencies for building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry and configure it to not create virtual environments
ENV POETRY_VERSION=2.4.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1


# Add Poetry's bin directory to the system PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry using the official installation script
RUN curl -sSL https://install.python-poetry.org | python3 -

# Working directory inside the container
WORKDIR /app

# Copy only the dependency files to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Install dependencies without dev-dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the entire application code into the container
COPY . .

# Set the PYTHONPATH environment variable to include the application directory
ENV PYTHONPATH=/app

# Set the port that the application will run on
EXPOSE 8000

# Srart the FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]