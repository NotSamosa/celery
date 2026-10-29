from django.urls import path
from .views import TriggerTaskView

urlpatterns = [
    path('run/', TriggerTaskView.as_view(), name='trigger-task'),
]

