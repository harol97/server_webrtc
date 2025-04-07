from dataclasses import dataclass
from typing import Literal

from fastapi import WebSocket

Mode = Literal["sender", "receiver"]


@dataclass
class WebSocketClient:
    websocket: WebSocket
    user_id: str
    mode: Mode

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, WebSocketClient):
            return False
        return self.user_id == value.user_id


class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocketClient] = []

    async def connect(self, websocket_client: WebSocketClient):
        await websocket_client.websocket.accept()
        self.active_connections.append(websocket_client)

    async def get_receiver_client(self, user_id: str) -> WebSocketClient | None:
        try:
            client = filter(
                lambda client: client.user_id == user_id and client.mode == "receiver",
                self.active_connections,
            )
            return next(client)
        except:
            return None

    def disconnect(self, websocket_client: WebSocketClient):
        self.active_connections.remove(websocket_client)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.websocket.send_text(message)
