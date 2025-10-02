import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatRoom(models.Model):
    """Different types of chat rooms for conversations"""

    ROOM_TYPES = [
        ("direct", "Direct Message"),
        ("group", "Group Chat"),
        ("project", "Project-based"),
        ("public", "Public Channel"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True, null=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default="direct")
    participants = models.ManyToManyField(User, related_name="chat_rooms")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_rooms"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # For direct message rooms, store the two users
    direct_user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="direct_rooms_user1",
    )
    direct_user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="direct_rooms_user2",
    )

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["room_type", "is_active"]),
            models.Index(fields=["direct_user1", "direct_user2"]),
        ]

    def __str__(self):
        if self.room_type == "direct" and self.direct_user1 and self.direct_user2:
            return f"DM: {self.direct_user1.email} ↔ {self.direct_user2.email}"
        return self.name or f"Room {self.id}"

    def get_other_user(self, user):
        """For direct messages, get the other participant"""
        if self.room_type == "direct":
            if self.direct_user1 == user:
                return self.direct_user2
            elif self.direct_user2 == user:
                return self.direct_user1
        return None


class Message(models.Model):
    """Core message model for chat conversations"""

    MESSAGE_TYPES = [
        ("text", "Text"),
        ("image", "Image"),
        ("file", "File"),
        ("system", "System"),
        ("typing", "Typing Indicator"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20, choices=MESSAGE_TYPES, default="text"
    )

    # File attachments
    file_attachment = models.FileField(upload_to="chat_files/", null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)

    # Timestamps and status
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    # Thread support
    reply_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies"
    )

    # Reactions
    reactions = models.JSONField(default=dict, blank=True)  # {"emoji": [user_ids]}

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["room", "timestamp"]),
            models.Index(fields=["sender", "timestamp"]),
            models.Index(fields=["is_deleted", "timestamp"]),
        ]

    def __str__(self):
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50 else self.content
        )
        return f"{self.sender.email}: {content_preview}"


class MessageReadStatus(models.Model):
    """Track read receipts for messages"""

    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["message", "user"]
        indexes = [
            models.Index(fields=["user", "read_at"]),
            models.Index(fields=["message", "read_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} read {self.message.id}"


class TypingIndicator(models.Model):
    """Track who is typing in which room"""

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["room", "user"]
        indexes = [
            models.Index(fields=["room", "is_typing", "last_seen"]),
        ]

    def __str__(self):
        return f"{self.user.email} typing in {self.room.id}"
