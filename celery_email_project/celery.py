import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module for 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celery_email_project.settings')

app = Celery('celery_email_project')

# Configure Celery using settings from Django settings.py with namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Broker, Result Backend, and Timezone configurations
app.conf.update(
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='django-db',
    timezone='Asia/Kolkata',
    enable_utc=True,
)

# Celery Beat Periodic Task Schedules
app.conf.beat_schedule = {
    'heartbeat-every-60-seconds': {
        'task': 'tasks.tasks.system_heartbeat_task',
        'schedule': 60.0,
    },
    'daily-summary-report-9am': {
        'task': 'email_sender.tasks.send_scheduled_report_task',
        'schedule': crontab(hour=9, minute=0),
    },
    'weekly-task-results-cleanup': {
        'task': 'tasks.tasks.cleanup_old_task_results_task',
        'schedule': crontab(hour=0, minute=0, day_of_week='sunday'),
        'kwargs': {'days': 7},
    },
}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
