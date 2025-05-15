from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    model_config = SettingsConfigDict(enable_decoding=False)
    origins: list[str]
    model_name: str
    conf: float
    iou: float
    classes: list[int] | None = None

    @field_validator("classes", mode="before")
    @classmethod
    def decode_classes(cls, v: str | None) -> list[str] | None:
        if isinstance(v, str):
            return v.split(",")

    @field_validator("origins", mode="before")
    @classmethod
    def decode_origins(cls, v: str) -> list[str]:
        return v.split(",")


@lru_cache
def get_settings():
    return Setting()  # type: ignore


SettingDepends = Annotated[Setting, Depends(get_settings)]


setting = Setting()  # type: ignore
