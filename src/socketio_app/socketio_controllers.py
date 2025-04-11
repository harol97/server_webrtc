from typing import cast

from engineio.payload import Payload
from redis import Redis
from socketio import AsyncServer

from .event_types import EventBox, EventDirection
from .setting import setting

Payload.max_decode_packets = setting.max_payload

socketio_server = AsyncServer(async_mode="asgi", cors_allowed_origins=setting.origins)


@socketio_server.event
async def on_join(sid, username):
    await socketio_server.enter_room(sid, username)


@socketio_server.event
async def on_direction(sid, data):
    direction = EventDirection(**data)
    await socketio_server.emit(
        "on_direction",
        direction.value.model_dump(by_alias=True),
        room=direction.user_id,
        skip_sid=sid,
    )


@socketio_server.event
async def on_box(sid, data):
    event_box = EventBox(**data)
    with Redis() as redis_obj:
        keys = [f"{event_box.user_id}:{track_id}" for track_id in event_box.track_ids]
        data_from_redis = cast(list, redis_obj.mget(keys))
        data_to_send = [item for item in data_from_redis if item]
        await socketio_server.emit(
            "on_track", data_to_send, room=event_box.user_id, skip_sid=sid
        )
