from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ChatRoomViewSet,
    MessageViewSet,
    ChatSearchViewSet,
    ChatSessionViewSet,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r"rooms", ChatRoomViewSet, basename="chat-rooms")
router.register(r"search", ChatSearchViewSet, basename="chat-search")
router.register(r"sessions", ChatSessionViewSet, basename="chat-sessions")

# Messages are nested under rooms
router.register(
    r"rooms/(?P<room_pk>[^/.]+)/messages", MessageViewSet, basename="room-messages"
)

app_name = "chat"

urlpatterns = [
    path("", include(router.urls)),
]
