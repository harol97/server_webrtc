from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.app import main_app
from src.socketio_app import socketio_app

app = FastAPI()
app.mount("/api", main_app, name="api")
app.mount("/static", StaticFiles(directory="statics"), name="static")
app.mount("/socket.io", socketio_app, name="socketio")
