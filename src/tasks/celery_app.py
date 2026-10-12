from celery import Celery

from core.settings import settings

celery_app = Celery(
    'worker',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['tasks.reminders'],
)

celery_app.conf.timezone = 'UTC'
celery_app.autodiscover_tasks(['tasks'])
