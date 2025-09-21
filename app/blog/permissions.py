from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import SiteSettings

class IsOwnerOrFeaturedReadOnly(BasePermission):
    """
    Read rules:
      - Unauthenticated users: can ONLY read published posts of the featured author.
      - Authenticated users: can read ONLY their own posts (regardless of status).
    Write rules:
      - Only owners can create/update/delete their own posts.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            if request.user.is_authenticated:
                return obj.author_id == request.user.id
            # unauthenticated: only featured/published objects
            settings_row = SiteSettings.objects.first()
            return (
                obj.status == obj.Status.PUBLISHED
                and settings_row
                and settings_row.featured_author_id == obj.author_id
            )
        # write - allow staff users to edit any post, otherwise only owners
        return request.user.is_authenticated and (
            request.user.is_staff or obj.author_id == request.user.id
        )