from typing import Any

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx

from app.config import get_settings
from app.services.api_client import create_api_client
from app.templating import templates

router = APIRouter(prefix="/customer", tags=["customer"])

SERVICE_TYPE_LABELS = {
    "ANTAR_JEMPUT": "Antar-Jemput",
    "JASA_TITIP": "Jasa Titip",
}

# Data contoh terpisah hanya untuk preview tampilan; bukan data aplikasi aktual.
# Bentuk field mengikuti Master API Reference v1.3.
SAMPLE_PREVIEW_DATA = {
    "customer_name": "Abdul (Contoh)",
    "active_driver_count": 4,
    "orders": [
        {
            "id": 101,
            "service_type": "ANTAR_JEMPUT",
            "status": "OPEN",
        },
        {
            "id": 102,
            "service_type": "JASA_TITIP",
            "status": "ON_THE_WAY",
        },
    ],
}


# ---------------------------------------------------------------------------
# Dashboard Customer (Raifan)
# ---------------------------------------------------------------------------


def format_orders_for_dashboard(raw_orders: list[dict]) -> list[dict]:
    """Memformat daftar order agar sesuai dengan tampilan Dashboard Customer."""
    formatted = []
    for order in raw_orders:
        raw_service = order.get("service_type", "")
        formatted.append(
            {
                "id": order.get("id"),
                "service_type": SERVICE_TYPE_LABELS.get(raw_service, raw_service),
                "status": order.get("status", ""),
            }
        )
    return formatted


def build_customer_dashboard_context(preview: str | None = None) -> dict:
    """Menyiapkan context tampilan Dashboard Customer."""
    is_sample_preview = preview == "contoh"

    if is_sample_preview:
        customer_name = SAMPLE_PREVIEW_DATA["customer_name"]
        active_drivers_count = SAMPLE_PREVIEW_DATA["active_driver_count"]
        orders = format_orders_for_dashboard(SAMPLE_PREVIEW_DATA["orders"])
    else:
        # Belum terintegrasi dengan Auth, Active Driver API, dan Order API.
        customer_name = None
        active_drivers_count = None
        orders = []

    return {
        "app_name": get_settings().app_name,
        "is_sample_preview": is_sample_preview,
        "customer_name": customer_name,
        "active_drivers_count": active_drivers_count,
        "orders": orders,
        # Rute fitur lain belum dibuat oleh PIC terkait; isi URL saat sudah tersedia.
        "services": [
            {
                "name": "Antar-Jemput",
                "description": "Pesan perjalanan antar atau jemput di sekitar area UGM.",
                "url": None,
            },
            {
                "name": "Jasa Titip",
                "description": "Titip ambil atau beli barang di sekitar kampus UGM.",
                "url": None,
            },
        ],
        "history_url": None,
    }


@router.get("/", name="customer_dashboard")
async def dashboard_page(
    request: Request,
    preview: str | None = Query(default=None),
):
    context = build_customer_dashboard_context(preview=preview)
    return templates.TemplateResponse(
        request=request,
        name="customer/dashboard.html",
        context=context,
    )


# ---------------------------------------------------------------------------
# Form Antar-Jemput (Cindy)
# ---------------------------------------------------------------------------


def _get_token(request: Request) -> str | None:
    if "session" in request.scope:
        return request.session.get("access_token")
    return request.cookies.get("access_token")


async def _fetch_locations(token: str | None) -> list[dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with create_api_client() as client:
            resp = await client.get("/api/v1/locations", headers=headers)
    except Exception:
        return []

    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("data"), list):
            return data["data"]
    return []


def _build_description(passenger_count: int, notes: str | None) -> str:
    base = f"Antar-jemput {passenger_count} penumpang."
    if notes and notes.strip():
        return f"{base} Catatan: {notes.strip()}"
    return base


@router.get("/antar-jemput", response_class=HTMLResponse)
async def form_antar_jemput_page(request: Request):
    token = _get_token(request)
    if not token:
        return RedirectResponse(url="/login", status_code=302)

    locations = await _fetch_locations(token)
    return templates.TemplateResponse(
        request=request,
        name="customer/form_antar_jemput.html",
        context={
            "app_name": get_settings().app_name,
            "locations": locations,
            "error_message": None,
            "form_data": {},
        },
    )


@router.post("/antar-jemput", response_class=HTMLResponse)
async def submit_antar_jemput(
    request: Request,
    pickup_location_id: str = Form(...),
    dropoff_location_id: str = Form(...),
    passenger_count: int = Form(1),
    estimated_fare: str = Form(""),
    notes: str = Form(""),
):
    token = _get_token(request)
    if not token:
        return RedirectResponse(url="/login", status_code=302)

    locations = await _fetch_locations(token)
    form_snapshot = {
        "pickup_location_id": pickup_location_id,
        "dropoff_location_id": dropoff_location_id,
        "passenger_count": passenger_count,
        "estimated_fare": estimated_fare,
        "notes": notes,
    }

    error_msg: str | None = None
    parsed_fare: float | None = None

    if not pickup_location_id or not dropoff_location_id:
        error_msg = "Lokasi jemput dan lokasi tujuan wajib diisi."
    elif pickup_location_id == dropoff_location_id:
        error_msg = "Lokasi jemput dan lokasi tujuan tidak boleh sama."
    elif passenger_count < 1:
        error_msg = "Jumlah penumpang minimal 1 orang."
    elif estimated_fare.strip() != "":
        try:
            parsed_fare = float(estimated_fare)
            if parsed_fare < 0:
                error_msg = "Perkiraan biaya tidak boleh negatif."
        except ValueError:
            error_msg = "Format perkiraan biaya tidak valid."

    if error_msg:
        return templates.TemplateResponse(
            request=request,
            name="customer/form_antar_jemput.html",
            context={
                "app_name": get_settings().app_name,
                "locations": locations,
                "error_message": error_msg,
                "form_data": form_snapshot,
            },
            status_code=400,
        )

    payload: dict[str, Any] = {
        "service_type": "ANTAR_JEMPUT",
        "pickup_location_id": pickup_location_id,
        "dropoff_location_id": dropoff_location_id,
        "description": _build_description(passenger_count, notes),
    }
    if parsed_fare is not None:
        payload["estimated_fare"] = parsed_fare

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        async with create_api_client() as client:
            resp = await client.post("/api/v1/orders", json=payload, headers=headers)
    except httpx.RequestError:
        return templates.TemplateResponse(
            request=request,
            name="customer/form_antar_jemput.html",
            context={
                "app_name": get_settings().app_name,
                "locations": locations,
                "error_message": (
                    "Tidak dapat terhubung ke server API. Coba beberapa saat lagi."
                ),
                "form_data": form_snapshot,
            },
            status_code=502,
        )
    except RuntimeError as exc:
        return templates.TemplateResponse(
            request=request,
            name="customer/form_antar_jemput.html",
            context={
                "app_name": get_settings().app_name,
                "locations": locations,
                "error_message": str(exc),
                "form_data": form_snapshot,
            },
            status_code=500,
        )

    if resp.status_code == 401:
        return RedirectResponse(url="/login", status_code=302)

    if resp.status_code == 201:
        body = resp.json() if resp.content else {}
        order_id = body.get("id") or (body.get("data") or {}).get("id")
        target_url = (
            f"/customer/orders/{order_id}" if order_id else "/customer/orders"
        )
        return RedirectResponse(url=target_url, status_code=303)

    detail = "Gagal membuat pesanan antar-jemput."
    try:
        err_json = resp.json()
        if isinstance(err_json, dict) and err_json.get("detail"):
            detail = str(err_json["detail"])
    except Exception:
        pass

    return templates.TemplateResponse(
        request=request,
        name="customer/form_antar_jemput.html",
        context={
            "app_name": get_settings().app_name,
            "locations": locations,
            "error_message": detail,
            "form_data": form_snapshot,
        },
        status_code=resp.status_code if resp.status_code >= 400 else 400,
    )