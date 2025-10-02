from django.contrib import admin
from .models import ChatRoom, Message, MessageReadStatus, TypingIndicator


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "room_type", "is_active", "created_at", "updated_at")
    list_filter = ("room_type", "is_active", "created_at")
    search_fields = ("name", "participants__email")
    readonly_fields = ("id", "created_at", "updated_at")
    filter_horizontal = ("participants",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "room",
        "sender",
        "message_type",
        "timestamp",
        "is_deleted",
    )
    list_filter = ("message_type", "is_deleted", "timestamp")
    search_fields = ("content", "sender__email", "room__name")
    readonly_fields = ("id", "timestamp", "edited_at")
    raw_id_fields = ("room", "sender", "reply_to")


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ("message", "user", "read_at")
    list_filter = ("read_at",)
    search_fields = ("user__email", "message__content")
    readonly_fields = ("read_at",)
    raw_id_fields = ("message", "user")


@admin.register(TypingIndicator)
class TypingIndicatorAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "is_typing", "last_seen")
    list_filter = ("is_typing", "last_seen")
    search_fields = ("user__email", "room__name")
    readonly_fields = ("last_seen",)
    raw_id_fields = ("room", "user")
