from django.contrib import admin
from .models import Leverandorer, Matriell, Jobber, JobbMatriell, JobberImage, JobberFile, Timeliste


@admin.register(Leverandorer)
class LeverandorerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "manufacturer_code", "website_url", "created_at", "updated_at")
    search_fields = ("name", "manufacturer_code")
    list_filter = ("manufacturer_code",)


@admin.register(Matriell)
class MatriellAdmin(admin.ModelAdmin):
    list_display = (
        "id", "el_nr", "tittel", "leverandor", "category", "approved",
        "discontinued", "in_stock", "created_at", "updated_at"
    )
    search_fields = (
        "el_nr", "tittel", "ean_number", "article_number",
        "norwegian_description", "english_description", "etim_class"
    )
    list_filter = (
        "leverandor", "category", "approved", "discontinued", "in_stock"
    )
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Core Information", {
            "fields": ("el_nr", "tittel", "info", "leverandor")
        }),
        ("Product Details", {
            "fields": (
                "ean_number", "article_number", "category", "etim_class",
                "approved", "discontinued", "in_stock"
            )
        }),
        ("Descriptions", {
            "fields": ("norwegian_description", "english_description")
        }),
        ("Technical Specifications", {
            "fields": ("height", "width", "depth", "weight"),
            "classes": ("collapse",)
        }),
        ("Documents & Media", {
            "fields": ("datasheet_url", "image_url"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        })
    )


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
