from django.apps import AppConfig


class ClaudeUsageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.claude_usage"
    verbose_name = "Claude Usage Monitoring"
