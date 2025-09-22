from django.db import models
from django.utils import timezone


class DockerHost(models.Model):
    name = models.CharField(max_length=100, unique=True)
    hostname = models.CharField(max_length=255)
    is_local = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # System specifications
    cpu_cores = models.IntegerField(null=True, blank=True)
    cpu_model = models.CharField(max_length=255, blank=True)
    total_memory = models.BigIntegerField(null=True, blank=True)  # bytes
    architecture = models.CharField(max_length=50, blank=True)
    os_name = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=100, blank=True)
    kernel_version = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.name} ({self.hostname})"

    class Meta:
        ordering = ['name']


class DockerContainer(models.Model):
    CONTAINER_STATES = [
        ('created', 'Created'),
        ('restarting', 'Restarting'),
        ('running', 'Running'),
        ('removing', 'Removing'),
        ('paused', 'Paused'),
        ('exited', 'Exited'),
        ('dead', 'Dead'),
    ]

    host = models.ForeignKey(DockerHost, on_delete=models.CASCADE, related_name='containers')
    container_id = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    image = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=CONTAINER_STATES)
    state = models.JSONField(default=dict)
    ports = models.JSONField(default=list)
    labels = models.JSONField(default=dict)
    networks = models.JSONField(default=dict)
    mounts = models.JSONField(default=list)
    created_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['host', 'container_id']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} on {self.host.name}"

    @property
    def is_running(self):
        return self.status == 'running'


class ContainerStats(models.Model):
    container = models.ForeignKey(DockerContainer, on_delete=models.CASCADE, related_name='stats')
    cpu_percent = models.FloatField(null=True, blank=True)
    memory_usage = models.BigIntegerField(null=True, blank=True)
    memory_limit = models.BigIntegerField(null=True, blank=True)
    memory_percent = models.FloatField(null=True, blank=True)
    network_rx = models.BigIntegerField(null=True, blank=True)
    network_tx = models.BigIntegerField(null=True, blank=True)
    block_read = models.BigIntegerField(null=True, blank=True)
    block_write = models.BigIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['container', '-timestamp']),
        ]

    def __str__(self):
        return f"Stats for {self.container.name} at {self.timestamp}"


class SystemStats(models.Model):
    host = models.ForeignKey(DockerHost, on_delete=models.CASCADE, related_name='system_stats')

    # CPU metrics
    cpu_percent = models.FloatField(null=True, blank=True)
    cpu_count = models.IntegerField(null=True, blank=True)
    load_avg_1m = models.FloatField(null=True, blank=True)
    load_avg_5m = models.FloatField(null=True, blank=True)
    load_avg_15m = models.FloatField(null=True, blank=True)

    # Memory metrics (in bytes)
    memory_total = models.BigIntegerField(null=True, blank=True)
    memory_available = models.BigIntegerField(null=True, blank=True)
    memory_used = models.BigIntegerField(null=True, blank=True)
    memory_free = models.BigIntegerField(null=True, blank=True)
    memory_percent = models.FloatField(null=True, blank=True)

    # Swap metrics (in bytes)
    swap_total = models.BigIntegerField(null=True, blank=True)
    swap_used = models.BigIntegerField(null=True, blank=True)
    swap_free = models.BigIntegerField(null=True, blank=True)
    swap_percent = models.FloatField(null=True, blank=True)

    # Disk metrics (in bytes)
    disk_total = models.BigIntegerField(null=True, blank=True)
    disk_used = models.BigIntegerField(null=True, blank=True)
    disk_free = models.BigIntegerField(null=True, blank=True)
    disk_percent = models.FloatField(null=True, blank=True)

    # Network metrics (in bytes)
    network_bytes_sent = models.BigIntegerField(null=True, blank=True)
    network_bytes_recv = models.BigIntegerField(null=True, blank=True)
    network_packets_sent = models.BigIntegerField(null=True, blank=True)
    network_packets_recv = models.BigIntegerField(null=True, blank=True)

    # Disk I/O metrics (in bytes)
    disk_read_bytes = models.BigIntegerField(null=True, blank=True)
    disk_write_bytes = models.BigIntegerField(null=True, blank=True)
    disk_read_count = models.BigIntegerField(null=True, blank=True)
    disk_write_count = models.BigIntegerField(null=True, blank=True)

    # System info
    boot_time = models.DateTimeField(null=True, blank=True)
    process_count = models.IntegerField(null=True, blank=True)

    # Temperature (in Celsius)
    cpu_temperature = models.FloatField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['host', '-timestamp']),
        ]

    def __str__(self):
        return f"System stats for {self.host.name} at {self.timestamp}"


class ProcessStats(models.Model):
    host = models.ForeignKey(DockerHost, on_delete=models.CASCADE, related_name='process_stats')
    pid = models.IntegerField()
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=100, blank=True)
    cpu_percent = models.FloatField(null=True, blank=True)
    memory_percent = models.FloatField(null=True, blank=True)
    memory_rss = models.BigIntegerField(null=True, blank=True)  # bytes
    memory_vms = models.BigIntegerField(null=True, blank=True)  # bytes
    status = models.CharField(max_length=20, blank=True)
    create_time = models.DateTimeField(null=True, blank=True)
    cmdline = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp', '-cpu_percent']
        indexes = [
            models.Index(fields=['host', '-timestamp']),
            models.Index(fields=['host', '-cpu_percent']),
        ]

    def __str__(self):
        return f"Process {self.name} ({self.pid}) on {self.host.name}"