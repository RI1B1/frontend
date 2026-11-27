from typing import Any

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.config import get_settings
from app.services.api_client import create_api_client
from app.templating import templates

router = APIRouter(prefix="/driver", tags=["driver"])


def get_error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except (httpx.ResponseNotRead, ValueError):
        return f"Permintaan gagal (HTTP {response.status_code})."

    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, dict):
        return str(detail.get("message") or detail.get("code") or "Permintaan gagal.")
    if isinstance(detail, str) and detail:
        return detail
    return f"Permintaan gagal (HTTP {response.status_code})."


def build_api_headers(request: Request) -> dict[str, str] | None:
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    return {"Authorization": f"Bearer {access_token}"}


@router.get("/", name="driver_dashboard")
@router.get("/dashboard", include_in_schema=False)
async def dashboard_page(request: Request):
    settings = get_settings()
    availability: str | None = None
    orders: list[dict[str, Any]] = []
    error_message: str | None = None
    headers = build_api_headers(request)

    if settings.backend_api_base_url is None:
        error_message = "Integrasi Backend belum dikonfigurasi."
    elif headers is None:
        error_message = "Silakan login sebagai Driver untuk melihat dashboard."
    else:
        try:
            async with create_api_client(settings) as api_client:
                availability_response = await api_client.get(
                    "/api/v1/driver/availability",
                    headers=headers,
                )
                if availability_response.status_code == 200:
                    availability = availability_response.json().get("availability")
                elif availability_response.status_code in (401, 403):
                    error_message = get_error_detail(availability_response)

                if availability == "ACTIVE":
                    available_response = await api_client.get(
                        "/api/v1/orders/available",
                        headers=headers,
                    )
                    if available_response.status_code == 200:
                        orders = available_response.json().get("orders", [])
                    elif available_response.status_code not in (401, 403):
                        error_message = get_error_detail(available_response)
                    else:
                        error_message = get_error_detail(available_response)
        except (httpx.HTTPError, ValidationError, ValueError):
            error_message = "Tidak dapat terhubung ke Backend saat ini."

    return templates.TemplateResponse(
        request=request,
        name="driver/dashboard.html",
        context={
            "app_name": settings.app_name,
            "availability": availability,
            "orders": orders,
            "error_message": error_message,
            "success_message": request.query_params.get("success"),
        },
    )


@router.post("/availability", name="driver_update_availability")
async def update_availability(
    request: Request,
    availability: str = Form(...),
):
    if availability not in ("ACTIVE", "INACTIVE"):
        return RedirectResponse(
            url="/driver/dashboard?error=Nilai+ketersediaan+tidak+valid",
            status_code=303,
        )

    settings = get_settings()
    headers = build_api_headers(request)
    if settings.backend_api_base_url is None:
        return RedirectResponse(
            url="/driver/dashboard?error=Integrasi+Backend+belum+dikonfigurasi",
            status_code=303,
        )
    if headers is None:
        return RedirectResponse(
            url="/auth/login?error=Silakan+login+terlebih+dahulu",
            status_code=303,
        )

    try:
        async with create_api_client(settings) as api_client:
            response = await api_client.patch(
                "/api/v1/driver/availability",
                headers=headers,
                json={"availability": availability},
            )
    except httpx.HTTPError:
        return RedirectResponse(
            url="/driver/dashboard?error=Tidak+dapat+terhubung+ke+Backend",
            status_code=303,
        )

    if response.status_code == 200:
        return RedirectResponse(
            url="/driver/dashboard?success=Status+ketersediaan+berhasil+diperbarui",
            status_code=303,
        )
    return RedirectResponse(
        url=f"/driver/dashboard?error={get_error_detail(response).replace(' ', '+')}",
        status_code=303,
    )


@router.post("/orders/{order_id}/accept", name="driver_accept_order")
async def accept_order(request: Request, order_id: int):
    settings = get_settings()
    headers = build_api_headers(request)
    if settings.backend_api_base_url is None:
        return RedirectResponse(
            url="/driver/dashboard?error=Integrasi+Backend+belum+dikonfigurasi",
            status_code=303,
        )
    if headers is None:
        return RedirectResponse(
            url="/auth/login?error=Silakan+login+terlebih+dahulu",
            status_code=303,
        )

    try:
        async with create_api_client(settings) as api_client:
            response = await api_client.post(
                f"/api/v1/orders/{order_id}/accept",
                headers=headers,
            )
    except httpx.HTTPError:
        return RedirectResponse(
            url="/driver/dashboard?error=Tidak+dapat+terhubung+ke+Backend",
            status_code=303,
        )

    if response.status_code == 200:
        return RedirectResponse(
            url="/driver/dashboard?success=Order+berhasil+diterima",
            status_code=303,
        )
    return RedirectResponse(
        url=f"/driver/dashboard?error={get_error_detail(response).replace(' ', '+')}",
        status_code=303,
    )