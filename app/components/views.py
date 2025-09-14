from rest_framework import viewsets, permissions
from .models import Llmproviders, Tag
from .serializers import LlmprovidersSerializer, TagSerializer


class ReadOnlyOrAuthenticated(permissions.BasePermission):
    """
    Allow GET/HEAD/OPTIONS requests for anyone,
    require authentication for POST/PUT/PATCH/DELETE.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [ReadOnlyOrAuthenticated]


class LlmprovidersViewSet(viewsets.ModelViewSet):
    queryset = Llmproviders.objects.all().order_by("-created_at")
    serializer_class = LlmprovidersSerializer
    permission_classes = [ReadOnlyOrAuthenticated]
