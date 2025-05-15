from asyncio import Task, sleep
from typing import cast

from engineio.payload import Payload
from redis.asyncio import Redis
from socketio import AsyncServer

from .event_types import EventBox, EventDirection
from .setting import setting

Payload.max_decode_packets = setting.max_payload

socketio_server = AsyncServer(async_mode="asgi", cors_allowed_origins=setting.origins)

# TODO It must be improve if use workers > 1
tasks: dict[str, Task] = {}


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
    user_task = tasks.get(event_box.user_id)
    if user_task:
        user_task.cancel()

    tasks[event_box.user_id] = socketio_server.start_background_task(
        read_redis, sid, event_box
    )


async def read_redis(sid: str, event_box: EventBox):
    async with Redis() as redis_obj:
        number_of_empties_results = 0
        while True:
            await sleep(setting.delta_time)
            keys = [
                f"{event_box.user_id}:{track_id}" for track_id in event_box.track_ids
            ]
            data_from_redis = cast(list, await redis_obj.mget(keys))
            data_to_send = [item for item in data_from_redis if item]
            if not data_to_send:
                if number_of_empties_results > 5:
                    continue
                else:
                    number_of_empties_results += 1
            if data_to_send:
                number_of_empties_results = 0
            await socketio_server.emit(
                "on_track", data_to_send, room=event_box.user_id, skip_sid=sid
            )
