import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response

User = get_user_model()

#* Function to send notifications to Gotify
def send_gotify_message(message, title="Django Notification", priority=5):
    """
    Send a notification to Gotify.
    :param message: The message content
    :param title: The notification title
    :param priority: Priority level (0-10)
    """
    url = f"{settings.GOTIFY_URL}/message"
    headers = {"X-Gotify-Key": settings.GOTIFY_TOKEN}
    data = {
        "title": title,
        "message": message,
        "priority": priority,
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print("Notification sent successfully")
    except requests.RequestException as e:
        print(f"Failed to send notification: {e}")

#* Signal to notify Gotify when a new user is created
@receiver(post_save, sender=User)
def notify_new_user(sender, instance, created, **kwargs):
    if created:
        send_gotify_message(
            message=f"New user registered: {instance.username}",
            title="New User",
            priority=5
        )
        print(f"Gotify notification sent for new user: {instance.username}")

#* Function to check Gotify messages and perform actions based on specific titles
def check_gotify_messages():
    url = f"{settings.GOTIFY_URL}/message"
    headers = {"X-Gotify-Key": settings.GOTIFY_TOKEN}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        messages = response.json().get("messages", [])
        for msg in messages:
            if msg.get("title") == "****":
                # Do your action here
                print("Special action for message:", msg)
    except requests.RequestException as e:
        print(f"Failed to fetch messages: {e}")