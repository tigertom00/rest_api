from django.contrib import admin
from . import models

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Optionally, customize the fields shown in admin:
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': (
            'display_name', 'date_of_birth', 'address', 'city', 'country',
            'website', 'phone', 'profile_picture', 'dark_mode'
        )}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': (
            'display_name', 'date_of_birth', 'address', 'city', 'country',
            'website', 'phone', 'profile_picture', 'dark_mode'
        )}),
    )
