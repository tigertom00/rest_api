from django.contrib import admin
from .models import Todo

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'completed', 'created_at', 'created_by')
    search_fields = ('title', 'created_by__email')
    list_filter = ('completed',)
