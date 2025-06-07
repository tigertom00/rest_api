from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserEmail, UserPhone

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'phone', 'display_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'city', 'country', 'dark_mode', 'two_factor_enabled')
    search_fields = ('email', 'display_name', 'phone', 'username', 'clerk_id')
    ordering = ('email',)

    readonly_fields = ('clerk_updated_at',)
    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        ('Personal info', {'fields': (
            'username', 'display_name', 'date_of_birth', 'address', 'city', 'country',
            'website', 'profile_picture', 'clerk_profile_image_url'
        )}),
        ('Clerk Info', {'fields': (
            'clerk_id', 'has_image', 'two_factor_enabled',
        )}),
        ('Preferences', {'fields': ('dark_mode',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

# Optionally register related models for inline editing
@admin.register(UserEmail)
class UserEmailAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'is_primary', 'is_verified')
    search_fields = ('email',)

@admin.register(UserPhone)
class UserPhoneAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_nr', 'is_primary', 'is_verified')
    search_fields = ('phone_nr',)