from django.db import models
from django.utils import timezone


class DockerHost(models.Model):
    name = models.CharField(max_length=100, unique=True)
    hostname = models.CharField(max_length=255)
    is_local = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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