from django.urls import path, include

urlpatterns = [
    # path('todo/', include('app.todo.urls')),
    path("tasks/", include("app.tasks.urls")),
    path("components/", include("app.components.urls")),
    path("memo/", include("app.memo.urls")),
    path("blog/", include("app.blog.urls")),
    path("chat/", include("app.chat.urls")),
]
