"""
ASGI config for srv project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from srv.routing import websocket_urlpatterns
from restAPI.socketio_server import socketio_app

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "srv.settings")

django_asgi_app = get_asgi_application()


# Combine Django Channels and Socket.IO
class CombinedASGIApp:
    def __init__(self, django_app, socketio_app):
        self.django_app = django_app
        self.socketio_app = socketio_app

    async def __call__(self, scope, receive, send):
        # Route Socket.IO requests to Socket.IO app
        if scope["type"] == "http" and scope["path"].startswith("/api/socketio"):
            await self.socketio_app(scope, receive, send)
        # Route WebSocket upgrade requests for Socket.IO
        elif scope["type"] == "websocket" and scope["path"].startswith("/api/socketio"):
            await self.socketio_app(scope, receive, send)
        # Route everything else through Django Channels
        else:
            if scope["type"] == "websocket":
                await AuthMiddlewareStack(URLRouter(websocket_urlpatterns))(
                    scope, receive, send
                )
            else:
                await self.django_app(scope, receive, send)


application = CombinedASGIApp(django_asgi_app, socketio_app)
