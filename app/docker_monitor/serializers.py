from rest_framework import serializers
from .models import DockerHost, DockerContainer, ContainerStats


class DockerHostSerializer(serializers.ModelSerializer):
    container_count = serializers.SerializerMethodField()
    running_containers = serializers.SerializerMethodField()

    class Meta:
        model = DockerHost
        fields = [
            'id', 'name', 'hostname', 'is_local', 'is_active',
            'last_seen', 'created_at', 'container_count', 'running_containers'
        ]

    def get_container_count(self, obj):
        return obj.containers.count()

    def get_running_containers(self, obj):
        return obj.containers.filter(status='running').count()


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

    def get_latest_stats(self, obj):
        latest_stat = obj.stats.first()
        if latest_stat:
            return ContainerStatsSerializer(latest_stat).data
        return None

    def get_uptime(self, obj):
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

    def get_stats_history(self, obj):
        # Get last 24 hours of stats
        from django.utils import timezone
        from datetime import timedelta

        last_24h = timezone.now() - timedelta(hours=24)
        stats = obj.stats.filter(timestamp__gte=last_24h).order_by('-timestamp')[:288]  # 5-minute intervals
        return ContainerStatsSerializer(stats, many=True).data