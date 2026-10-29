import os
from celery import Celery

# Set default Django settings module for 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celery_email_project.settings')

app = Celery('celery_email_project')

# Configure Celery using settings from Django settings.py with namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Broker and Result Backend configurations
app.conf.update(
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='django-db',
    timezone='Asia/Kolkata',
    enable_utc=True,
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

