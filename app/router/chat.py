from fastapi import APIRouter, Request

from app.config import get_settings
from app.templating import templates

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/", name="chat_home")
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="chat/index.html",
        context={"app_name": get_settings().app_name},
    )