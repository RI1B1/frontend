from fastapi import APIRouter, Query, Request

from app.config import get_settings
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