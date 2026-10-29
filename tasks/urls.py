from django.urls import path
from .views import (
    TriggerTaskView,
    ListPeriodicTasksView,
    CreateDynamicScheduleView,
    TogglePeriodicTaskView,
    DeletePeriodicTaskView,
)

urlpatterns = [
    path('run/', TriggerTaskView.as_view(), name='trigger-task'),
    path('schedules/', ListPeriodicTasksView.as_view(), name='list-schedules'),
    path('schedules/create/', CreateDynamicScheduleView.as_view(), name='create-schedule'),
    path('schedules/<int:task_id>/toggle/', TogglePeriodicTaskView.as_view(), name='toggle-schedule'),
    path('schedules/<int:task_id>/delete/', DeletePeriodicTaskView.as_view(), name='delete-schedule'),
]
