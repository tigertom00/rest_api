from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserEmail, UserPhone, ChatSession, UserDevice
from rest_framework.authtoken.models import Token

Token._meta.verbose_name = "API Token"
Token._meta.verbose_name_plural = "API Tokens"
admin.site.register(Token)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "phone", "display_name", "is_staff", "is_active")
    list_filter = (
        "is_staff",
        "is_active",
        "city",
        "country",
        "theme",
        "two_factor_enabled",
    )
    search_fields = ("email", "display_name", "phone", "username", "clerk_user_id")
    ordering = ("email",)

    readonly_fields = ("clerk_updated_at",)
    fieldsets = (
        (None, {"fields": ("email", "phone", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "username",
                    "display_name",
                    "date_of_birth",
                    "address",
                    "city",
                    "country",
                    "website",
                    "language",
                    "profile_picture",
                    "clerk_profile_image_url",
                )
            },
        ),
        (
            "Clerk Info",
            {
                "fields": (
                    "clerk_user_id",
                    "has_image",
                    "two_factor_enabled",
                )
            },
        ),
        ("Preferences", {"fields": ("theme",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )


# Optionally register related models for inline editing
@admin.register(UserEmail)
class UserEmailAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "is_primary", "is_verified")
    search_fields = ("email",)


@admin.register(UserPhone)
class UserPhoneAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_nr", "is_primary", "is_verified")
    search_fields = ("phone_nr",)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "session_type",
        "is_active",
        "is_bot_session",
        "last_ping",
        "created_at",
    )
    list_filter = ("session_type", "is_active", "is_bot_session", "created_at")
    search_fields = (
        "user__email",
        "n8n_conversation_id",
        "device_id",
        "websocket_channel",
    )
    readonly_fields = ("id", "created_at", "last_ping")
    raw_id_fields = ("user",)


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "device_name",
        "device_type",
        "os_version",
        "app_version",
        "is_active",
        "last_active",
        "created_at",
    )
    list_filter = ("device_type", "is_active", "created_at", "last_active")
    search_fields = (
        "user__email",
        "device_name",
        "device_id",
        "ip_address",
        "push_token",
    )
    readonly_fields = ("id", "created_at", "updated_at", "last_active")
    raw_id_fields = ("user",)
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("id", "user", "is_active")}),
        (
            "Device Information",
            {
                "fields": (
                    "device_type",
                    "device_name",
                    "device_id",
                    "os_version",
                    "app_version",
                    "user_agent",
                )
            },
        ),
        (
            "Push Notifications",
            {"fields": ("push_token",)},
        ),
        (
            "Security & Tracking",
            {"fields": ("ip_address", "last_active")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    actions = ["revoke_selected_devices", "activate_selected_devices"]

    @admin.action(description="Revoke selected devices")
    def revoke_selected_devices(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Successfully revoked {count} device(s).")

    @admin.action(description="Activate selected devices")
    def activate_selected_devices(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {count} device(s).")
