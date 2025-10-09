import os
import uuid
from django.utils import timezone

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


# Users
class CustomUserManager(UserManager):
    def create_user(self, email, password=None, username=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        if not username:
            username = email.split("@")[0]
        extra_fields["username"] = username
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class UserEmail(models.Model):
    user = models.ForeignKey(
        "CustomUser", related_name="emails", on_delete=models.CASCADE
    )
    email = models.EmailField()
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.email


class UserPhone(models.Model):
    user = models.ForeignKey(
        "CustomUser", related_name="phones", on_delete=models.CASCADE
    )
    phone_nr = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.phone_nr


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=50, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_image", default="default/profile.png"
    )
    clerk_profile_image_url = models.URLField(blank=True, null=True)
    theme = models.CharField(
        max_length=20,
        choices=[
            ("light", "Light"),
            ("dark", "Dark"),
            ("pink", "Pink"),
            ("purple", "Purple"),
            ("system", "System"),
        ],
        default="dark",
    )
    clerk_user_id = models.CharField(max_length=255, blank=True, null=True)
    has_image = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    clerk_updated_at = models.DateTimeField(auto_now=True)
    language = models.CharField(
        max_length=10,
        choices=[
            ("en", "English"),
            ("no", "Norwegian"),
        ],
        default="en",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        if not self.username and self.email:
            self.username = self.email.split("@")[0]
            if len(self.username) < 4:
                self.username = self.username + os.urandom(2).hex()[:8]
        if not self.display_name and self.username:
            self.display_name = self.username.capitalize()
        elif self.display_name:
            self.display_name = self.display_name.capitalize()
        super(CustomUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.email


class AuditLog(models.Model):
    """
    Model for storing audit log entries.
    Tracks sensitive operations for security and compliance.
    """

    class ActionType(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"
        PERMISSION_CHANGE = "PERMISSION_CHANGE", "Permission Change"
        BULK_OPERATION = "BULK_OPERATION", "Bulk Operation"
        ADMIN_ACTION = "ADMIN_ACTION", "Admin Action"
        FILE_UPLOAD = "FILE_UPLOAD", "File Upload"
        DATA_EXPORT = "DATA_EXPORT", "Data Export"
        ACCESS_DENIED = "ACCESS_DENIED", "Access Denied"

    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    user_email = models.EmailField(blank=True)  # Store email in case user is deleted
    action = models.CharField(max_length=50, choices=ActionType.choices, db_index=True)
    resource = models.CharField(
        max_length=100, db_index=True
    )  # e.g., 'Task', 'User', 'BlogMedia'
    resource_id = models.CharField(max_length=50, blank=True, db_index=True)
    description = models.TextField()
    severity = models.CharField(
        max_length=10, choices=Severity.choices, default=Severity.LOW
    )

    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)

    # Additional context
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp", "action"]),
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["severity", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.timestamp} - {self.user_email or 'Anonymous'} - {self.action} - {self.resource}"


class ChatSession(models.Model):
    """Track individual chat sessions for users across multiple devices"""

    SESSION_TYPES = [
        ("web", "Web Browser"),
        ("mobile", "Mobile App"),
        ("desktop", "Desktop App"),
        ("api", "API Client"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "CustomUser", on_delete=models.CASCADE, related_name="chat_sessions"
    )
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default="web")

    # Connection tracking
    websocket_channel = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_ping = models.DateTimeField(auto_now=True)

    # Device/Client info
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id = models.CharField(max_length=255, blank=True, null=True)

    # n8n integration for chatbot
    n8n_conversation_id = models.CharField(max_length=255, blank=True, null=True)
    is_bot_session = models.BooleanField(default=False)
    bot_context = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    connected_at = models.DateTimeField(null=True, blank=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_ping"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["websocket_channel"]),
            models.Index(fields=["last_ping"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.session_type} ({self.id})"

    def get_n8n_session_id(self):
        """Return appropriate ID for n8n webhook"""
        return self.n8n_conversation_id or str(self.id)

    def update_connection(self, channel_name=None, user_agent=None, ip_address=None):
        """Update connection information"""
        if channel_name:
            self.websocket_channel = channel_name
        if user_agent:
            self.user_agent = user_agent
        if ip_address:
            self.ip_address = ip_address
        if not self.connected_at:
            self.connected_at = timezone.now()
        self.is_active = True
        self.save()


class UserDevice(models.Model):
    """
    Model for tracking user devices (primarily mobile devices).
    Used for push notifications, session management, and security monitoring.
    """

    DEVICE_TYPES = [
        ("ios", "iOS"),
        ("android", "Android"),
        ("web", "Web Browser"),
        ("desktop", "Desktop App"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="devices"
    )
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    device_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="User-friendly device name (e.g., 'iPhone 15')",
    )

    # Device identification
    device_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Unique device identifier from the device",
    )

    # Push notification token (for Expo or FCM/APNS)
    push_token = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Expo push token or FCM/APNS token",
    )

    # Device/OS information
    os_version = models.CharField(max_length=50, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(blank=True)

    # Security tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_active = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True, help_text="Set to False to revoke this device session"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Device"
        verbose_name_plural = "User Devices"
        ordering = ["-last_active"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["device_id"]),
            models.Index(fields=["push_token"]),
            models.Index(fields=["last_active"]),
        ]
        # Ensure unique device_id per user (if device_id is provided)
        constraints = [
            models.UniqueConstraint(
                fields=["user", "device_id"],
                condition=models.Q(device_id__isnull=False),
                name="unique_user_device_id",
            )
        ]

    def __str__(self):
        device_display = self.device_name or f"{self.get_device_type_display()}"
        return f"{self.user.email} - {device_display}"

    def revoke(self):
        """Revoke this device's access"""
        self.is_active = False
        self.save()

    def update_activity(self, ip_address=None):
        """Update last active timestamp and optionally IP address"""
        if ip_address:
            self.ip_address = ip_address
        self.last_active = timezone.now()
        self.save(update_fields=["last_active", "ip_address"])
