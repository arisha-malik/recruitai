import os
from celery import Celery
from app.config import settings

# Determine Broker and Result Backend URLs dynamically
# Allows Redis or falls back to database queue if Redis is not configured
broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND

# If not explicitly configured, derive from REDIS_URL or DATABASE_URL
if not broker_url:
    # If REDIS_URL is default but empty, or if we fallback
    if settings.REDIS_URL and not settings.REDIS_URL.startswith("redis://localhost:6379"):
        broker_url = settings.REDIS_URL
    else:
        # PostgreSQL fallback for broker
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            broker_url = f"sqla+{db_url}"
        elif db_url.startswith("sqlite://"):
            broker_url = f"sqla+{db_url}"
        elif db_url.startswith("mysql+pymysql://"):
            broker_url = f"sqla+{db_url}"
        else:
            # Default to redis
            broker_url = settings.REDIS_URL

if not result_backend:
    if settings.REDIS_URL and not settings.REDIS_URL.startswith("redis://localhost:6379"):
        result_backend = settings.REDIS_URL
    else:
        # PostgreSQL fallback for backend
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            result_backend = f"db+{db_url}"
        elif db_url.startswith("sqlite://"):
            result_backend = f"db+sqlite:///{db_url.split('sqlite:///')[-1]}"
        elif db_url.startswith("mysql+pymysql://"):
            result_backend = f"db+{db_url}"
        else:
            result_backend = settings.REDIS_URL

# Create Celery instance
celery_app = Celery(
    "recruitai_worker",
    broker=broker_url,
    backend=result_backend
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Auto-load tasks file
    imports=["app.worker.tasks"]
)
