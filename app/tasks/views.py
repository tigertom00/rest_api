from datetime import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from restAPI.utils.audit import AuditLogger
from restAPI.utils.caching import CacheManager, QueryOptimizer, cache_api_response
from restAPI.utils.monitoring import monitor_performance
from restAPI.utils.throttling import (
    APIRateThrottle,
    BulkOperationRateThrottle,
    DatabaseOperationThrottle,
)

from .models import Category, Project, ProjectImage, Task, TaskImage
from .serializers import (
    CategorySerializer,
    ProjectImageSerializer,
    ProjectSerializer,
    TaskImageSerializer,
    TaskSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class TaskViewSet(viewsets.ModelViewSet):
    queryset = (
        Task.objects.all()
        .select_related("user_id")
        .prefetch_related("category", "images")
    )
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    # Testing: Re-enable both throttling classes
    throttle_classes = [APIRateThrottle, DatabaseOperationThrottle]

    def get_queryset(self):
        # Only return tasks for the current user
        queryset = Task.objects.filter(user_id=self.request.user)

        # Apply filters
        filters_applied = {}

        # Category filtering (multiple categories with AND logic)
        categories = self.request.query_params.getlist("category")
        if categories:
            filters_applied["categories"] = categories
            # For multiple categories, we need tasks that have ALL specified categories
            for category in categories:
                queryset = queryset.filter(category__slug=category)

        # Project filtering
        project = self.request.query_params.get("project")
        if project:
            filters_applied["projects"] = [project]
            queryset = queryset.filter(project__name=project)

        # Status filtering (multiple statuses)
        statuses = self.request.query_params.getlist("status")
        if statuses:
            filters_applied["status"] = statuses
            queryset = queryset.filter(status__in=statuses)

        # Priority filtering (multiple priorities)
        priorities = self.request.query_params.getlist("priority")
        if priorities:
            filters_applied["priority"] = priorities
            queryset = queryset.filter(priority__in=priorities)

        # Date range filtering
        due_date_start = self.request.query_params.get("due_date_start")
        due_date_end = self.request.query_params.get("due_date_end")

        if due_date_start or due_date_end:
            date_range = {}
            if due_date_start:
                try:
                    start_date = datetime.fromisoformat(
                        due_date_start.replace("Z", "+00:00")
                    ).date()
                    queryset = queryset.filter(due_date__gte=start_date)
                    date_range["start"] = due_date_start
                except ValueError:
                    pass  # Invalid date format, ignore filter

            if due_date_end:
                try:
                    end_date = datetime.fromisoformat(
                        due_date_end.replace("Z", "+00:00")
                    ).date()
                    queryset = queryset.filter(due_date__lte=end_date)
                    date_range["end"] = due_date_end
                except ValueError:
                    pass  # Invalid date format, ignore filter

            if date_range:
                filters_applied["date_range"] = date_range

        # Full-text search across title and description
        search = self.request.query_params.get("search")
        if search:
            filters_applied["search"] = search
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(notes__icontains=search)
            )

        # Store filters_applied in the request for use in list response
        self.request.filters_applied = filters_applied

        # Apply query optimization - temporarily simplified to debug production issue
        try:
            return QueryOptimizer.optimize_task_queryset(queryset)
        except Exception:
            # Fallback to basic optimization if QueryOptimizer fails
            return queryset.select_related("user_id", "project").prefetch_related(
                "category", "images"
            )

    def perform_create(self, serializer):
        task = serializer.save(user_id=self.request.user)

        # Invalidate user's task cache with error handling
        try:
            CacheManager.invalidate_user_cache(self.request.user.id, ["task_lists"])
            CacheManager.invalidate_list_cache("task_lists")
        except Exception:
            pass  # Don't let cache issues break task creation

        # Broadcast task created event with error handling
        try:
            self.broadcast_task_event(
                "task_created",
                {
                    "task": self.serialize_task_for_websocket(task),
                    "created_by": self.request.user.id,
                },
            )
        except Exception:
            pass  # Don't let websocket issues break task creation

    # Emergency simplified version to fix 500 errors
    def list(self, request, *args, **kwargs):
        """
        Simplified list method to restore service.
        """
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            # Log the error for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Task list error: {str(e)}", exc_info=True)
            raise

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        task = self.get_object()
        serializer = TaskImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="image_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID of the image to delete",
            )
        ]
    )
    @action(detail=True, methods=["delete"], url_path="images/(?P<image_id>[^/.]+)")
    def delete_image(self, request, pk=None, image_id=None):
        task = self.get_object()
        try:
            image = TaskImage.objects.get(id=image_id, task=task)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TaskImage.DoesNotExist:
            return Response(
                {"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "task_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of task IDs to update",
                    },
                    "updates": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["todo", "in_progress", "completed"],
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                            },
                            "category": {"type": "array", "items": {"type": "string"}},
                            "project": {"type": "string"},
                        },
                        "description": "Updates to apply to selected tasks",
                    },
                },
                "required": ["task_ids", "updates"],
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "updated_count": {"type": "integer"},
                    "failed_updates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "error": {"type": "string"},
                            },
                        },
                    },
                },
            }
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="bulk-update",
        throttle_classes=[BulkOperationRateThrottle],
    )
    def bulk_update(self, request):
        """
        Bulk update multiple tasks.

        Request body:
        {
            "task_ids": [1, 2, 3],
            "updates": {
                "status": "completed",
                "priority": "high",
                "category": ["web", "design"],
                "project": "nxfs"
            }
        }
        """
        task_ids = request.data.get("task_ids", [])
        updates = request.data.get("updates", {})

        if not task_ids:
            return Response(
                {"error": "task_ids is required and must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not updates:
            return Response(
                {"error": "updates is required and must be a non-empty object"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only allow updates to tasks owned by the current user
        user_tasks = Task.objects.filter(id__in=task_ids, user_id=request.user)
        found_task_ids = set(user_tasks.values_list("id", flat=True))

        updated_count = 0
        failed_updates = []

        for task_id in task_ids:
            if task_id not in found_task_ids:
                failed_updates.append(
                    {"id": task_id, "error": "Task not found or not owned by user"}
                )
                continue

            try:
                task = user_tasks.get(id=task_id)

                # Apply updates
                if "status" in updates:
                    task.status = updates["status"]

                if "priority" in updates:
                    task.priority = updates["priority"]

                if "project" in updates:
                    project_name = updates["project"]
                    if project_name:
                        try:
                            project = Project.objects.get(
                                name=project_name, user_id=request.user
                            )
                            task.project = project
                        except Project.DoesNotExist:
                            failed_updates.append(
                                {
                                    "id": task_id,
                                    "error": f'Project "{project_name}" not found',
                                }
                            )
                            continue
                    else:
                        task.project = None

                task.save()

                # Handle category updates (many-to-many)
                if "category" in updates:
                    category_names = updates["category"]
                    if isinstance(category_names, list):
                        categories = Category.objects.filter(name__in=category_names)
                        task.category.set(categories)

                updated_count += 1

            except Exception as e:
                failed_updates.append({"id": task_id, "error": str(e)})

        # Log bulk operation
        AuditLogger.log_bulk_operation(
            "update", updated_count, request.user, request, "Task"
        )

        return Response(
            {"updated_count": updated_count, "failed_updates": failed_updates}
        )

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "task_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of task IDs to delete",
                    }
                },
                "required": ["task_ids"],
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "deleted_count": {"type": "integer"},
                    "failed_deletes": {"type": "array", "items": {"type": "integer"}},
                },
            }
        },
    )
    @action(
        detail=False,
        methods=["delete"],
        url_path="bulk-delete",
        throttle_classes=[BulkOperationRateThrottle],
    )
    def bulk_delete(self, request):
        """
        Bulk delete multiple tasks.

        Request body:
        {
            "task_ids": [1, 2, 3]
        }
        """
        task_ids = request.data.get("task_ids", [])

        if not task_ids:
            return Response(
                {"error": "task_ids is required and must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only allow deletion of tasks owned by the current user
        user_tasks = Task.objects.filter(id__in=task_ids, user_id=request.user)
        found_task_ids = list(user_tasks.values_list("id", flat=True))

        deleted_count = user_tasks.count()
        failed_deletes = [
            task_id for task_id in task_ids if task_id not in found_task_ids
        ]

        # Delete the tasks
        user_tasks.delete()

        # Log bulk operation
        AuditLogger.log_bulk_operation(
            "delete", deleted_count, request.user, request, "Task"
        )

        return Response(
            {"deleted_count": deleted_count, "failed_deletes": failed_deletes}
        )

    def perform_update(self, serializer):
        """Override perform_update to broadcast task updated event."""
        task = serializer.save()

        # Invalidate user's task cache
        CacheManager.invalidate_user_cache(self.request.user.id, ["task_lists"])
        CacheManager.invalidate_list_cache("task_lists")

        # Broadcast task updated event
        self.broadcast_task_event(
            "task_updated",
            {
                "task_id": task.id,
                "task": self.serialize_task_for_websocket(task),
                "updated_by": self.request.user.id,
            },
        )

    def perform_destroy(self, instance):
        """Override perform_destroy to broadcast task deleted event."""
        task_id = instance.id

        # Invalidate user's task cache
        CacheManager.invalidate_user_cache(self.request.user.id, ["task_lists"])
        CacheManager.invalidate_list_cache("task_lists")

        # Delete the task
        instance.delete()

        # Broadcast task deleted event
        self.broadcast_task_event(
            "task_deleted", {"task_id": task_id, "deleted_by": self.request.user.id}
        )

    def broadcast_task_event(self, event_type, data):
        """
        Broadcast task events to WebSocket channels.

        Sends events to:
        - Global tasks room
        - Project-specific room (if task has a project)
        - User-specific room
        """
        channel_layer = get_channel_layer()

        if not channel_layer:
            return  # No channel layer configured

        # Send to global tasks room
        async_to_sync(channel_layer.group_send)(
            "task_tasks", {"type": event_type, **data}
        )

        # Send to user-specific room
        async_to_sync(channel_layer.group_send)(
            f"task_user_{self.request.user.id}", {"type": event_type, **data}
        )

        # Send to project-specific room if task has a project
        if event_type in ["task_created", "task_updated"] and "task" in data:
            task_data = data["task"]
            if task_data.get("project_id"):
                async_to_sync(channel_layer.group_send)(
                    f'task_project_{task_data["project_id"]}',
                    {"type": event_type, **data},
                )

    def serialize_task_for_websocket(self, task):
        """Serialize task data for WebSocket transmission."""
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "project_id": task.project.id if task.project else None,
            "project_name": task.project.name if task.project else None,
            "categories": list(task.category.values_list("name", flat=True)),
            "user_id": task.user_id.id,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = (
        Project.objects.all()
        .select_related("user_id")
        .prefetch_related("tasks", "images")
    )
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Only return projects for the current user
        return Project.objects.filter(user_id=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="image_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID of the image to delete",
            )
        ]
    )
    @action(detail=True, methods=["delete"], url_path="images/(?P<image_id>[^/.]+)")
    def delete_image(self, request, pk=None, image_id=None):
        project = self.get_object()
        try:
            image = ProjectImage.objects.get(id=image_id, project=project)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProjectImage.DoesNotExist:
            return Response(
                {"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND
            )
