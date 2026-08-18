"""
app/workers/celery_app.py — Celery Application Configuration

PATTERN: Celery application factory with explicit queue definitions.

WHY explicit queues (not the default queue):
    Different task types have different priorities and worker requirements:

    - `pdf_generation`: CPU-bound (ReportLab rendering). Workers can have
      more memory allocated. Low concurrency (2-4 workers enough).
    - `excel_export`: Memory-bound (openpyxl loads entire sheets). Separate
      workers prevent Excel jobs from starving real-time tasks.
    - `stock_reservation`: Time-critical (60-second timeout tasks).
      High priority, low latency. Never mix with slow PDF tasks.
    - `default`: General tasks (emails, notifications, cache warming).

    Without separate queues, a slow PDF job blocks a time-critical reservation
    release task — causing inventory bugs.

SCALABILITY:
    To scale specific task types:
        docker compose up --scale celery_worker_pdf=2
    Different worker services can subscribe to different queues.

RELIABILITY:
    - task_acks_late=True: Celery acknowledges the task AFTER completion,
      not on receipt. If a worker crashes mid-task, the task is re-queued
      automatically. Without this, crashes cause silent task loss.
    - max_retries=3: Transient failures (DB timeout, network blip) are
      automatically retried with exponential backoff.
    - task_reject_on_worker_lost=True: Re-queues tasks if the worker dies.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from app.core.config import get_settings

settings = get_settings()

# Create Celery application
# WHY include=[] with explicit task modules: Celery auto-discovers tasks
# only from the `include` list. Explicit is safer than `autodiscover_tasks`.
celery_app = Celery(
    "erp_worker",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=[
        "app.workers.pdf_tasks",
        "app.workers.excel_tasks",
        "app.workers.reservation_tasks",
        "app.workers.notification_tasks",
    ],
)

# ── Queue Configuration ────────────────────────────────────────────────────────
# WHY direct exchange: Messages are routed directly to named queues.
# Topic exchange (with routing keys) would be needed for pub/sub patterns.
default_exchange = Exchange("default", type="direct")
pdf_exchange = Exchange("pdf", type="direct")
excel_exchange = Exchange("excel", type="direct")
reservation_exchange = Exchange("reservation", type="direct")

celery_app.conf.task_queues = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("pdf_generation", pdf_exchange, routing_key="pdf"),
    Queue("excel_export", excel_exchange, routing_key="excel"),
    Queue(
        "stock_reservation",
        reservation_exchange,
        routing_key="reservation",
        # Higher priority queue — reservation tasks must run before default
        queue_arguments={"x-max-priority": 10},
    ),
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "default"

# ── Task Routing ──────────────────────────────────────────────────────────────
celery_app.conf.task_routes = {
    "app.workers.pdf_tasks.*": {"queue": "pdf_generation"},
    "app.workers.excel_tasks.*": {"queue": "excel_export"},
    "app.workers.reservation_tasks.*": {"queue": "stock_reservation"},
    "app.workers.notification_tasks.*": {"queue": "default"},
}

# ── Serialization ─────────────────────────────────────────────────────────────
celery_app.conf.update(
    task_serializer=settings.celery.task_serializer,
    result_serializer=settings.celery.result_serializer,
    accept_content=settings.celery.accept_content,
    timezone=settings.celery.timezone,
    enable_utc=settings.celery.enable_utc,

    # ── Reliability settings ──────────────────────────────────────────────
    task_acks_late=True,            # Acknowledge AFTER completion (see docstring)
    task_reject_on_worker_lost=True,  # Re-queue on worker death
    worker_prefetch_multiplier=settings.celery.worker_prefetch_multiplier,

    # ── Time limits ───────────────────────────────────────────────────────
    task_soft_time_limit=settings.celery.task_soft_time_limit,   # 5 min: raise SoftTimeLimitExceeded
    task_time_limit=settings.celery.task_time_limit,             # 10 min: hard kill

    # ── Result expiry ─────────────────────────────────────────────────────
    # Task results stored for 24 hours. After that, auto-deleted from Redis.
    result_expires=86400,

    # ── Retry policy ──────────────────────────────────────────────────────
    task_default_retry_delay=60,   # 60s base delay
    task_max_retries=3,
)

# ── Beat Schedule (Periodic Tasks) ────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Daily inventory snapshot at 11:55 PM IST
    "daily-inventory-snapshot": {
        "task": "app.workers.excel_tasks.generate_daily_inventory_snapshot",
        "schedule": crontab(hour=18, minute=25),  # UTC 18:25 = IST 23:55
    },
    # Low stock alert check every hour
    "low-stock-alert-check": {
        "task": "app.workers.notification_tasks.check_low_stock_alerts",
        "schedule": crontab(minute=0),  # Every hour at :00
    },
    # Clean up expired reservations every 2 minutes
    # (belt-and-suspenders: Celery eta handles individual timeouts)
    "cleanup-expired-reservations": {
        "task": "app.workers.reservation_tasks.cleanup_expired_reservations",
        "schedule": crontab(minute="*/2"),
    },
}
