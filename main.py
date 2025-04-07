from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from socketio.asgi import ASGIApp

from src.controllers import index, offer
from src.setting import setting
from src.socketio_events import socketio_server

socketio_app = ASGIApp(socketio_server, socketio_path="/socket")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=setting.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="statics"))
app.mount("/socket", socketio_app)

app.add_api_route("/offer", offer, methods=["POST"])
app.add_api_route("/", index, methods=["GET"])
