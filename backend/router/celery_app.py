import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

_broker  = os.getenv("CELERY_BROKER_URL",  os.getenv("REDIS_URL", "redis://localhost:6379/0"))
_backend = os.getenv("CELERY_RESULT_BACKEND", _broker)

celery_app = Celery(
    "router",
    broker=_broker,
    backend=_backend,
    include=["backend.router.execution"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
