from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult
from django_celery_results.models import TaskResult

from .serializers import SendEmailSerializer, BulkEmailSerializer, WelcomeEmailSerializer
from .tasks import send_email_task, send_bulk_email_task, send_welcome_email_task


class SendEmailView(APIView):
    """
    API endpoint to dispatch a background email sending task via Celery.
    """
    def post(self, request, *args, **kwargs):
        serializer = SendEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        task = send_email_task.delay(
            subject=data["subject"],
            message=data["message"],
            recipient_list=data["recipient_list"],
            html_message=data.get("html_message"),
        )

        return Response(
            {
                "status": "queued",
                "message": "Email task has been queued for background processing.",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class SendBulkEmailView(APIView):
    """
    API endpoint to dispatch bulk emails asynchronously.
    """
    def post(self, request, *args, **kwargs):
        serializer = BulkEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        task = send_bulk_email_task.delay(
            subject=data["subject"],
            message=data["message"],
            recipient_list=data["recipient_list"],
        )

        return Response(
            {
                "status": "queued",
                "message": "Bulk email task has been queued for background processing.",
                "task_id": task.id,
                "recipient_count": len(data["recipient_list"]),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class SendWelcomeEmailView(APIView):
    """
    API endpoint to trigger an onboarding welcome email asynchronously.
    """
    def post(self, request, *args, **kwargs):
        serializer = WelcomeEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        task = send_welcome_email_task.delay(
            user_email=data["email"],
            username=data["username"],
        )

        return Response(
            {
                "status": "queued",
                "message": f"Welcome email task queued for user {data['username']}.",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class TaskStatusView(APIView):
    """
    API endpoint to check Celery task status and results by task_id.
    """
    def get(self, request, task_id, *args, **kwargs):
        async_result = AsyncResult(task_id)

        # Check in django-celery-results database table first
        db_result = TaskResult.objects.filter(task_id=task_id).first()

        response_data = {
            "task_id": task_id,
            "status": async_result.status,
            "ready": async_result.ready(),
            "successful": async_result.successful(),
        }

        if db_result:
            response_data["status"] = db_result.status
            response_data["result"] = db_result.result
            response_data["date_done"] = db_result.date_done
            response_data["task_name"] = db_result.task_name
        elif async_result.ready():
            try:
                response_data["result"] = async_result.result
            except Exception as e:
                response_data["result"] = str(e)
        else:
            response_data["result"] = None

        return Response(response_data, status=status.HTTP_200_OK)
