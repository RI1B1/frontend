from fastapi import APIRouter, Request

from app.config import get_settings
from app.templating import templates

router = APIRouter(prefix="/driver", tags=["driver"])


@router.get("/", name="driver_dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="driver/dashboard.html",
        context={"app_name": get_settings().app_name},
    )