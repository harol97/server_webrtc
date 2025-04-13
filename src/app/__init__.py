from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .controllers import index, offer
from .setting import setting

main_app = FastAPI()
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=setting.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
main_app.add_api_route("/offer", offer, methods=["POST"])
main_app.add_api_route("/", index, methods=["GET"])
