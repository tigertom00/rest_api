from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Max
from django.utils import timezone

from .models import ChatRoom, Message, MessageReadStatus, TypingIndicator
from .serializers import (
    ChatRoomSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    MessageUpdateSerializer,
    ChatRoomCreateSerializer,
    DirectMessageRoomSerializer,
    TypingIndicatorSerializer,
    MessageReactionSerializer,
)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for chat endpoints"""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100


class ChatRoomViewSet(viewsets.ModelViewSet):
    """ViewSet for chat room operations"""

    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get chat rooms for current user"""
        user = self.request.user
        return (
            ChatRoom.objects.filter(participants=user, is_active=True)
            .select_related("created_by")
            .prefetch_related("participants")
        )

    def get_serializer_class(self):
        """Get appropriate serializer based on action"""
        if self.action == "create":
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    def perform_create(self, serializer):
        """Set created_by when creating room"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["post"])
    def direct_message(self, request):
        """Create or get direct message room with another user"""
        serializer = DirectMessageRoomSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        other_user_id = serializer.validated_data["user_id"]
        other_user = get_object_or_404(User, id=other_user_id)

        # Check if direct message room already exists
        room = ChatRoom.objects.filter(
            room_type="direct", direct_user1=request.user, direct_user2=other_user
        ).first()

        if not room:
            room = ChatRoom.objects.filter(
                room_type="direct", direct_user1=other_user, direct_user2=request.user
            ).first()

        if not room:
            # Create new direct message room
            room = ChatRoom.objects.create(
                room_type="direct",
                direct_user1=request.user,
                direct_user2=other_user,
                created_by=request.user,
            )
            room.participants.add(request.user, other_user)

        serializer = ChatRoomSerializer(room, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark all messages in room as read"""
        room = self.get_object()
        user = request.user

        # Mark all unread messages as read
        unread_messages = Message.objects.filter(room=room, is_deleted=False).exclude(
            id__in=MessageReadStatus.objects.filter(user=user).values_list(
                "message_id", flat=True
            )
        )

        # Create read statuses
        read_statuses = [
            MessageReadStatus(message=message, user=user) for message in unread_messages
        ]
        MessageReadStatus.objects.bulk_create(read_statuses)

        return Response({"status": "marked as read", "count": len(read_statuses)})

    @action(detail=True, methods=["get"])
    def typing_users(self, request, pk=None):
        """Get list of users currently typing in this room"""
        room = self.get_object()

        # Get active typing indicators (last 30 seconds)
        thirty_seconds_ago = timezone.now() - timezone.timedelta(seconds=30)
        typing_users = TypingIndicator.objects.filter(
            room=room, is_typing=True, last_seen__gte=thirty_seconds_ago
        ).select_related("user")

        serializer = TypingIndicatorSerializer(typing_users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        """Leave a chat room (for group/project rooms)"""
        room = self.get_object()

        if room.room_type == "direct":
            return Response(
                {"error": "Cannot leave direct message rooms"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        room.participants.remove(request.user)
        return Response({"status": "left room"})


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for message operations"""

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get messages for a specific room"""
        room_id = self.kwargs.get("room_pk")
        if not room_id:
            return Message.objects.none()

        # Verify user has access to this room
        room = get_object_or_404(ChatRoom, id=room_id)
        if not room.participants.filter(id=self.request.user.id).exists():
            return Message.objects.none()

        return (
            Message.objects.filter(room=room_id, is_deleted=False)
            .select_related("sender", "reply_to")
            .order_by("timestamp")
        )

    def get_serializer_class(self):
        """Get appropriate serializer based on action"""
        if self.action == "create":
            return MessageCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return MessageUpdateSerializer
        return MessageSerializer

    def perform_create(self, serializer):
        """Set sender and room when creating message"""
        room_id = self.kwargs.get("room_pk")
        room = get_object_or_404(ChatRoom, id=room_id)

        # Verify user has access to this room
        if not room.participants.filter(id=self.request.user.id).exists():
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You don't have access to this room")

        serializer.save(sender=self.request.user, room=room)

        # Update room timestamp
        room.updated_at = timezone.now()
        room.save()

    def perform_update(self, serializer):
        """Only allow sender to edit their own messages"""
        message = self.get_object()
        if message.sender != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only edit your own messages")

        serializer.save(edited_at=timezone.now())

    def perform_destroy(self, instance):
        """Soft delete message (only sender can delete)"""
        if instance.sender != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only delete your own messages")

        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=["post"])
    def react(self, request, room_pk=None, pk=None):
        """Add or remove reaction to message"""
        message = self.get_object()
        serializer = MessageReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        emoji = serializer.validated_data["emoji"]
        action = serializer.validated_data["action"]

        reactions = message.reactions or {}

        if action == "add":
            if emoji not in reactions:
                reactions[emoji] = []
            user_id_str = str(request.user.id)
            if user_id_str not in reactions[emoji]:
                reactions[emoji].append(user_id_str)
        else:  # remove
            if emoji in reactions:
                user_id_str = str(request.user.id)
                if user_id_str in reactions[emoji]:
                    reactions[emoji].remove(user_id_str)
                if not reactions[emoji]:
                    del reactions[emoji]

        message.reactions = reactions
        message.save()

        return Response({"reactions": reactions, "message": f"Reaction {action}ed"})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, room_pk=None, pk=None):
        """Mark specific message as read"""
        message = self.get_object()

        read_status, created = MessageReadStatus.objects.get_or_create(
            message=message, user=request.user
        )

        return Response({"status": "marked as read", "was_already_read": not created})


class ChatSearchViewSet(viewsets.ViewSet):
    """ViewSet for searching chat content"""

    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def messages(self, request):
        """Search messages across user's rooms"""
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"error": "Search query is required"}, status=400)

        # Get user's rooms
        user_rooms = ChatRoom.objects.filter(participants=request.user)

        # Search messages
        messages = (
            Message.objects.filter(
                room__in=user_rooms, content__icontains=query, is_deleted=False
            )
            .select_related("sender", "room")
            .order_by("-timestamp")[:50]
        )

        serializer = MessageSerializer(
            messages, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def rooms(self, request):
        """Search chat rooms"""
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"error": "Search query is required"}, status=400)

        rooms = (
            ChatRoom.objects.filter(participants=request.user, is_active=True)
            .filter(
                Q(name__icontains=query)
                | Q(participants__email__icontains=query)
                | Q(participants__display_name__icontains=query)
            )
            .distinct()
            .select_related("created_by")
            .prefetch_related("participants")
        )

        serializer = ChatRoomSerializer(rooms, many=True, context={"request": request})
        return Response(serializer.data)


class ChatSessionViewSet(viewsets.ViewSet):
    """ViewSet for chat session management"""

    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def active_sessions(self, request):
        """Get user's active chat sessions"""
        from restAPI.models import ChatSession

        sessions = ChatSession.objects.filter(
            user=request.user, is_active=True
        ).order_by("-last_ping")

        session_data = []
        for session in sessions:
            session_data.append(
                {
                    "session_id": str(session.id),
                    "session_type": session.session_type,
                    "is_active": session.is_active,
                    "last_ping": session.last_ping,
                    "connected_at": session.connected_at,
                    "user_agent": session.user_agent,
                    "ip_address": session.ip_address,
                }
            )

        return Response(session_data)

    @action(detail=False, methods=["post"])
    def cleanup_old_sessions(self, request):
        """Clean up old inactive sessions"""
        from restAPI.models import ChatSession

        # Remove sessions inactive for more than 24 hours
        cutoff_time = timezone.now() - timezone.timedelta(hours=24)
        deleted_count = ChatSession.objects.filter(
            user=request.user, is_active=False, last_ping__lt=cutoff_time
        ).delete()[0]

        return Response(
            {"status": "cleanup completed", "deleted_sessions": deleted_count}
        )
