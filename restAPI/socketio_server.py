"""
Socket.IO server configuration for real-time communication
"""

import socketio
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Configure based on your CORS settings
    logger=True,
    engineio_logger=False,
)


@database_sync_to_async
def get_user_from_token(token):
    """Authenticate user from JWT token"""
    try:
        access_token = AccessToken(token)
        user_id = access_token["user_id"]
        from restAPI.models import CustomUser

        return CustomUser.objects.get(id=user_id)
    except Exception as e:
        print(f"Auth error: {e}")
        return None


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    print(f"Client connecting: {sid}")

    # Optional: Authenticate using JWT token from auth
    if auth and "token" in auth:
        user = await get_user_from_token(auth["token"])
        if user:
            await sio.save_session(sid, {"user_id": user.id, "username": user.username})
            print(f"User {user.username} connected: {sid}")
        else:
            print(f"Authentication failed for {sid}")
            return False  # Reject connection

    print(f"Client connected: {sid}")
    return True


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    session = await sio.get_session(sid)
    username = session.get("username", "Unknown") if session else "Unknown"
    print(f"Client disconnected: {sid} (User: {username})")


@sio.event
async def message(sid, data):
    """Handle generic message event"""
    print(f"Message from {sid}: {data}")
    await sio.emit("message", {"data": data, "from": sid})


@sio.event
async def join_room(sid, data):
    """Allow clients to join rooms"""
    room = data.get("room")
    if room:
        sio.enter_room(sid, room)
        await sio.emit("joined", {"room": room}, room=sid)
        print(f"Client {sid} joined room: {room}")


@sio.event
async def leave_room(sid, data):
    """Allow clients to leave rooms"""
    room = data.get("room")
    if room:
        sio.leave_room(sid, room)
        await sio.emit("left", {"room": room}, room=sid)
        print(f"Client {sid} left room: {room}")


# Create ASGI application
socketio_app = socketio.ASGIApp(sio, socketio_path="socketio")
