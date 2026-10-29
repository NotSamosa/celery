from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_celery_beat.models import PeriodicTask
from .tasks import test_connection_task, long_running_task
from .serializers import PeriodicTaskListSerializer, DynamicScheduleCreateSerializer


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


class ListPeriodicTasksView(APIView):
    """
    API endpoint to list all scheduled periodic tasks in Celery Beat database.
    """
    def get(self, request, *args, **kwargs):
        tasks = PeriodicTask.objects.all().order_by('-date_changed')
        serializer = PeriodicTaskListSerializer(tasks, many=True)
        return Response({"count": tasks.count(), "results": serializer.data})


class CreateDynamicScheduleView(APIView):
    """
    API endpoint to dynamically create a new periodic task (Interval or Crontab).
    """
    def post(self, request, *args, **kwargs):
        serializer = DynamicScheduleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        periodic_task = serializer.save()
        return Response(
            {
                "status": "success",
                "message": f"Periodic task '{periodic_task.name}' created successfully.",
                "task_id": periodic_task.id,
                "task": periodic_task.task,
                "enabled": periodic_task.enabled,
            },
            status=status.HTTP_201_CREATED,
        )


class TogglePeriodicTaskView(APIView):
    """
    API endpoint to enable or disable an existing periodic task.
    """
    def post(self, request, task_id, *args, **kwargs):
        try:
            periodic_task = PeriodicTask.objects.get(id=task_id)
        except PeriodicTask.DoesNotExist:
            return Response(
                {"error": f"Periodic task with id {task_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        periodic_task.enabled = not periodic_task.enabled
        periodic_task.save()

        return Response({
            "status": "success",
            "task_id": periodic_task.id,
            "name": periodic_task.name,
            "enabled": periodic_task.enabled,
            "message": f"Periodic task is now {'enabled' if periodic_task.enabled else 'disabled'}.",
        })


class DeletePeriodicTaskView(APIView):
    """
    API endpoint to delete an existing dynamic periodic task.
    """
    def delete(self, request, task_id, *args, **kwargs):
        try:
            periodic_task = PeriodicTask.objects.get(id=task_id)
            name = periodic_task.name
            periodic_task.delete()
            return Response({
                "status": "success",
                "message": f"Periodic task '{name}' deleted successfully.",
            }, status=status.HTTP_200_OK)
        except PeriodicTask.DoesNotExist:
            return Response(
                {"error": f"Periodic task with id {task_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
