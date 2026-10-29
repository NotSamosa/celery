from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('email_sender.urls')),
    path('api/tasks/', include('tasks.urls')),
]
