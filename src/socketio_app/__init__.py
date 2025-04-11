from socketio import ASGIApp

from .socketio_controllers import socketio_server

socketio_app = ASGIApp(socketio_server)
