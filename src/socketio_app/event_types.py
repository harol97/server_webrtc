from pydantic import BaseModel, Field


class Event(BaseModel):
    user_id: str = Field(alias="user")

    model_config = {"populate_by_name": True}


class Direction(BaseModel):
    objetivo: str
    input1: str
    input2: str
    stepSize: str
    direction: str


class EventDirection(Event):
    value: Direction


class EventBox(Event):
    track_ids: list[int] = Field(alias="trackIds")
