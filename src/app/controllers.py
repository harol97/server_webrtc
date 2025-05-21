from typing import Annotated
from fastapi import BackgroundTasks, Depends, Form
from fastapi.responses import HTMLResponse

from src.utils.yolov_tracker.tracker_manager import Tracker
from src.utils.sender_information import Sender

from .dtos import FeedbackForm, OfferBody, OfferResponse
from .setting import SettingDepends
from .web_rtc import create_session


async def index():
    return HTMLResponse(open("web/index.html", "r").read())


async def offer(body: OfferBody, setting: SettingDepends):
    tracker = Tracker(setting.conf, setting.iou, setting.model_name, setting.classes)
    session = await create_session(body.sdp, body.session_type, body.user_id, tracker)
    return OfferResponse(sdp=session.sdp, session_type=session.type)


async def send_feedback(
    sender: Annotated[Sender, Depends()],
    form: Annotated[FeedbackForm, Form()],
    background_tasks: BackgroundTasks,
):
    body_as_dict = form.model_dump()

    message_as_list = ["<html>"]
    message_as_list.append("<body>")
    message_as_list.append("<table>")
    message_as_list.append("<thead>")
    for key in body_as_dict.keys():
        message_as_list.append(f"<th>{key}</th>")
    message_as_list.append("</thead>")
    message_as_list.append("</tbody><tr>")

    for value in body_as_dict.values():
        message_as_list.append(f"<td>{value}</td>")

    message_as_list.append("</tr></tbody>")

    background_tasks.add_task(sender.send, "".join(message_as_list), "OPINION")
    return {}
