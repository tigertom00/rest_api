from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, MessageReadStatus, TypingIndicator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for chat"""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "display_name",
            "profile_picture",
            "clerk_profile_image_url",
        ]


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for chat rooms"""

    participants = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "room_type",
            "participants",
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
            "last_message",
            "unread_count",
            "other_user",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_last_message(self, obj):
        """Get the last message in the room"""
        last_message = (
            obj.messages.filter(is_deleted=False).order_by("-timestamp").first()
        )
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None

    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        user = self.context["request"].user
        if user.is_authenticated:
            total_messages = obj.messages.filter(is_deleted=False).count()
            read_messages = MessageReadStatus.objects.filter(
                message__room=obj, user=user
            ).count()
            return max(0, total_messages - read_messages)
        return 0

    def get_other_user(self, obj):
        """For direct messages, get the other user"""
        if obj.room_type == "direct":
            user = self.context["request"].user
            other_user = obj.get_other_user(user)
            if other_user:
                return UserSerializer(other_user).data
        return None


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages"""

    sender = UserSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()
    read_by = serializers.SerializerMethodField()
    is_edited = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "room",
            "sender",
            "content",
            "message_type",
            "file_attachment",
            "file_name",
            "file_size",
            "timestamp",
            "edited_at",
            "is_deleted",
            "reply_to",
            "reactions",
            "read_by",
            "is_edited",
        ]
        read_only_fields = ["id", "sender", "timestamp", "edited_at", "read_by"]

    def get_reply_to(self, obj):
        """Get reply-to message details"""
        if obj.reply_to and not obj.reply_to.is_deleted:
            return {
                "id": str(obj.reply_to.id),
                "content": (
                    obj.reply_to.content[:100] + "..."
                    if len(obj.reply_to.content) > 100
                    else obj.reply_to.content
                ),
                "sender": UserSerializer(obj.reply_to.sender).data,
            }
        return None

    def get_read_by(self, obj):
        """Get list of users who read this message"""
        read_statuses = MessageReadStatus.objects.filter(message=obj)
        users = [status.user for status in read_statuses]
        return UserSerializer(users, many=True).data

    def get_is_edited(self, obj):
        """Check if message was edited"""
        return obj.edited_at is not None


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""

    class Meta:
        model = Message
        fields = ["content", "message_type", "reply_to", "file_attachment"]

    def validate_content(self, value):
        """Validate message content"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip()

    def validate_reply_to(self, value):
        """Validate reply-to message"""
        if value and value.is_deleted:
            raise serializers.ValidationError("Cannot reply to a deleted message")
        return value


class MessageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating messages"""

    class Meta:
        model = Message
        fields = ["content", "is_deleted"]

    def validate_content(self, value):
        """Validate updated content"""
        if value and not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip() if value else None


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat rooms"""

    participant_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )

    class Meta:
        model = ChatRoom
        fields = ["name", "room_type", "participant_ids"]

    def validate_participant_ids(self, value):
        """Validate participant IDs"""
        if self.initial_data.get("room_type") in ["group", "project"] and not value:
            raise serializers.ValidationError(
                "Group and project rooms must have participants"
            )

        # Check if users exist
        existing_users = User.objects.filter(id__in=value).count()
        if existing_users != len(value):
            raise serializers.ValidationError("One or more participants not found")

        return value

    def create(self, validated_data):
        """Create chat room with participants"""
        participant_ids = validated_data.pop("participant_ids", [])
        user = validated_data.pop("user", None)  # Get user from context

        room = ChatRoom.objects.create(created_by=user, **validated_data)

        # Add participants
        participants = User.objects.filter(id__in=participant_ids)
        room.participants.add(*participants)

        # Add creator as participant if not already included
        if user and user not in participants:
            room.participants.add(user)

        return room


class DirectMessageRoomSerializer(serializers.Serializer):
    """Serializer for creating direct message rooms"""

    user_id = serializers.UUIDField()

    def validate_user_id(self, value):
        """Validate other user"""
        try:
            other_user = User.objects.get(id=value)
            if other_user == self.context["request"].user:
                raise serializers.ValidationError(
                    "Cannot start a direct message with yourself"
                )
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")


class TypingIndicatorSerializer(serializers.ModelSerializer):
    """Serializer for typing indicators"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = TypingIndicator
        fields = ["room", "user", "is_typing", "last_seen"]
        read_only_fields = ["user", "last_seen"]


class ChatSessionSerializer(serializers.Serializer):
    """Serializer for chat session info"""

    session_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    session_type = serializers.CharField()
    is_active = serializers.BooleanField()
    last_ping = serializers.DateTimeField()
    device_info = serializers.DictField()


class MessageReactionSerializer(serializers.Serializer):
    """Serializer for message reactions"""

    emoji = serializers.CharField(max_length=50)
    action = serializers.ChoiceField(choices=["add", "remove"])

    def validate_emoji(self, value):
        """Validate emoji"""
        # Basic emoji validation - you might want to use a proper emoji library
        if len(value) > 50:
            raise serializers.ValidationError("Emoji too long")
        return value
