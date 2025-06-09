from django.core.management.base import BaseCommand
from django.conf import settings
import requests

#* python manage.py check_gotify
#* This command checks Gotify messages and performs an action if the title matches a specific string.
class Command(BaseCommand):
    help = "Poll Gotify for messages and perform an action if title matches"

    def handle(self, *args, **options):
        url = f"{settings.GOTIFY_URL}/message"
        headers = {"X-Gotify-Key": settings.GOTIFY_ACCESS_TOKEN}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            messages = response.json().get("messages", [])
            for msg in messages:
                title = msg.get("title", "")
                if title == "hey":  # Replace **** with your target title
                    self.stdout.write(self.style.SUCCESS(
                        f"Action triggered for message: {msg}"
                    ))
                    # Place your custom action here
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Failed to fetch messages: {e}"))