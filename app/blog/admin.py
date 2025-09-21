# apps/blog/admin.py
from django.contrib import admin
from .models import SiteSettings, Tag, BlogPost, PostImage, PostAudio, PostYouTube

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("featured_author",)
    # Optional: limit to a singleton
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists() or super().has_add_permission(request)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    readonly_fields = ("slug",)

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0

class PostAudioInline(admin.TabularInline):
    model = PostAudio
    extra = 0

class PostYouTubeInline(admin.TabularInline):
    model = PostYouTube
    extra = 0

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "published_at", "created_at")
    list_filter = ("status", "author", "tags")
    search_fields = ("title", "excerpt", "body_markdown")
    inlines = [PostImageInline, PostAudioInline, PostYouTubeInline]
    autocomplete_fields = ("author", "tags")
    readonly_fields = ("slug", "published_at", "created_at", "updated_at")
