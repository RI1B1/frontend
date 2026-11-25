from fastapi import APIRouter, Request

from app.config import get_settings
from app.templating import templates

router = APIRouter(prefix="/customer", tags=["customer"])


@router.get("/", name="customer_dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="customer/dashboard.html",
        context={"app_name": get_settings().app_name},
    )