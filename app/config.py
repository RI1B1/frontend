from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="AnterinDong", validation_alias="APP_NAME")
    environment: str = Field(default="development", validation_alias="APP_ENV")
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    backend_api_base_url: AnyHttpUrl | None = Field(
        default=None,
        validation_alias="APP_BACKEND_API_BASE_URL",
    )
    backend_api_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        validation_alias="APP_BACKEND_API_TIMEOUT_SECONDS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
