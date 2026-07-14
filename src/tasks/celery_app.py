import os
import asyncio
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import delete
# Async generator for database sessions
from src.database import AsyncSessionLocal as async_session_maker 
from src.models.auth import ActivationToken
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.beat_schedule = {
    "delete-expired-activation-tokens-every-hour": {
        "task": "tasks.delete_expired_activation_tokens",
        "schedule": crontab(minute=0, hour="*/1"),  # Каждый час
    },
}

# Обертка для асинхронного запуска задач в Celery
def async_to_sync(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

@celery_app.task
def delete_expired_activation_tokens():
    async def _delete():
        async with async_session_maker() as session:
            query = delete(ActivationToken).where(ActivationToken.expires_at < datetime.utcnow())
            await session.execute(query)
            await session.commit()
    
    async_to_sync(_delete())