import time
from celery import shared_task
import logging

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

