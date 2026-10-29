from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .tasks import test_connection_task, long_running_task


class TriggerTaskView(APIView):
    """
    API endpoint to trigger test tasks (connection test or long running task).
    """
    def post(self, request, *args, **kwargs):
        task_type = request.data.get("task_type", "connection")
        duration = int(request.data.get("duration", 5))

        if task_type == "connection":
            task = test_connection_task.delay()
        elif task_type == "long_running":
            task = long_running_task.delay(duration=duration)
        else:
            return Response(
                {"error": "Invalid task_type. Choose 'connection' or 'long_running'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "status": "queued",
                "task_type": task_type,
                "task_id": task.id,
                "message": f"Task '{task_type}' queued successfully.",
            },
            status=status.HTTP_202_ACCEPTED,
        )
