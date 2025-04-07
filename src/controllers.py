import json

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from redis import Redis

from .dtos import OfferBody, OfferResponse
from .event_types import Event, EventBox, EventDirection
from .web_rtc import create_session
from .websocket_manager import Mode, WebSocketClient, WebSocketManager

websocket_manager = WebSocketManager()


async def index():
    return HTMLResponse(open("web/index.html", "r").read())


async def offer(body: OfferBody):
    session = await create_session(body.sdp, body.session_type, body.user_id)
    return OfferResponse(sdp=session.sdp, session_type=session.type)


async def websocket_ids(websocket: WebSocket, user_id: str, mode: Mode):
    client = WebSocketClient(websocket, user_id, mode)
    await websocket_manager.connect(client)
    try:
        while True:
            data = await websocket.receive_text()
            data_as_json = json.loads(data)
            event = data_as_json.get("name")
            destinatary_user = data_as_json.get("user")  # user Id to send data
            event_objt = Event.model_validate({"name": event, "user": destinatary_user})
            client_to_send = await websocket_manager.get_receiver_client(
                destinatary_user
            )
            if not client_to_send:
                continue
            if event_objt.name == "direction":
                data_to_send = EventDirection.model_validate(data_as_json).model_dump(
                    by_alias=True
                )
            else:
                eventbox = EventBox.model_validate(data_as_json)
                data_to_send = eventbox.model_dump(by_alias=True)
                data_to_send["ids"] = []
                with Redis() as redis_obj:
                    for track_id in eventbox.ids:
                        if data_from_redis := redis_obj.get(
                            f"{destinatary_user}:{track_id}"
                        ):
                            data_to_send["ids"].append(
                                json.loads(await data_from_redis)
                            )

            await websocket_manager.send_personal_message(
                json.dumps(data_to_send), client_to_send.websocket
            )
    except WebSocketDisconnect:
        websocket_manager.disconnect(client)
