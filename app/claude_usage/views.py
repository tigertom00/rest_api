from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import Project, Session, UsageSnapshot
from .serializers import (
    ProjectSerializer,
    ProjectListSerializer,
    SessionSerializer,
    UsageSnapshotSerializer,
    UsageStatsSerializer,
)
from .services import ClaudeDataExtractor


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def usage_stats(request):
    """Get overall usage statistics with rate limit information"""
    extractor = ClaudeDataExtractor()
    stats = extractor.get_usage_stats()

    # Add rate limit information
    rate_limit_status = extractor.get_current_rate_limit_status()
    stats.update(rate_limit_status)

    serializer = UsageStatsSerializer(stats)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_list(request):
    """Get all projects"""
    projects = Project.objects.all()
    serializer = ProjectListSerializer(projects, many=True)
    return Response({"projects": serializer.data, "count": len(serializer.data)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_detail(request, project_name):
    """Get detailed info for a specific project"""
    # Try to get from database first
    try:
        project = Project.objects.get(name=project_name)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)
    except Project.DoesNotExist:
        # If not in database, try to get from Claude data
        extractor = ClaudeDataExtractor()
        project_data = extractor.get_project_data(project_name)

        if project_data:
            return Response(project_data)
        else:
            return Response(
                {"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_detail(request, session_id):
    """Get detailed info for a specific session"""
    session = get_object_or_404(Session, session_id=session_id)
    serializer = SessionSerializer(session)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_sessions(request, project_name):
    """Get all sessions for a specific project"""
    project = get_object_or_404(Project, name=project_name)
    sessions = project.sessions.all()
    serializer = SessionSerializer(sessions, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def refresh_data(request):
    """Refresh Claude usage data from files"""
    try:
        from .tasks import update_claude_data

        # For now, run synchronously. In production, you might want to use Celery
        extractor = ClaudeDataExtractor()
        data = extractor.extract_usage_data()

        # Update database with latest data
        for project_data in data:
            project, created = Project.objects.get_or_create(
                name=project_data["project_name"],
                defaults={"path": f"~/.claude/projects/{project_data['project_name']}"},
            )

            for session_data in project_data["sessions"]:
                session, created = Session.objects.get_or_create(
                    session_id=session_data["session_id"],
                    project=project,
                    defaults={
                        "message_count": session_data["message_count"],
                        "total_tokens": session_data["total_tokens"],
                        "total_input_tokens": session_data["total_input_tokens"],
                        "total_output_tokens": session_data["total_output_tokens"],
                        "total_cache_creation_tokens": session_data[
                            "total_cache_creation_tokens"
                        ],
                        "total_cache_read_tokens": session_data[
                            "total_cache_read_tokens"
                        ],
                        "created_at": (
                            session_data["messages"][0]["timestamp"]
                            if session_data["messages"]
                            else None
                        ),
                    },
                )

                # Clear existing usage snapshots for this session to avoid duplicates
                UsageSnapshot.objects.filter(session=session).delete()

                # Create usage snapshots for each message
                for message in session_data["messages"]:
                    UsageSnapshot.objects.create(
                        session=session,
                        project=project,
                        input_tokens=message["message"]["usage"].get("input_tokens", 0),
                        output_tokens=message["message"]["usage"].get(
                            "output_tokens", 0
                        ),
                        cache_creation_tokens=message["message"]["usage"].get(
                            "cache_creation_input_tokens", 0
                        ),
                        cache_read_tokens=message["message"]["usage"].get(
                            "cache_read_input_tokens", 0
                        ),
                        total_tokens=sum(
                            [
                                message["message"]["usage"].get("input_tokens", 0),
                                message["message"]["usage"].get("output_tokens", 0),
                                message["message"]["usage"].get(
                                    "cache_creation_input_tokens", 0
                                ),
                                message["message"]["usage"].get(
                                    "cache_read_input_tokens", 0
                                ),
                            ]
                        ),
                        cost_usd=extractor.calculate_cost(message),
                        model=message["message"]["model"],
                        timestamp=message["timestamp"],
                        request_id=message.get("requestId", ""),
                        message_id=message["message"].get("id", ""),
                    )

        return Response(
            {
                "message": "Data refreshed successfully",
                "projects_updated": len(data),
                "total_sessions": sum(len(p["sessions"]) for p in data),
            }
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agent_sync_claude_usage(request):
    """
    Webhook endpoint for remote agents to sync Claude usage data.
    Similar to docker_monitor's agent_sync_containers.

    Expected payload:
    {
        "projects": [
            {
                "name": "project-name",
                "path": "~/.claude/projects/project-name",
                "sessions": [
                    {
                        "session_id": "uuid",
                        "messages": [
                            {
                                "timestamp": "2025-09-14T11:57:01.497Z",
                                "message": {
                                    "id": "msg_...",
                                    "model": "claude-sonnet-4-20250514",
                                    "usage": {...}
                                },
                                "requestId": "req_...",
                                ...
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """
    try:
        data = request.data
        projects_data = data.get("projects", [])

        if not projects_data:
            return Response(
                {"error": "No projects data provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        projects_updated = 0
        sessions_updated = 0
        snapshots_created = 0

        extractor = ClaudeDataExtractor()

        for project_data in projects_data:
            # Get or create project
            project, created = Project.objects.get_or_create(
                name=project_data["name"],
                defaults={
                    "path": project_data.get(
                        "path", f"~/.claude/projects/{project_data['name']}"
                    )
                },
            )

            if created:
                projects_updated += 1

            # Process sessions
            for session_data in project_data.get("sessions", []):
                messages = session_data.get("messages", [])

                if not messages:
                    continue

                # Calculate session totals
                total_input = sum(
                    m["message"]["usage"].get("input_tokens", 0) for m in messages
                )
                total_output = sum(
                    m["message"]["usage"].get("output_tokens", 0) for m in messages
                )
                total_cache_creation = sum(
                    m["message"]["usage"].get("cache_creation_input_tokens", 0)
                    for m in messages
                )
                total_cache_read = sum(
                    m["message"]["usage"].get("cache_read_input_tokens", 0)
                    for m in messages
                )
                total_tokens = (
                    total_input + total_output + total_cache_creation + total_cache_read
                )

                # Parse timestamp from first message
                created_at = None
                try:
                    created_at = parse_datetime(
                        messages[0]["timestamp"].replace("Z", "+00:00")
                    )
                except (ValueError, TypeError, KeyError):
                    created_at = timezone.now()

                # Get or create session
                session, created = Session.objects.get_or_create(
                    session_id=session_data["session_id"],
                    project=project,
                    defaults={
                        "message_count": len(messages),
                        "total_tokens": total_tokens,
                        "total_input_tokens": total_input,
                        "total_output_tokens": total_output,
                        "total_cache_creation_tokens": total_cache_creation,
                        "total_cache_read_tokens": total_cache_read,
                        "created_at": created_at,
                    },
                )

                if created:
                    sessions_updated += 1
                else:
                    # Update existing session
                    session.message_count = len(messages)
                    session.total_tokens = total_tokens
                    session.total_input_tokens = total_input
                    session.total_output_tokens = total_output
                    session.total_cache_creation_tokens = total_cache_creation
                    session.total_cache_read_tokens = total_cache_read
                    session.save()

                # Clear existing snapshots to avoid duplicates
                UsageSnapshot.objects.filter(session=session).delete()

                # Create usage snapshots
                for message in messages:
                    try:
                        timestamp = parse_datetime(
                            message["timestamp"].replace("Z", "+00:00")
                        )
                        usage = message["message"]["usage"]
                        msg_total_tokens = sum(
                            [
                                usage.get("input_tokens", 0),
                                usage.get("output_tokens", 0),
                                usage.get("cache_creation_input_tokens", 0),
                                usage.get("cache_read_input_tokens", 0),
                            ]
                        )

                        UsageSnapshot.objects.create(
                            session=session,
                            project=project,
                            input_tokens=usage.get("input_tokens", 0),
                            output_tokens=usage.get("output_tokens", 0),
                            cache_creation_tokens=usage.get(
                                "cache_creation_input_tokens", 0
                            ),
                            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
                            total_tokens=msg_total_tokens,
                            cost_usd=extractor.calculate_cost(message),
                            model=message["message"].get("model", "unknown"),
                            timestamp=timestamp,
                            request_id=message.get("requestId", ""),
                            message_id=message["message"].get("id", ""),
                        )
                        snapshots_created += 1
                    except (KeyError, ValueError, TypeError) as e:
                        # Skip malformed messages
                        continue

        return Response(
            {
                "status": "success",
                "message": f"Synced {projects_updated} projects, {sessions_updated} sessions, {snapshots_created} snapshots",
                "projects_updated": projects_updated,
                "sessions_updated": sessions_updated,
                "snapshots_created": snapshots_created,
                "timestamp": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
