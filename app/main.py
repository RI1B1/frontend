from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.router import router
from app.templating import templates

APP_DIR = Path(__file__).resolve().parent
settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.mount(
    "/static",
    StaticFiles(directory=str(APP_DIR / "static")),
    name="static",
)
app.include_router(router)


@app.get("/", include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )
