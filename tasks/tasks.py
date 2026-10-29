import time
import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django_celery_results.models import TaskResult

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def test_connection_task(self):
    """
    Simple connectivity test task to verify Celery worker and Redis broker communication.
    """
    logger.info("Executing test_connection_task...")
    return {
        "status": "success",
        "message": "Celery connection successful!",
        "task_id": self.request.id,
    }


@shared_task(bind=True)
def long_running_task(self, duration=5):
    """
    Long running task with sleep to test asynchronous execution and background processing.
    """
    logger.info(f"Starting long_running_task with duration: {duration} seconds...")
    time.sleep(duration)
    logger.info(f"Finished long_running_task (duration: {duration}s)")
    return {
        "status": "completed",
        "duration": duration,
        "message": f"Task completed successfully after {duration} seconds.",
        "task_id": self.request.id,
    }


@shared_task(bind=True)
def system_heartbeat_task(self):
    """
    Periodic heartbeat task checking system health and current timezone timestamp.
    """
    now = timezone.now()
    now_local = timezone.localtime(now)
    logger.info(
        f"[Heartbeat] System alive at {now_local.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC: {now})"
    )
    return {
        "status": "healthy",
        "utc_time": now.isoformat(),
        "local_time": now_local.isoformat(),
        "timezone": str(timezone.get_current_timezone()),
        "task_id": self.request.id,
    }


@shared_task(bind=True)
def cleanup_old_task_results_task(self, days=7):
    """
    Periodic task to clean up old TaskResult records older than specified days.
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = TaskResult.objects.filter(date_done__lt=cutoff_date).delete()
    logger.info(
        f"[Cleanup] Deleted {deleted_count} TaskResult entries older than {days} days (cutoff: {cutoff_date})"
    )
    return {
        "status": "completed",
        "deleted_count": deleted_count,
        "days_threshold": days,
        "cutoff_date": cutoff_date.isoformat(),
        "task_id": self.request.id,
    }
