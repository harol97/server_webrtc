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
