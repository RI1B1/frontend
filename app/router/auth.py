from fastapi import APIRouter, Request

from app.config import get_settings
from app.templating import templates

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", name="auth_login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"app_name": get_settings().app_name},
    )