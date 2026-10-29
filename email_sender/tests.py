from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIClient
from email_sender.tasks import send_email_task, send_bulk_email_task


class EmailTaskTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_send_email_task_execution(self):
        result = send_email_task.apply(
            args=["Test Subject", "Test Body Message", ["user@example.com"]]
        ).get()

        self.assertEqual(result["status"], "success")
        self.assertIn("user@example.com", result["recipients"])
        self.assertEqual(result["sent_count"], 1)

    def test_send_email_task_invalid_recipient(self):
        result = send_email_task.apply(
            args=["Invalid Email", "Message", ["invalid-email-format"]]
        ).get()

        self.assertEqual(result["status"], "failed")
        self.assertIn("No valid recipients", result["error"])

    def test_send_bulk_email_task_execution(self):
        recipients = ["user1@example.com", "user2@example.com"]
        result = send_bulk_email_task.apply(
            args=["Bulk Subject", "Bulk Message", recipients]
        ).get()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_recipients"], 2)

    def test_send_email_api_endpoint(self):
        url = reverse('send-email')
        payload = {
            "subject": "API Test",
            "message": "Hello from API!",
            "recipient_list": ["test@example.com"],
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["status"], "queued")
        self.assertIn("task_id", response.data)

    def test_send_email_api_validation_error(self):
        url = reverse('send-email')
        payload = {
            "subject": "Missing recipients and message"
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_task_status_endpoint(self):
        # Dispatch a task and check status
        task = send_email_task.delay(
            "Status Check", "Body", ["check@example.com"]
        )
        url = reverse('task-status', kwargs={'task_id': task.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["task_id"], task.id)
        self.assertIn("status", response.data)
