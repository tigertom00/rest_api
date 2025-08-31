# Example Django models structure you'll need:
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ])
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    due_date = models.DateField(null=True, blank=True)
    estimated_time = models.DecimalField(null=True, blank=True, decimal_places=1, max_digits=3)
    completed = models.BooleanField(default=False)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.completed and self.completed_at is None:
            self.completed_at = timezone.now()
        elif not self.completed:
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title