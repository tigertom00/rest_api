from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'completed', 'user_id', 'created_at')
    search_fields = ('title', 'user_id__email')
    list_filter = ('completed', 'created_at')