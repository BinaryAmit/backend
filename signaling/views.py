import os
import time
import jwt
import secrets
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Room

JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt")


def _make_token(payload: dict, ttl=3600):
    """Generate JWT token for the participant."""
    payload = {**payload, "exp": int(time.time()) + ttl}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@api_view(["POST"])
def create_room(request):
    """Create a new room."""
    code = secrets.token_hex(3)  # Example: 'a1b2c3'
    room = Room.objects.create(code=code, title=request.data.get("title", ""))
    return Response({"code": room.code})


@api_view(["POST"])
def join_room(request, code):
    """Join an existing active room."""
    room = get_object_or_404(Room, code=code, is_active=True)
    display_name = request.data.get("display_name", "Guest")
    token = _make_token({"room": code, "name": display_name})

    # ICE servers for WebRTC
    iceServers = [
        {"urls": ["stun:stun.l.google.com:19302"]},
    ]
    # Optional TURN from environment
    turn_urls = os.getenv("TURN_URLS")  # e.g. turn:host:3478,turns:host:5349
    turn_username = os.getenv("TURN_USERNAME")
    turn_credential = os.getenv("TURN_CREDENTIAL")
    if turn_urls:
        for url in [u.strip() for u in turn_urls.split(",") if u.strip()]:
            entry = {"urls": url}
            if turn_username is not None and turn_credential is not None:
                entry["username"] = turn_username
                entry["credential"] = turn_credential
            iceServers.append(entry)

    # Choose WebSocket scheme based on environment
    if request.is_secure() or "vercel.app" in request.get_host():
        ws_scheme = "wss"
    else:
        ws_scheme = "ws"

    host = request.get_host()


    return Response({
        "roomCode": room.code,
        "jwt": token,
        "ws_url": f"{ws_scheme}://{host}/ws/rooms/{room.code}/",
        "iceServers": iceServers,
    })


@api_view(["POST"])
def end_room(request, code):
    """End an existing room."""
    room = get_object_or_404(Room, code=code)
    room.is_active = False
    room.save(update_fields=["is_active"])
    return Response({"ended": True})
