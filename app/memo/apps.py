from django.apps import AppConfig


class MemoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.memo"

    def ready(self):
        import app.memo.signals  # noqa: F401
