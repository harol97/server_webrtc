from fastapi.responses import HTMLResponse

from .dtos import OfferBody, OfferResponse
from .web_rtc import create_session


async def index():
    return HTMLResponse(open("web/index.html", "r").read())


async def offer(body: OfferBody):
    session = await create_session(body.sdp, body.session_type, body.user_id)
    return OfferResponse(sdp=session.sdp, session_type=session.type)
