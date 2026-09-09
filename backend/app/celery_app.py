"""Celery application instance.

Like what you know: this is the Python equivalent of setting up a BullMQ
Queue + Worker against a Redis connection. No tasks are registered yet —
those arrive with the matching engine (spec.md section 8, Phase 5) — this
just gives docker-compose's `worker` service something to run so the shape
of background-job infra is in place from day one.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("mwtv", broker=settings.redis_url, backend=settings.redis_url)
