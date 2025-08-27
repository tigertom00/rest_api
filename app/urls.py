from django.urls import path, include

urlpatterns = [
    path('', include('app.todo.urls')),
    path('', include('app.tasks.urls')),
]