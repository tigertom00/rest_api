from django.contrib import admin
from .models import DockerHost, DockerContainer, ContainerStats


@admin.register(DockerHost)
class DockerHostAdmin(admin.ModelAdmin):
    list_display = ['name', 'hostname', 'is_local', 'is_active', 'last_seen', 'container_count']
    list_filter = ['is_local', 'is_active']
    search_fields = ['name', 'hostname']
    readonly_fields = ['created_at', 'last_seen']

    def container_count(self, obj):
        return obj.containers.count()
    container_count.short_description = 'Containers'


@admin.register(DockerContainer)
class DockerContainerAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'status', 'image', 'is_running', 'created_at', 'updated_at']
    list_filter = ['status', 'host', 'created_at']
    search_fields = ['name', 'container_id', 'image']
    readonly_fields = ['container_id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('host', 'container_id', 'name', 'image', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'finished_at', 'updated_at')
        }),
        ('Configuration', {
            'fields': ('state', 'ports', 'labels', 'networks', 'mounts'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContainerStats)
class ContainerStatsAdmin(admin.ModelAdmin):
    list_display = ['container', 'cpu_percent', 'memory_percent', 'timestamp']
    list_filter = ['timestamp', 'container__host']
    readonly_fields = ['timestamp']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('container', 'container__host')