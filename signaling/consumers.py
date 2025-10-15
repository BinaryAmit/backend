import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

JWT_SECRET = getattr(settings, "JWT_SECRET", "dev-jwt")

# Simple in-memory membership for development (single-process)
# Maps room_code -> { sid: name }
ROOMS: dict[str, dict[str, str]] = {}

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["code"]
        self.room_group_name = f"room_{self.room_code}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # Notify others that this participant left
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "broadcast", "event": "leave", "sid": self.channel_name},
        )
        # Remove from membership
        room = ROOMS.get(self.room_code)
        if room and self.channel_name in room:
            try:
                del room[self.channel_name]
            except KeyError:
                pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "join":
            token = data.get("token")
            user = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            name = user.get("name", "Guest")
            # Send current peers to the joiner
            room = ROOMS.setdefault(self.room_code, {})
            existing = [
                {"sid": sid, "name": nm}
                for sid, nm in room.items()
                if sid != self.channel_name
            ]
            await self.send(json.dumps({
                "type": "peers",
                "peers": existing,
            }))

            # Add joiner to room and notify others
            room[self.channel_name] = name
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "broadcast", "event": "join", "sid": self.channel_name, "name": name},
            )

        elif msg_type in ["offer", "answer", "candidate"]:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "relay", "payload": data, "sender": self.channel_name},
            )

    async def broadcast(self, event):
        if event["sid"] == self.channel_name:
            return
        payload = {
            "type": event["event"],
            "sid": event["sid"],
        }
        if "name" in event and event["name"] is not None:
            payload["name"] = event["name"]
        await self.send(json.dumps(payload))

    async def relay(self, event):
        payload = event["payload"]
        sender = event["sender"]
        if payload.get("to") == self.channel_name:
            await self.send(json.dumps({
                **payload,
                "sid": sender
            }))
