from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from app.claude_usage.services import ClaudeDataExtractor
from app.claude_usage.models import Project, Session, UsageSnapshot


class Command(BaseCommand):
    help = "Update Claude usage data from local JSONL files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--claude-path",
            type=str,
            default="~/.claude",
            help="Path to Claude data directory (default: ~/.claude)",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Enable verbose output"
        )

    def handle(self, *args, **options):
        claude_path = options["claude_path"]
        verbose = options["verbose"]

        self.stdout.write(f"Updating Claude usage data from {claude_path}")

        try:
            extractor = ClaudeDataExtractor(claude_path)
            data = extractor.extract_usage_data()

            if not data:
                self.stdout.write(self.style.WARNING("No Claude data found"))
                return

            projects_updated = 0
            sessions_updated = 0
            snapshots_created = 0

            for project_data in data:
                project, created = Project.objects.get_or_create(
                    name=project_data["project_name"],
                    defaults={
                        "path": f"{claude_path}/projects/{project_data['project_name']}"
                    },
                )

                if created:
                    projects_updated += 1
                    if verbose:
                        self.stdout.write(f"Created new project: {project.name}")

                for session_data in project_data["sessions"]:
                    # Parse timestamp from first message
                    created_at = None
                    if session_data["messages"]:
                        try:
                            created_at = parse_datetime(
                                session_data["messages"][0]["timestamp"].replace(
                                    "Z", "+00:00"
                                )
                            )
                        except (ValueError, TypeError):
                            pass

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
                            "created_at": created_at,
                        },
                    )

                    if created:
                        sessions_updated += 1
                        if verbose:
                            self.stdout.write(
                                f"Created new session: {session.session_id}"
                            )
                    else:
                        # Update existing session with latest data
                        session.message_count = session_data["message_count"]
                        session.total_tokens = session_data["total_tokens"]
                        session.total_input_tokens = session_data["total_input_tokens"]
                        session.total_output_tokens = session_data[
                            "total_output_tokens"
                        ]
                        session.total_cache_creation_tokens = session_data[
                            "total_cache_creation_tokens"
                        ]
                        session.total_cache_read_tokens = session_data[
                            "total_cache_read_tokens"
                        ]
                        session.save()

                    # Clear existing usage snapshots for this session to avoid duplicates
                    existing_snapshots = UsageSnapshot.objects.filter(
                        session=session
                    ).count()
                    if existing_snapshots > 0:
                        UsageSnapshot.objects.filter(session=session).delete()
                        if verbose:
                            self.stdout.write(
                                f"Removed {existing_snapshots} existing snapshots for session {session.session_id}"
                            )

                    # Create usage snapshots for each message
                    for message in session_data["messages"]:
                        try:
                            timestamp = parse_datetime(
                                message["timestamp"].replace("Z", "+00:00")
                            )
                            total_tokens = sum(
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
                            )

                            UsageSnapshot.objects.create(
                                session=session,
                                project=project,
                                input_tokens=message["message"]["usage"].get(
                                    "input_tokens", 0
                                ),
                                output_tokens=message["message"]["usage"].get(
                                    "output_tokens", 0
                                ),
                                cache_creation_tokens=message["message"]["usage"].get(
                                    "cache_creation_input_tokens", 0
                                ),
                                cache_read_tokens=message["message"]["usage"].get(
                                    "cache_read_input_tokens", 0
                                ),
                                total_tokens=total_tokens,
                                cost_usd=extractor.calculate_cost(message),
                                model=message["message"]["model"],
                                timestamp=timestamp,
                                request_id=message.get("requestId", ""),
                                message_id=message["message"].get("id", ""),
                            )
                            snapshots_created += 1
                        except (KeyError, ValueError, TypeError) as e:
                            if verbose:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"Skipping malformed message: {e}"
                                    )
                                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated Claude data:\n"
                    f"  Projects: {projects_updated}\n"
                    f"  Sessions: {sessions_updated}\n"
                    f"  Usage snapshots: {snapshots_created}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating Claude data: {e}"))
            raise
