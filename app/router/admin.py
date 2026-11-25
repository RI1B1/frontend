from fastapi import APIRouter, Request

from app.config import get_settings
from app.templating import templates

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/", name="admin_dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={"app_name": get_settings().app_name},
    )