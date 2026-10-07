from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DataSource = Literal["demo", "webfleet"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[3] / ".env", ".env"), extra="ignore"
    )

    database_url: str = Field(
        default="postgresql+psycopg://fleetflow:fleetflow@localhost:5432/fleetflow", repr=False
    )
    data_source: DataSource = "demo"
    cors_origins: list[str] = ["http://localhost:5173"]
    webfleet_account: SecretStr | None = None
    webfleet_username: SecretStr | None = None
    webfleet_password: SecretStr | None = None
    webfleet_api_key: SecretStr | None = None
    webfleet_timeout_seconds: float = Field(default=15, ge=1, le=60)


@lru_cache
def get_settings() -> Settings:
    return Settings()
