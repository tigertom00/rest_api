from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timezone
import requests
import os

User = get_user_model()
#! NOT IN USE
#* Signal to create a Clerk user when a Django user is created
@receiver(post_save, sender=User)
def create_clerk_user(sender, instance, created, **kwargs):
    if created:
        email = instance.email
        username = instance.username
        url = "https://api.clerk.com/v1/users"
        headers = {
            "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email_address": [email],
            "password": os.urandom(16).hex(),
        }
        if username:
            data["username"] = username
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print("Clerk response:", response.status_code, response.text)
            response.raise_for_status()
            clerk_data = response.json()
            # Update fields on the user instance
            instance.clerk_id = clerk_data.get("id")
            instance.clerk_profile_image_url = clerk_data.get("profile_image_url")
            instance.username = clerk_data.get("username", email.split('@')[0])
            instance.first_name = clerk_data.get("first_name", "")
            instance.last_name = clerk_data.get("last_name", "")
            instance.two_factor_enabled = clerk_data.get("two_factor_enabled", False)
            # Convert Clerk's updated_at (ms timestamp) to datetime
            updated_at = clerk_data.get("updated_at")
            if updated_at:
                instance.clerk_updated_at = datetime.fromtimestamp(updated_at / 1000, tz=timezone.utc)
            instance.save(update_fields=[
                'clerk_id', 'clerk_profile_image_url', 'username', 'first_name',
                'last_name', 'two_factor_enabled', 'clerk_updated_at'
            ])
            # Add primary email and phone if present
            email_addresses = clerk_data.get("email_addresses", [])
            if email_addresses:
                from ..models import UserEmail
                UserEmail.objects.get_or_create(
                    user=instance,
                    email=email_addresses[0].get("email_address"),
                    defaults={"is_primary": True, "is_verified": email_addresses[0].get("verification", {}).get("status") == "verified"}
                )
            phone_numbers = clerk_data.get("phone_numbers", [])
            if phone_numbers:
                from ..models import UserPhone
                UserPhone.objects.get_or_create(
                    user=instance,
                    phone_nr=phone_numbers[0].get("phone_number"),
                    defaults={"is_primary": True, "is_verified": phone_numbers[0].get("verification", {}).get("status") == "verified"}
                )
        except Exception as e:
            print(f"Failed to create Clerk user: {e}")