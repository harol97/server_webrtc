from fastapi.responses import HTMLResponse

from src.utils.yolov_tracker.tracker_manager import Tracker

from .dtos import OfferBody, OfferResponse
from .setting import SettingDepends
from .web_rtc import create_session


async def index():
    return HTMLResponse(open("web/index.html", "r").read())


async def offer(body: OfferBody, setting: SettingDepends):
    tracker = Tracker(setting.conf, setting.iou, setting.model_name, setting.classes)
    session = await create_session(body.sdp, body.session_type, body.user_id, tracker)
    return OfferResponse(sdp=session.sdp, session_type=session.type)
