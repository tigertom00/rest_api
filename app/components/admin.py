from django.contrib import admin
from .models import Llmproviders, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name_en", "name_no")
    search_fields = ("name_en", "name_no")


@admin.register(Llmproviders)
class LlmprovidersAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "url", "pricing", "pricing_nb", "created_at", "updated_at")
    list_filter = ("pricing", "pricing_nb", "created_at")
    search_fields = ("name", "description", "description_nb")
    filter_horizontal = ("tags",)
