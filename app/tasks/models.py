# Example Django models structure you'll need:
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from restAPI.utils.n8n_translate import send_translation_request
import os

User = get_user_model()

class Category(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    name_nb = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


def task_image_upload_path(instance, filename):
    """Generate upload path for task images"""
    return f'tasks/{instance.task.user_id.id}/images/{filename}'


def project_image_upload_path(instance, filename):
    """Generate upload path for project images"""
    return f'projects/{instance.project.user_id.id}/images/{filename}'


class TaskImage(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=task_image_upload_path)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        # Delete the file when the model instance is deleted
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.task.title}"


class ProjectImage(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=project_image_upload_path)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        # Delete the file when the model instance is deleted
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.project.name}"

class Task(models.Model):
    title = models.CharField(max_length=200)
    title_nb = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True)
    description_nb = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ])
    status_nb = models.CharField(max_length=20, choices=[
        ('å gjøre', 'Å gjøre'),
        ('pågående', 'Pågående'),
        ('fullført', 'Fullført')
    ], default='å gjøre')
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    due_date = models.DateField(null=True, blank=True)
    estimated_time = models.DecimalField(null=True, blank=True, decimal_places=1, max_digits=3)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ManyToManyField(Category, blank=True, related_name='tasks')
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='project_tasks', null=True, blank=True)

    STATUS_TRANSLATION = {
    'todo': 'å gjøre',
    'in_progress': 'pågående',
    'completed': 'fullført'
}

    def save(self, *args, **kwargs):
    # Sync completed with status
        if self.status == "completed":
            self.completed = True
            if self.completed_at is None:
                self.completed_at = timezone.now()
        else:
            self.completed = False
            self.completed_at = None

    # Sync translated status
        self.status_nb = self.__class__.STATUS_TRANSLATION.get(self.status, self.status)
        super(Task, self).save(*args, **kwargs)

    def __str__(self):
        return self.title
    
class Project(models.Model):
    name = models.CharField(max_length=100)
    name_nb = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True)
    description_nb = models.TextField(blank=True, null=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    tasks = models.ManyToManyField(Task, related_name='projects', blank=True)
    status = models.CharField(max_length=20, choices=[
       ('todo', 'To Do'),
       ('in_progress', 'In Progress'),
       ('completed', 'Completed')
    ])
    status_nb = models.CharField(max_length=20, choices=[
        ('å gjøre', 'Å gjøre'),
        ('pågående', 'Pågående'),
        ('fullført', 'Fullført')
    ])
 


    def save(self, *args, **kwargs):
    # Sync completed with status
        if self.status == "completed":
            self.completed = True
            if self.completed_at is None:
                self.completed_at = timezone.now()
        else:
            self.completed = False
            self.completed_at = None



        super(Project, self).save(*args, **kwargs)



    def __str__(self):
        return self.name