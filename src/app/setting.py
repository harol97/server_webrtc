from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    model_config = SettingsConfigDict(enable_decoding=False)
    origins: list[str]
    model_name: str = "best.pt"
    conf: float
    iou: float

    @field_validator("origins", mode="before")
    @classmethod
    def decode_origins(cls, v: str) -> list[str]:
        return v.split(",")


@lru_cache
def get_settings():
    return Setting()  # type: ignore


SettingDepends = Annotated[Setting, Depends(get_settings)]


setting = Setting()  # type: ignore
