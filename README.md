# Django Celery Integration Project

A complete, production-ready Django application demonstrating asynchronous task processing with Celery, Redis as the message broker, Django-Celery-Results for result monitoring, and Celery Beat for periodic and dynamic crontab task scheduling.

---

## 🎯 Architecture & Technologies
- **Framework**: Django 6.x / Django REST Framework
- **Task Queue**: Celery 5.x
- **Message Broker**: Redis (running on port `6379`)
- **Result Backend**: `django-celery-results` (`django-db`)
- **Periodic Scheduler**: `django-celery-beat` (`DatabaseScheduler`)
- **Timezone**: `Asia/Kolkata` (Indian Standard Time, UTC+05:30)

---

## 📁 Project Structure

```text
celery_email_project/
├── celery_email_project/
│   ├── __init__.py          # Celery app export (celery_app)
│   ├── celery.py            # Celery app configuration & static beat schedules
│   ├── settings.py          # Celery, Redis, Timezone, SMTP/Console config
│   ├── urls.py              # Root routing (/admin/, /api/, /api/tasks/)
│   ├── wsgi.py
│   └── asgi.py
├── tasks/
│   ├── tasks.py             # test_connection_task, long_running_task, system_heartbeat_task, cleanup_old_task_results_task
│   ├── views.py             # Task triggers & dynamic schedule CRUD APIs
│   ├── serializers.py       # Serializers for periodic tasks and schedules
│   ├── urls.py              # Schedule endpoints (/api/tasks/schedules/...)
│   └── tests.py             # 6 Unit & integration tests for tasks & beat
├── email_sender/
│   ├── tasks.py             # send_email_task, send_bulk_email_task, send_welcome_email_task, send_scheduled_report_task
│   ├── views.py             # Email dispatch views and task-status API
│   ├── serializers.py       # Validation serializers for email payloads
│   ├── urls.py              # Email endpoints (/api/send-email/, /api/task-status/...)
│   └── tests.py             # 6 Unit & integration tests for email tasks & APIs
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Environment & Dependencies
```bash
# Navigate to project
cd celery_email_project

# Activate virtual environment
source venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

### 2. Verify Redis
Ensure Redis server is running on port 6379:
```bash
redis-cli ping
# Expected output: PONG
```

### 3. Database Migrations
```bash
python manage.py migrate
```

### 4. Run Celery Worker
In a dedicated terminal:
```bash
celery -A celery_email_project worker -l info --pool=solo
```

### 5. Run Celery Beat (Periodic Scheduler)
In a second terminal:
```bash
celery -A celery_email_project beat -l info
```

### 6. Run Django Server
In a third terminal:
```bash
python manage.py runserver
```

---

## 🕒 Celery Beat Periodic & Crontab Scheduling

### Static Schedules ([`celery_email_project/celery.py`](file:///Users/monuchaudhary/Desktop/Tasks/celery_email_project/celery_email_project/celery.py))
- **Heartbeat Task**: Every 60 seconds (`tasks.tasks.system_heartbeat_task`)
- **Daily Summary Email**: Daily at 9:00 AM IST (`crontab(hour=9, minute=0)`)
- **Weekly DB Cleanup**: Every Sunday at midnight IST (`crontab(hour=0, minute=0, day_of_week='sunday')`)

### Dynamic Database Scheduling ([`django-celery-beat`](file:///Users/monuchaudhary/Desktop/Tasks/celery_email_project/tasks/serializers.py))
Schedules can be modified dynamically at runtime without restarting Celery or Django:
- In the **Django Admin**: `http://127.0.0.1:8000/admin/django_celery_beat/periodictask/`
- Via the **REST API**: `/api/tasks/schedules/create/`

---

## 📡 API Endpoints Reference

### Email Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/send-email/` | Queue a background email with automatic retries |
| `POST` | `/api/send-bulk-email/` | Queue bulk emails to a list of recipients |
| `POST` | `/api/send-welcome-email/` | Send formatted onboarding welcome email |
| `GET` | `/api/task-status/<task_id>/` | Check live status and results of any Celery task |

### Dynamic Schedule Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/tasks/schedules/` | List all dynamic periodic tasks and last run times |
| `POST` | `/api/tasks/schedules/create/` | Create a dynamic interval or crontab schedule |
| `POST` | `/api/tasks/schedules/<id>/toggle/` | Enable or disable a periodic task |
| `DELETE` | `/api/tasks/schedules/<id>/delete/` | Delete a periodic task |
| `POST` | `/api/tasks/run/` | Trigger test tasks (`connection` or `long_running`) |

---

## 🧪 Testing

Run the automated test suite (12 tests covering tasks, retries, beat scheduling, and APIs):
```bash
python manage.py test
```

---

## 🛡️ Monitoring via Django Admin
Login to the admin dashboard at `http://127.0.0.1:8000/admin/`:
- **Username**: `admin`
- **Password**: `admin123`
- **Task Results**: View finished and active tasks in **Django Celery Results -> Task results**.
- **Periodic Tasks**: View, pause, resume, or edit schedules in **Periodic Tasks**.

