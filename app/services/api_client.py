import os

import httpx

# Alamat Backend. Ganti sesuai info dari tim (atau set lewat environment variable).
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8001") + "/api/v1"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# === Auth ===

def api_login(email: str, password: str):
    """POST /api/v1/auth/login"""
    return httpx.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )


def api_me(token: str):
    """GET /api/v1/auth/me"""
    return httpx.get(f"{BACKEND_URL}/auth/me", headers=_headers(token), timeout=10)

def api_register(name: str, email: str, password: str):
    """Kirim data pendaftaran ke Backend."""
    return httpx.post(
        f"{BACKEND_URL}/auth/register",
        json={"name": name, "email": email, "password": password},
        timeout=10,
    )

# === Pengajuan Driver ===

def api_get_application(token: str):
    """GET /api/v1/driver/application. Status 404 = belum pernah mengajukan."""
    return httpx.get(
        f"{BACKEND_URL}/driver/application", headers=_headers(token), timeout=10
    )


def api_apply_driver(token: str, vehicle_type: str, vehicle_description: str):
    """POST /api/v1/driver/applications. User ID ditentukan Backend dari token."""
    body = {"vehicle_type": vehicle_type}
    if vehicle_description:
        body["vehicle_description"] = vehicle_description
    return httpx.post(
        f"{BACKEND_URL}/driver/applications",
        json=body,
        headers=_headers(token),
        timeout=10,
    )