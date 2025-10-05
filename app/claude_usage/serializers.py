from rest_framework import serializers
from .models import Project, Session, UsageSnapshot


class UsageSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageSnapshot
        fields = [
            "id",
            "project",
            "session",
            "input_tokens",
            "output_tokens",
            "cache_creation_tokens",
            "cache_read_tokens",
            "total_tokens",
            "cost_usd",
            "model",
            "timestamp",
            "request_id",
            "message_id",
        ]
        read_only_fields = ["id"]


class SessionSerializer(serializers.ModelSerializer):
    usage_snapshots = UsageSnapshotSerializer(many=True, read_only=True)

    class Meta:
        model = Session
        fields = [
            "id",
            "session_id",
            "project",
            "message_count",
            "total_tokens",
            "total_input_tokens",
            "total_output_tokens",
            "total_cache_creation_tokens",
            "total_cache_read_tokens",
            "total_cost",
            "created_at",
            "updated_at",
            "usage_snapshots",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectSerializer(serializers.ModelSerializer):
    sessions = SessionSerializer(many=True, read_only=True)
    total_tokens = serializers.ReadOnlyField()
    total_sessions = serializers.ReadOnlyField()
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "path",
            "created_at",
            "updated_at",
            "total_tokens",
            "total_sessions",
            "total_cost",
            "sessions",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectListSerializer(serializers.ModelSerializer):
    total_tokens = serializers.ReadOnlyField()
    total_sessions = serializers.ReadOnlyField()
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "path",
            "created_at",
            "updated_at",
            "total_tokens",
            "total_sessions",
            "total_cost",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UsageStatsSerializer(serializers.Serializer):
    total_tokens = serializers.IntegerField()
    total_input_tokens = serializers.IntegerField()
    total_output_tokens = serializers.IntegerField()
    total_cache_creation_tokens = serializers.IntegerField()
    total_cache_read_tokens = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    projects = serializers.IntegerField()
    projects_data = serializers.ListField(child=serializers.DictField())

    # Rate limit fields
    current_window_tokens = serializers.IntegerField(required=False)
    current_window_start = serializers.CharField(required=False, allow_null=True)
    next_reset_at = serializers.CharField(required=False, allow_null=True)
    time_until_reset_seconds = serializers.IntegerField(required=False, allow_null=True)
    time_until_reset_human = serializers.CharField(required=False, allow_null=True)
    is_within_active_window = serializers.BooleanField(required=False)
    window_details = serializers.DictField(required=False)
