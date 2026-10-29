from django.urls import path
from .views import (
    SendEmailView,
    SendBulkEmailView,
    SendWelcomeEmailView,
    TaskStatusView,
)

urlpatterns = [
    path('send-email/', SendEmailView.as_view(), name='send-email'),
    path('send-bulk-email/', SendBulkEmailView.as_view(), name='send-bulk-email'),
    path('send-welcome-email/', SendWelcomeEmailView.as_view(), name='send-welcome-email'),
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
]

