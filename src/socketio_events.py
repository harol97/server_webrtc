import json
from typing import cast

from redis import Redis
from socketio import AsyncServer

from src.event_types import EventBox, EventDirection

from .setting import setting

socketio_server = AsyncServer(cors_allowed_origins=setting.origins, async_mode="asgi")


@socketio_server.event
async def join_room(sid: str, data: dict):
    await socketio_server.enter_room(sid, data["user"])


@socketio_server.event
async def boxes(sid: str, data: dict):
    obj = EventBox.model_validate(data)
    boxes_to_send = []
    with Redis() as redis:
        for track_id in obj.track_ids:
            if data_from_redis := redis.get(f"{obj.user_id}:{track_id}"):
                boxes_to_send.append(json.loads(cast(bytes, data_from_redis)))

    await socketio_server.emit("boxes", boxes_to_send, room=obj.user_id, skip_sid=sid)


@socketio_server.event
async def direction(sid: str, data: dict):
    obj = EventDirection.model_validate(data)
    await socketio_server.emit("direction", obj.value, room=obj.user_id, skip_sid=sid)
