from django.apps import AppConfig
  # Ensure this import is correct based on your project structure

class RestapiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'restAPI'

    def ready(self):

        from .views import ClerkAuthenticationScheme
        import restAPI.utils.gotify
        # import restAPI.utils.signals #* For sending django created users to Clerk

