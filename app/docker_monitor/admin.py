from django.contrib import admin

from .models import (
    ContainerStats,
    DockerContainer,
    DockerHost,
    ProcessStats,
    SystemStats,
)


@admin.register(DockerHost)
class DockerHostAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "hostname",
        "is_local",
        "is_active",
        "last_seen",
        "container_count",
    ]
    list_filter = ["is_local", "is_active"]
    search_fields = ["name", "hostname"]
    readonly_fields = ["created_at", "last_seen"]

    def container_count(self, obj):
        return obj.containers.count()

    container_count.short_description = "Containers"


@admin.register(DockerContainer)
class DockerContainerAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "host",
        "status",
        "image",
        "is_running",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "host", "created_at"]
    search_fields = ["name", "container_id", "image"]
    readonly_fields = ["container_id", "created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("host", "container_id", "name", "image", "status")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "started_at", "finished_at", "updated_at")},
        ),
        (
            "Configuration",
            {
                "fields": ("state", "ports", "labels", "networks", "mounts"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ContainerStats)
class ContainerStatsAdmin(admin.ModelAdmin):
    list_display = ["container", "cpu_percent", "memory_percent", "timestamp"]
    list_filter = ["timestamp", "container__host"]
    readonly_fields = ["timestamp"]

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("container", "container__host")
        )


@admin.register(SystemStats)
class SystemStatsAdmin(admin.ModelAdmin):
    list_display = [
        "host",
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "timestamp",
    ]
    list_filter = ["timestamp", "host"]
    readonly_fields = ["timestamp"]

    fieldsets = (
        ("Basic Information", {"fields": ("host", "timestamp")}),
        (
            "CPU Metrics",
            {
                "fields": (
                    "cpu_percent",
                    "cpu_count",
                    "load_avg_1m",
                    "load_avg_5m",
                    "load_avg_15m",
                    "cpu_temperature",
                )
            },
        ),
        (
            "Memory Metrics",
            {
                "fields": (
                    "memory_total",
                    "memory_available",
                    "memory_used",
                    "memory_free",
                    "memory_percent",
                )
            },
        ),
        (
            "Swap Metrics",
            {"fields": ("swap_total", "swap_used", "swap_free", "swap_percent")},
        ),
        (
            "Disk Metrics",
            {"fields": ("disk_total", "disk_used", "disk_free", "disk_percent")},
        ),
        (
            "Network Metrics",
            {
                "fields": (
                    "network_bytes_sent",
                    "network_bytes_recv",
                    "network_packets_sent",
                    "network_packets_recv",
                )
            },
        ),
        (
            "Disk I/O Metrics",
            {
                "fields": (
                    "disk_read_bytes",
                    "disk_write_bytes",
                    "disk_read_count",
                    "disk_write_count",
                )
            },
        ),
        ("System Info", {"fields": ("boot_time", "process_count")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("host")


@admin.register(ProcessStats)
class ProcessStatsAdmin(admin.ModelAdmin):
    list_display = [
        "host",
        "name",
        "pid",
        "username",
        "cpu_percent",
        "memory_percent",
        "status",
        "timestamp",
    ]
    list_filter = ["timestamp", "host", "status", "username"]
    search_fields = ["name", "pid", "username", "cmdline"]
    readonly_fields = ["timestamp"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("host", "pid", "name", "username", "status", "timestamp")},
        ),
        (
            "Performance Metrics",
            {"fields": ("cpu_percent", "memory_percent", "memory_rss", "memory_vms")},
        ),
        (
            "Process Details",
            {"fields": ("create_time", "cmdline"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("host")
