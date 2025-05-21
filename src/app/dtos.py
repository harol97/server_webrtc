from typing import Annotated

from pydantic import BaseModel, Field


class OfferBody(BaseModel):
    sdp: str
    session_type: Annotated[str, Field(alias="type")]
    user_id: Annotated[str, Field(alias="userId")]

    model_config = {"populate_by_name": True}


class OfferResponse(BaseModel):
    sdp: str
    session_type: Annotated[str, Field(alias="type")]

    model_config = {"populate_by_name": True}


class FeedbackForm(BaseModel):
    usability: str
    technical_issues: str
    device: str
    device_other: str = ""
    liked_aspect: str
    aspect_to_improve: str
    future_functionality: str
