from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from tasks.tasks import (
    test_connection_task,
    long_running_task,
    system_heartbeat_task,
    cleanup_old_task_results_task,
)


class PeriodicTaskAndBeatTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_system_heartbeat_task(self):
        result = system_heartbeat_task.apply().get()
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["timezone"], "Asia/Kolkata")
        self.assertIn("local_time", result)

    def test_cleanup_old_task_results_task(self):
        result = cleanup_old_task_results_task.apply(kwargs={"days": 1}).get()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["days_threshold"], 1)

    def test_create_dynamic_interval_task(self):
        url = reverse('create-schedule')
        payload = {
            "name": "dynamic-heartbeat-test",
            "task": "tasks.tasks.system_heartbeat_task",
            "schedule_type": "interval",
            "interval_every": 30,
            "interval_period": "seconds",
            "enabled": True,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.assertTrue(PeriodicTask.objects.filter(name="dynamic-heartbeat-test").exists())

    def test_create_dynamic_crontab_task(self):
        url = reverse('create-schedule')
        payload = {
            "name": "daily-kolkata-report-test",
            "task": "email_sender.tasks.send_scheduled_report_task",
            "schedule_type": "crontab",
            "crontab_minute": "30",
            "crontab_hour": "10",
            "crontab_day_of_week": "*",
            "crontab_timezone": "Asia/Kolkata",
            "enabled": True,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = PeriodicTask.objects.get(name="daily-kolkata-report-test")
        self.assertIsNotNone(task.crontab)
        self.assertEqual(task.crontab.minute, "30")
        self.assertEqual(task.crontab.hour, "10")
        self.assertEqual(str(task.crontab.timezone), "Asia/Kolkata")

    def test_list_and_toggle_periodic_task(self):
        interval, _ = IntervalSchedule.objects.get_or_create(every=10, period="seconds")
        task = PeriodicTask.objects.create(
            name="toggle-test-task",
            task="tasks.tasks.system_heartbeat_task",
            interval=interval,
            enabled=True,
        )

        # 1. List
        list_url = reverse('list-schedules')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

        # 2. Toggle to False
        toggle_url = reverse('toggle-schedule', kwargs={'task_id': task.id})
        toggle_resp = self.client.post(toggle_url)
        self.assertEqual(toggle_resp.status_code, status.HTTP_200_OK)
        self.assertFalse(toggle_resp.data["enabled"])

        # 3. Toggle back to True
        toggle_resp2 = self.client.post(toggle_url)
        self.assertEqual(toggle_resp2.status_code, status.HTTP_200_OK)
        self.assertTrue(toggle_resp2.data["enabled"])

    def test_delete_periodic_task(self):
        interval, _ = IntervalSchedule.objects.get_or_create(every=10, period="seconds")
        task = PeriodicTask.objects.create(
            name="delete-me-task",
            task="tasks.tasks.system_heartbeat_task",
            interval=interval,
        )
        delete_url = reverse('delete-schedule', kwargs={'task_id': task.id})
        resp = self.client.delete(delete_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(PeriodicTask.objects.filter(id=task.id).exists())
