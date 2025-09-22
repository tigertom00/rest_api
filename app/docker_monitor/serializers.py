from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from typing import Dict, Any, Optional, List
from .models import DockerHost, DockerContainer, ContainerStats, SystemStats, ProcessStats


class DockerHostSerializer(serializers.ModelSerializer):
    container_count = serializers.SerializerMethodField()
    running_containers = serializers.SerializerMethodField()
    latest_system_stats = serializers.SerializerMethodField()

    class Meta:
        model = DockerHost
        fields = [
            'id', 'name', 'hostname', 'is_local', 'is_active',
            'last_seen', 'created_at', 'container_count', 'running_containers',
            'cpu_cores', 'cpu_model', 'total_memory', 'architecture',
            'os_name', 'os_version', 'kernel_version', 'latest_system_stats'
        ]

    @extend_schema_field(serializers.IntegerField)
    def get_container_count(self, obj) -> int:
        return obj.containers.count()

    @extend_schema_field(serializers.IntegerField)
    def get_running_containers(self, obj) -> int:
        return obj.containers.filter(status='running').count()

    @extend_schema_field(serializers.DictField)
    def get_latest_system_stats(self, obj) -> Optional[Dict[str, Any]]:
        latest_stat = obj.system_stats.first()
        if latest_stat:
            return SystemStatsSerializer(latest_stat).data
        return None


class ContainerStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContainerStats
        fields = [
            'id', 'cpu_percent', 'memory_usage', 'memory_limit',
            'memory_percent', 'network_rx', 'network_tx',
            'block_read', 'block_write', 'timestamp'
        ]


class DockerContainerSerializer(serializers.ModelSerializer):
    host_name = serializers.CharField(source='host.name', read_only=True)
    latest_stats = serializers.SerializerMethodField()
    uptime = serializers.SerializerMethodField()

    class Meta:
        model = DockerContainer
        fields = [
            'id', 'container_id', 'name', 'image', 'status',
            'host_name', 'ports', 'labels', 'networks',
            'created_at', 'started_at', 'finished_at',
            'updated_at', 'is_running', 'latest_stats', 'uptime'
        ]

    @extend_schema_field(serializers.DictField)
    def get_latest_stats(self, obj) -> Optional[Dict[str, Any]]:
        latest_stat = obj.stats.first()
        if latest_stat:
            return ContainerStatsSerializer(latest_stat).data
        return None

    @extend_schema_field(serializers.DictField)
    def get_uptime(self, obj) -> Optional[Dict[str, Any]]:
        if obj.started_at and obj.status == 'running':
            from django.utils import timezone
            uptime = timezone.now() - obj.started_at
            return {
                'days': uptime.days,
                'seconds': uptime.seconds,
                'total_seconds': uptime.total_seconds()
            }
        return None


class DockerContainerDetailSerializer(DockerContainerSerializer):
    stats_history = serializers.SerializerMethodField()

    class Meta(DockerContainerSerializer.Meta):
        fields = DockerContainerSerializer.Meta.fields + ['stats_history', 'state', 'mounts']

    @extend_schema_field(serializers.ListField)
    def get_stats_history(self, obj) -> List[Dict[str, Any]]:
        # Get last 24 hours of stats
        from django.utils import timezone
        from datetime import timedelta

        last_24h = timezone.now() - timedelta(hours=24)
        stats = obj.stats.filter(timestamp__gte=last_24h).order_by('-timestamp')[:288]  # 5-minute intervals
        return ContainerStatsSerializer(stats, many=True).data


class SystemStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemStats
        fields = [
            'id', 'cpu_percent', 'cpu_count', 'load_avg_1m', 'load_avg_5m', 'load_avg_15m',
            'memory_total', 'memory_available', 'memory_used', 'memory_free', 'memory_percent',
            'swap_total', 'swap_used', 'swap_free', 'swap_percent',
            'disk_total', 'disk_used', 'disk_free', 'disk_percent',
            'network_bytes_sent', 'network_bytes_recv', 'network_packets_sent', 'network_packets_recv',
            'disk_read_bytes', 'disk_write_bytes', 'disk_read_count', 'disk_write_count',
            'boot_time', 'process_count', 'cpu_temperature', 'timestamp'
        ]


class ProcessStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessStats
        fields = [
            'id', 'pid', 'name', 'username', 'cpu_percent', 'memory_percent',
            'memory_rss', 'memory_vms', 'status', 'create_time', 'cmdline', 'timestamp'
        ]


class DockerHostDetailSerializer(DockerHostSerializer):
    system_stats_history = serializers.SerializerMethodField()
    top_processes = serializers.SerializerMethodField()

    class Meta(DockerHostSerializer.Meta):
        fields = DockerHostSerializer.Meta.fields + ['system_stats_history', 'top_processes']

    @extend_schema_field(serializers.ListField)
    def get_system_stats_history(self, obj) -> List[Dict[str, Any]]:
        # Get last 24 hours of system stats
        from django.utils import timezone
        from datetime import timedelta

        last_24h = timezone.now() - timedelta(hours=24)
        stats = obj.system_stats.filter(timestamp__gte=last_24h).order_by('-timestamp')[:288]  # 5-minute intervals
        return SystemStatsSerializer(stats, many=True).data

    @extend_schema_field(serializers.ListField)
    def get_top_processes(self, obj) -> List[Dict[str, Any]]:
        # Get latest process stats
        latest_processes = obj.process_stats.order_by('-timestamp', '-cpu_percent')[:10]
        return ProcessStatsSerializer(latest_processes, many=True).data


class SystemDashboardSerializer(serializers.Serializer):
    """Serializer for system dashboard data combining multiple metrics"""
    host = DockerHostSerializer(read_only=True)
    current_system_stats = SystemStatsSerializer(read_only=True)
    containers_summary = serializers.DictField(read_only=True)
    top_processes = ProcessStatsSerializer(many=True, read_only=True)

    # Time-series data for charts
    cpu_history = serializers.ListField(read_only=True)
    memory_history = serializers.ListField(read_only=True)
    disk_history = serializers.ListField(read_only=True)
    network_history = serializers.ListField(read_only=True)