from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    @property
    def total_tokens(self):
        return sum(session.total_tokens for session in self.sessions.all())

    @property
    def total_sessions(self):
        return self.sessions.count()

    @property
    def total_cost(self):
        return float(sum(session.total_cost for session in self.sessions.all()))


class Session(models.Model):
    session_id = models.CharField(max_length=100)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="sessions"
    )
    message_count = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    total_input_tokens = models.IntegerField(default=0)
    total_output_tokens = models.IntegerField(default=0)
    total_cache_creation_tokens = models.IntegerField(default=0)
    total_cache_read_tokens = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["session_id", "project"]

    def __str__(self):
        return f"{self.project.name} - {self.session_id}"


class UsageSnapshot(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="usage_snapshots"
    )
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="usage_snapshots"
    )
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_creation_tokens = models.IntegerField(default=0)
    cache_read_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6)
    model = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    request_id = models.CharField(max_length=100, blank=True)
    message_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["model"]),
            models.Index(fields=["project", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.model} - {self.total_tokens} tokens"
