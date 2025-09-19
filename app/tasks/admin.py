from django.contrib import admin
from .models import Category, Task, Project, TaskImage, ProjectImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "name_nb")
    search_fields = ("name", "name_nb")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "priority",
        "completed",
        "user_id",
        "due_date",
        "created_at",
    )
    list_filter = ("status", "priority", "completed", "created_at")
    search_fields = ("title", "title_nb", "description", "description_nb")
    autocomplete_fields = ("user_id", "category")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "user_id", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "name_nb", "description", "description_nb")
    autocomplete_fields = ("user_id", "tasks")


@admin.register(TaskImage)
class TaskImageAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "caption", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("task__title", "caption")
    autocomplete_fields = ("task",)


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "caption", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("project__name", "caption")
    autocomplete_fields = ("project",)
