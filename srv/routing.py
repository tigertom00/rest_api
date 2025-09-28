from django.urls import re_path

from restAPI.consumers import TaskConsumer

websocket_urlpatterns = [
    re_path(r"ws/tasks/$", TaskConsumer.as_asgi()),
    re_path(r"ws/project/(?P<project_id>\w+)/$", TaskConsumer.as_asgi()),
    re_path(r"ws/user/(?P<user_id>\w+)/$", TaskConsumer.as_asgi()),
]
