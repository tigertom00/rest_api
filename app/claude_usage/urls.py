from django.urls import path
from . import views

app_name = "claude_usage"

urlpatterns = [
    path("stats/", views.usage_stats, name="usage-stats"),
    path("projects/", views.project_list, name="project-list"),
    path("projects/<str:project_name>/", views.project_detail, name="project-detail"),
    path(
        "projects/<str:project_name>/sessions/",
        views.project_sessions,
        name="project-sessions",
    ),
    path("sessions/<str:session_id>/", views.session_detail, name="session-detail"),
    path("refresh/", views.refresh_data, name="refresh-data"),
    path("agent-sync/", views.agent_sync_claude_usage, name="agent-sync"),
]
