from django.contrib import admin
from .models import Leverandorer, Matriell, Jobber, JobbMatriell, JobberImage, JobberFile, Timeliste


@admin.register(Leverandorer)
class LeverandorerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "url", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Matriell)
class MatriellAdmin(admin.ModelAdmin):
    list_display = ("id", "el_nr", "tittel", "leverandor", "created_at", "updated_at")
    search_fields = ("tittel",)
    list_filter = ("leverandor",)


@admin.register(Jobber)
class JobberAdmin(admin.ModelAdmin):
    list_display = ("ordre_nr", "tittel", "ferdig", "created_at", "updated_at")
    search_fields = ("tittel", "adresse", "telefon_nr")
    list_filter = ("ferdig",)


@admin.register(JobbMatriell)
class JobbMatriellAdmin(admin.ModelAdmin):
    list_display = ("id", "jobb", "matriell", "antall", "transf", "created_at")
    list_filter = ("jobb", "matriell", "antall")


@admin.register(JobberImage)
class JobberImageAdmin(admin.ModelAdmin):
    list_display = ("id", "jobb", "image", "created_at")
    list_filter = ("jobb",)


@admin.register(JobberFile)
class JobberFileAdmin(admin.ModelAdmin):
    list_display = ("id", "jobb", "file", "created_at")
    list_filter = ("jobb",)


@admin.register(Timeliste)
class TimelisteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "jobb", "dato", "timer", "created_at", "updated_at")
    list_filter = ("user", "jobb", "dato", "timer")
