from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    model_config = SettingsConfigDict(enable_decoding=False)
    origins: list[str]
    max_payload: int

    @field_validator("origins", mode="before")
    @classmethod
    def decode_origins(cls, v: str) -> list[str]:
        return v.split(",")


setting = Setting()  # type: ignore
