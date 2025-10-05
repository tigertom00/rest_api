from django.contrib import admin
from .models import Project, Session, UsageSnapshot


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "total_sessions",
        "total_tokens",
        "total_cost",
        "created_at",
        "updated_at",
    ]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]

    def total_sessions(self, obj):
        return obj.sessions.count()

    total_sessions.short_description = "Sessions"


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        "session_id",
        "project",
        "message_count",
        "total_tokens",
        "total_cost",
        "created_at",
    ]
    list_filter = ["project", "created_at"]
    search_fields = ["session_id", "project__name"]
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("project")


@admin.register(UsageSnapshot)
class UsageSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "session",
        "model",
        "total_tokens",
        "cost_usd",
        "timestamp",
    ]
    list_filter = ["project", "model", "timestamp"]
    search_fields = ["project__name", "session__session_id", "model"]
    readonly_fields = ["timestamp"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("project", "session")
