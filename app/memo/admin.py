from django import forms
from django.contrib import admin

from .models import (
    ActiveTimerSession,
    ElektriskKategori,
    Jobber,
    JobberFile,
    JobberImage,
    JobberTask,
    JobbMatriell,
    Leverandorer,
    Matriell,
    Timeliste,
)


class ElektriskKategoriForm(forms.ModelForm):
    class Meta:
        model = ElektriskKategori
        fields = ["blokknummer", "kategori", "beskrivelse", "slug", "etim_gruppe"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make slug field read-only in the form
        if "slug" in self.fields:
            self.fields["slug"].widget.attrs["readonly"] = True


@admin.register(ElektriskKategori)
class ElektriskKategoriAdmin(admin.ModelAdmin):
    form = ElektriskKategoriForm
    list_display = (
        "blokknummer",
        "kategori",
        "etim_gruppe",
        "created_at",
        "updated_at",
    )
    search_fields = ("blokknummer", "kategori", "beskrivelse", "etim_gruppe")
    list_filter = ("blokknummer", "etim_gruppe")
    readonly_fields = ("slug", "created_at", "updated_at")

    fieldsets = (
        (
            "Category Information",
            {"fields": ("blokknummer", "kategori", "beskrivelse", "slug")},
        ),
        ("ETIM Classification", {"fields": ("etim_gruppe",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Leverandorer)
class LeverandorerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "telefon", "poststed", "created_at", "updated_at")
    search_fields = ("name", "telefon", "epost", "addresse")
    list_filter = ("poststed",)

    fieldsets = (
        ("Company Information", {"fields": ("name", "telefon", "epost")}),
        ("Address", {"fields": ("addresse", "poststed", "postnummer")}),
        ("Web", {"fields": ("hjemmeside",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Matriell)
class MatriellAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "el_nr",
        "tittel",
        "leverandor",
        "kategori",
        "varemerke",
        "approved",
        "discontinued",
        "in_stock",
        "favorites",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "el_nr",
        "tittel",
        "varemerke",
        "varenummer",
        "gtin_number",
        "varebetegnelse",
        "teknisk_beskrivelse",
    )
    list_filter = (
        "leverandor",
        "kategori",
        "varemerke",
        "approved",
        "discontinued",
        "in_stock",
        "favorites",
    )
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Core Information",
            {"fields": ("el_nr", "tittel", "leverandor", "kategori", "varemerke")},
        ),
        (
            "Product Details",
            {
                "fields": (
                    "varenummer",
                    "gtin_number",
                    "info",
                    "approved",
                    "discontinued",
                    "in_stock",
                    "favorites",
                )
            },
        ),
        ("Descriptions", {"fields": ("varebetegnelse", "teknisk_beskrivelse")}),
        (
            "Dimensions",
            {"fields": ("hoyde", "bredde", "lengde", "vekt"), "classes": ("collapse",)},
        ),
        (
            "Documents & Media",
            {
                "fields": (
                    "bilder",
                    "produktblad",
                    "produkt_url",
                    "fdv",
                    "cpr_sertifikat",
                    "miljoinformasjon",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
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


@admin.register(JobberTask)
class JobberTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "jobb",
        "title",
        "completed",
        "completed_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("completed", "jobb", "created_at")
    search_fields = ("title", "notes", "jobb__tittel")
    readonly_fields = ("completed_at", "created_at", "updated_at")

    fieldsets = (
        ("Job Information", {"fields": ("jobb",)}),
        ("Task Details", {"fields": ("title", "notes", "image")}),
        (
            "Status",
            {"fields": ("completed", "completed_at")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Timeliste)
class TimelisteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "jobb", "dato", "timer", "created_at", "updated_at")
    list_filter = ("user", "jobb", "dato", "timer")


@admin.register(ActiveTimerSession)
class ActiveTimerSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "jobb", "start_time", "last_ping", "elapsed_time")
    list_filter = ("user", "jobb", "start_time")
    search_fields = ("user__username", "jobb__tittel", "jobb__ordre_nr")
    readonly_fields = ("start_time", "last_ping", "elapsed_time")

    def elapsed_time(self, obj):
        """Display elapsed time in human-readable format."""
        seconds = obj.elapsed_seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs}s"

    elapsed_time.short_description = "Elapsed Time"
