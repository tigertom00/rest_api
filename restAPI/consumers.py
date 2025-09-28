import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from app.tasks.models import Task

User = get_user_model()


class TaskConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time task updates.

    Handles room management for:
    - 'tasks' - Global task updates
    - 'project_{id}' - Project-specific updates
    - 'user_{id}' - User-specific notifications
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        # Determine room based on URL path
        self.room_name = self.get_room_name()
        self.room_group_name = f"task_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Send user joined event
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "user_joined", "user_id": self.user.id, "room": self.room_name},
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "room_group_name"):
            # Send user left event
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "user_left", "user_id": self.user.id, "room": self.room_name},
            )

            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type")

            if message_type == "join_room":
                await self.handle_join_room(text_data_json)
            elif message_type == "leave_room":
                await self.handle_leave_room(text_data_json)
            elif message_type == "task_update":
                await self.handle_task_update(text_data_json)
            else:
                await self.send(
                    text_data=json.dumps(
                        {"error": f"Unknown message type: {message_type}"}
                    )
                )

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))

    def get_room_name(self):
        """Get room name from URL path."""
        url_route = self.scope["url_route"]

        if "project_id" in url_route["kwargs"]:
            return f"project_{url_route['kwargs']['project_id']}"
        elif "user_id" in url_route["kwargs"]:
            return f"user_{url_route['kwargs']['user_id']}"
        else:
            return "tasks"  # Global tasks room

    async def handle_join_room(self, data):
        """Handle join room request."""
        new_room = data.get("room", "tasks")

        # Leave current room
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Join new room
        self.room_name = new_room
        self.room_group_name = f"task_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.send(
            text_data=json.dumps({"type": "room_joined", "room": self.room_name})
        )

    async def handle_leave_room(self, data):
        """Handle leave room request."""
        room_to_leave = data.get("room")

        if room_to_leave:
            room_group_name = f"task_{room_to_leave}"
            await self.channel_layer.group_discard(room_group_name, self.channel_name)

        await self.send(
            text_data=json.dumps({"type": "room_left", "room": room_to_leave})
        )

    async def handle_task_update(self, data):
        """Handle task update from client."""
        task_id = data.get("task_id")
        updates = data.get("updates", {})

        if not task_id:
            await self.send(text_data=json.dumps({"error": "task_id is required"}))
            return

        try:
            # Update task in database
            task = await self.update_task(task_id, updates)

            if task:
                # Broadcast update to room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "task_updated",
                        "task_id": task_id,
                        "task": await self.get_task_data(task),
                        "updated_by": self.user.id,
                    },
                )
            else:
                await self.send(
                    text_data=json.dumps({"error": "Task not found or access denied"})
                )

        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))

    @database_sync_to_async
    def update_task(self, task_id, updates):
        """Update task in database."""
        try:
            task = Task.objects.get(id=task_id, user_id=self.user)

            # Apply updates
            for field, value in updates.items():
                if hasattr(task, field) and field in [
                    "status",
                    "priority",
                    "title",
                    "description",
                ]:
                    setattr(task, field, value)

            task.save()
            return task
        except Task.DoesNotExist:
            return None

    @database_sync_to_async
    def get_task_data(self, task):
        """Get task data for serialization."""
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "updated_at": task.updated_at.isoformat(),
        }

    # Event handlers for group messages
    async def task_updated(self, event):
        """Send task updated event to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "task_updated",
                    "task_id": event["task_id"],
                    "task": event["task"],
                    "updated_by": event["updated_by"],
                }
            )
        )

    async def task_created(self, event):
        """Send task created event to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "task_created",
                    "task": event["task"],
                    "created_by": event["created_by"],
                }
            )
        )

    async def task_deleted(self, event):
        """Send task deleted event to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "task_deleted",
                    "task_id": event["task_id"],
                    "deleted_by": event["deleted_by"],
                }
            )
        )

    async def user_joined(self, event):
        """Send user joined event to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_joined",
                    "user_id": event["user_id"],
                    "room": event["room"],
                }
            )
        )

    async def user_left(self, event):
        """Send user left event to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "user_id": event["user_id"],
                    "room": event["room"],
                }
            )
        )

    async def notification(self, event):
        """Send notification event to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "notification_type": event["notification_type"],
                    "message": event["message"],
                    "data": event.get("data"),
                }
            )
        )
