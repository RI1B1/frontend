import httpx

from app.config import Settings, get_settings


def create_api_client(settings: Settings | None = None) -> httpx.AsyncClient:
    configured_settings = settings or get_settings()
    if configured_settings.backend_api_base_url is None:
        raise RuntimeError(
            "Set APP_BACKEND_API_BASE_URL in .env before calling the backend."
        )

    return httpx.AsyncClient(
        base_url=str(configured_settings.backend_api_base_url),
        timeout=configured_settings.backend_api_timeout_seconds,
    )
