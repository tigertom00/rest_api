from django.urls import re_path

from restAPI.consumers import TaskConsumer
from app.chat.consumers import ChatConsumer, DirectMessageConsumer

websocket_urlpatterns = [
    re_path(r"ws/tasks/$", TaskConsumer.as_asgi()),
    re_path(r"ws/project/(?P<project_id>\w+)/$", TaskConsumer.as_asgi()),
    re_path(r"ws/user/(?P<user_id>\w+)/$", TaskConsumer.as_asgi()),
    # Chat endpoints
    re_path(r"ws/chat/(?P<room_id>[\w-]+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/direct/(?P<user_id>[\w-]+)/$", DirectMessageConsumer.as_asgi()),
]
