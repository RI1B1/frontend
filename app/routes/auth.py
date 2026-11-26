from pathlib import Path

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.api_client import (
    api_apply_driver,
    api_get_application,
    api_login,
    api_me,
)

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)

EMAIL_DOMAIN = "@mail.ugm.ac.id"
COOKIE_NAME = "access_token"

# Halaman utama tiap role. TANYAKAN URL sebenarnya ke Raifan (Customer),
# Tegar Danu (Driver), dan Wulan (Admin), lalu sesuaikan di sini.
ROLE_HOME = {"CUSTOMER": "/customer", "DRIVER": "/driver", "ADMIN": "/admin"}


# ---------- Fungsi bantu (boleh dipakai teman lewat import) ----------

def get_user(request: Request):
    """Data user yang sedang login, atau None kalau belum login / token habis."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        r = api_me(token)
    except httpx.RequestError:
        return None
    if r.status_code != 200:
        return None
    data = r.json()
    return data.get("user", data)


def cek_akses(request: Request, role: str):
    """Penjaga halaman. Hasilnya (user, None) kalau boleh masuk,
    atau (user, response) kalau harus dialihkan / ditolak."""
    user = get_user(request)
    if user is None:
        return None, RedirectResponse("/login", status_code=303)
    if user["role"] != role:
        return user, templates.TemplateResponse(
            request, "auth/akses_ditolak.html", {"user": user}, status_code=403
        )
    return user, None


def get_application(request: Request):
    """Pengajuan Driver milik user (dict), atau None kalau belum pernah mengajukan."""
    token = request.cookies.get(COOKIE_NAME)
    try:
        r = api_get_application(token)
    except httpx.RequestError:
        return None
    if r.status_code != 200:
        return None
    return r.json().get("application")


# ---------- Halaman utama ----------
# Kalau Alif/Adam sudah membuat route "/", HAPUS fungsi home ini.

@router.get("/")
def home(request: Request):
    user = get_user(request)
    if user:
        return RedirectResponse(ROLE_HOME.get(user["role"], "/login"), status_code=303)
    return RedirectResponse("/login", status_code=303)


# ---------- Login dan logout ----------

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html", {})


@router.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()

    def tampil_error(pesan: str, kode: int):
        return templates.TemplateResponse(
            request, "auth/login.html", {"error": pesan, "email": email}, status_code=kode
        )

    # Validasi dasar di tampilan. Validasi yang sah tetap di Backend.
    if not email.endswith(EMAIL_DOMAIN):
        return tampil_error(f"Email harus berakhiran {EMAIL_DOMAIN}", 400)

    try:
        resp = api_login(email, password)
    except httpx.RequestError:
        return tampil_error("Server belum bisa dihubungi. Coba lagi sebentar lagi.", 503)

    if resp.status_code == 200:
        data = resp.json()
        r = RedirectResponse(ROLE_HOME.get(data["user"]["role"], "/login"), status_code=303)
        r.set_cookie(
            COOKIE_NAME,
            data["access_token"],
            httponly=True,
            samesite="lax",
            max_age=data["expires_in"],
        )
        return r

    if resp.status_code == 401:
        return tampil_error("Email atau password salah.", 401)
    return tampil_error("Data yang kamu isi belum valid.", 400)


@router.post("/logout")
def logout():
    r = RedirectResponse("/login", status_code=303)
    r.delete_cookie(COOKIE_NAME)
    return r


# ---------- Pengajuan Driver (milik Customer) ----------
# Alamatnya sengaja /driver-application supaya tidak bentrok dengan folder URL
# /customer milik Raifan. Minta Raifan menaruh tombol "Jadi Driver" ke alamat ini.

@router.get("/driver-application", response_class=HTMLResponse)
def driver_application_page(request: Request):
    user, tolak = cek_akses(request, "CUSTOMER")
    if tolak:
        return tolak
    return templates.TemplateResponse(
        request,
        "auth/driver_application.html",
        {"user": user, "application": get_application(request)},
    )


@router.post("/driver-application", response_class=HTMLResponse)
def driver_application_submit(
    request: Request,
    vehicle_type: str = Form(...),
    vehicle_description: str = Form(""),
):
    user, tolak = cek_akses(request, "CUSTOMER")
    if tolak:
        return tolak

    def tampil_error(pesan: str, kode: int):
        return templates.TemplateResponse(
            request,
            "auth/driver_application.html",
            {
                "user": user,
                "application": get_application(request),
                "error": pesan,
                "vehicle_description": vehicle_description,
            },
            status_code=kode,
        )

    try:
        resp = api_apply_driver(
            request.cookies.get(COOKIE_NAME), vehicle_type, vehicle_description.strip()
        )
    except httpx.RequestError:
        return tampil_error("Server belum bisa dihubungi. Coba lagi sebentar lagi.", 503)

    if resp.status_code == 201:
        return RedirectResponse("/driver-application", status_code=303)
    if resp.status_code == 401:
        return RedirectResponse("/login", status_code=303)
    if resp.status_code == 409:
        return tampil_error("Kamu sudah punya pengajuan yang masih aktif.", 409)
    if resp.status_code == 403:
        return tampil_error("Akunmu belum memenuhi syarat untuk mengajukan Driver.", 403)
    return tampil_error("Data pengajuan belum valid. Periksa lagi isianmu.", 422)
