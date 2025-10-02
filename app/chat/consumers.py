import json
import uuid
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import ChatRoom, Message, MessageReadStatus, TypingIndicator

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for chat room functionality"""

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        # Get or create chat session
        self.chat_session = await self.get_or_create_chat_session()

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Update session with WebSocket channel
        await self.update_chat_session(self.channel_name)

        await self.accept()

        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user": self.user.email,
                "user_id": str(self.user.id),
            },
        )

    async def disconnect(self, close_code):
        # Mark session as inactive
        await self.deactivate_chat_session()

        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                "user": self.user.email,
                "user_id": str(self.user.id),
            },
        )

        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "message")

        if message_type == "message":
            await self.handle_message(data)
        elif message_type == "typing":
            await self.handle_typing(data)
        elif message_type == "read_receipt":
            await self.handle_read_receipt(data)

    async def handle_message(self, data):
        """Handle incoming message"""
        content = data.get("content", "").strip()
        reply_to_id = data.get("reply_to", None)

        if not content:
            return

        # Save message to database
        message = await self.save_message(content, reply_to_id)

        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": await self.serialize_message(message)},
        )

    async def handle_typing(self, data):
        """Handle typing indicators"""
        is_typing = data.get("is_typing", False)

        if is_typing:
            await self.set_typing(True)
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user": self.user.email,
                    "user_id": str(self.user.id),
                    "is_typing": True,
                },
            )
        else:
            await self.set_typing(False)
            # Broadcast stop typing
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user": self.user.email,
                    "user_id": str(self.user.id),
                    "is_typing": False,
                },
            )

    async def handle_read_receipt(self, data):
        """Handle read receipts"""
        message_id = data.get("message_id")
        if message_id:
            await self.mark_message_read(message_id)

    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(
            text_data=json.dumps({"type": "message", "message": event["message"]})
        )

    async def user_joined(self, event):
        """Notify when user joins"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_joined",
                    "user": event["user"],
                    "user_id": event["user_id"],
                }
            )
        )

    async def user_left(self, event):
        """Notify when user leaves"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "user": event["user"],
                    "user_id": event["user_id"],
                }
            )
        )

    async def typing_indicator(self, event):
        """Send typing indicator"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing",
                    "user": event["user"],
                    "user_id": event["user_id"],
                    "is_typing": event["is_typing"],
                }
            )
        )

    @database_sync_to_async
    def get_or_create_chat_session(self):
        """Get or create chat session for this connection"""
        from restAPI.models import ChatSession

        session, created = ChatSession.objects.get_or_create(
            user=self.user,
            session_type="web",
            defaults={
                "user_agent": self.scope.get("headers", {}).get("user-agent", [""])[0],
                "ip_address": self.scope.get("client", [None])[0],
            },
        )
        return session

    @database_sync_to_async
    def update_chat_session(self, channel_name):
        """Update chat session with WebSocket info"""
        self.chat_session.websocket_channel = channel_name
        self.chat_session.is_active = True
        self.chat_session.connected_at = timezone.now()
        self.chat_session.save()

    @database_sync_to_async
    def deactivate_chat_session(self):
        """Deactivate chat session"""
        self.chat_session.is_active = False
        self.chat_session.disconnected_at = timezone.now()
        self.chat_session.save()

    @database_sync_to_async
    def save_message(self, content, reply_to_id=None):
        """Save message to database"""
        room = ChatRoom.objects.get(id=self.room_id)
        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id)
            except Message.DoesNotExist:
                pass

        message = Message.objects.create(
            room=room, sender=self.user, content=content, reply_to=reply_to
        )

        # Update room timestamp
        room.updated_at = timezone.now()
        room.save()

        return message

    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for WebSocket"""
        return {
            "id": str(message.id),
            "content": message.content,
            "sender": {
                "id": str(message.sender.id),
                "email": message.sender.email,
                "display_name": message.sender.display_name,
            },
            "timestamp": message.timestamp.isoformat(),
            "message_type": message.message_type,
            "reply_to": str(message.reply_to.id) if message.reply_to else None,
            "reactions": message.reactions,
        }

    @database_sync_to_async
    def set_typing(self, is_typing):
        """Set typing indicator"""
        room = ChatRoom.objects.get(id=self.room_id)
        typing_indicator, created = TypingIndicator.objects.get_or_create(
            room=room, user=self.user, defaults={"is_typing": is_typing}
        )

        if not created:
            typing_indicator.is_typing = is_typing
            typing_indicator.save()

    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(id=message_id)
            MessageReadStatus.objects.get_or_create(message=message, user=self.user)
        except Message.DoesNotExist:
            pass


class DirectMessageConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for direct messages between users"""

    async def connect(self):
        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        # Get or create direct message room
        self.room = await self.get_or_create_direct_room()
        self.room_group_name = f"chat_{self.room.id}"

        # Get or create chat session
        self.chat_session = await self.get_or_create_chat_session()

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Update session
        await self.update_chat_session(self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.deactivate_chat_session()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "message")

        if message_type == "message":
            await self.handle_message(data)
        elif message_type == "typing":
            await self.handle_typing(data)

    async def handle_message(self, data):
        content = data.get("content", "").strip()
        if not content:
            return

        message = await self.save_message(content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": await self.serialize_message(message)},
        )

    async def handle_typing(self, data):
        is_typing = data.get("is_typing", False)
        await self.set_typing(is_typing)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user": self.user.email,
                "user_id": str(self.user.id),
                "is_typing": is_typing,
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps({"type": "message", "message": event["message"]})
        )

    async def typing_indicator(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing",
                    "user": event["user"],
                    "user_id": event["user_id"],
                    "is_typing": event["is_typing"],
                }
            )
        )

    @database_sync_to_async
    def get_or_create_direct_room(self):
        """Get or create direct message room between two users"""
        other_user = User.objects.get(id=self.other_user_id)

        # Check if room already exists
        room = ChatRoom.objects.filter(
            room_type="direct", direct_user1=self.user, direct_user2=other_user
        ).first()

        if not room:
            room = ChatRoom.objects.filter(
                room_type="direct", direct_user1=other_user, direct_user2=self.user
            ).first()

        if not room:
            # Create new direct message room
            room = ChatRoom.objects.create(
                room_type="direct",
                direct_user1=self.user,
                direct_user2=other_user,
                created_by=self.user,
            )
            room.participants.add(self.user, other_user)

        return room

    @database_sync_to_async
    def get_or_create_chat_session(self):
        from restAPI.models import ChatSession

        session, created = ChatSession.objects.get_or_create(
            user=self.user,
            session_type="web",
            defaults={
                "user_agent": self.scope.get("headers", {}).get("user-agent", [""])[0],
                "ip_address": self.scope.get("client", [None])[0],
            },
        )
        return session

    @database_sync_to_async
    def update_chat_session(self, channel_name):
        self.chat_session.websocket_channel = channel_name
        self.chat_session.is_active = True
        self.chat_session.connected_at = timezone.now()
        self.chat_session.save()

    @database_sync_to_async
    def deactivate_chat_session(self):
        self.chat_session.is_active = False
        self.chat_session.disconnected_at = timezone.now()
        self.chat_session.save()

    @database_sync_to_async
    def save_message(self, content):
        message = Message.objects.create(
            room=self.room, sender=self.user, content=content
        )

        self.room.updated_at = timezone.now()
        self.room.save()

        return message

    @database_sync_to_async
    def serialize_message(self, message):
        return {
            "id": str(message.id),
            "content": message.content,
            "sender": {
                "id": str(message.sender.id),
                "email": message.sender.email,
                "display_name": message.sender.display_name,
            },
            "timestamp": message.timestamp.isoformat(),
            "message_type": message.message_type,
            "reply_to": str(message.reply_to.id) if message.reply_to else None,
            "reactions": message.reactions,
        }

    @database_sync_to_async
    def set_typing(self, is_typing):
        typing_indicator, created = TypingIndicator.objects.get_or_create(
            room=self.room, user=self.user, defaults={"is_typing": is_typing}
        )

        if not created:
            typing_indicator.is_typing = is_typing
            typing_indicator.save()
