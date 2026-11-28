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
    api_register, 
)

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)

EMAIL_DOMAIN = "@mail.ugm.ac.id"
COOKIE_NAME = "access_token"

# Halaman utama tiap role. Sesuaikan dengan URL dashboard dari Raifan, Tegar Danu, Wulan.
ROLE_HOME = {"CUSTOMER": "/customer", "DRIVER": "/driver", "ADMIN": "/admin"}


def alamat(request: Request, nama_route: str) -> str:
    """Alamat halaman berdasarkan NAMA fungsi route-nya.
    Aman walau router didaftarkan dengan prefix (misal /auth) di main.py."""
    return str(request.app.url_path_for(nama_route))


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


def cek_akses(request: Request, role):
    """role boleh satu role ("CUSTOMER") atau beberapa (("CUSTOMER", "DRIVER"))."""
    boleh = (role,) if isinstance(role, str) else tuple(role)
    user = get_user(request)
    if user is None:
        return None, RedirectResponse(alamat(request, "login_page"), status_code=303)
    if user["role"] not in boleh:
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
        return RedirectResponse(
            ROLE_HOME.get(user["role"], alamat(request, "login_page")), status_code=303
        )
    return RedirectResponse(alamat(request, "login_page"), status_code=303)


# ---------- Login dan logout ----------

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, registered: str = ""):
    context = {}
    if registered == "1":
        context["success"] = "Akun berhasil dibuat. Silakan masuk."
    return templates.TemplateResponse(request, "auth/login.html", context)

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
        tujuan = ROLE_HOME.get(data["user"]["role"], alamat(request, "login_page"))
        r = RedirectResponse(tujuan, status_code=303)
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
def logout(request: Request):
    r = RedirectResponse(alamat(request, "login_page"), status_code=303)
    r.delete_cookie(COOKIE_NAME)
    return r

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html", {})


@router.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    name = name.strip()
    email = email.strip().lower()

    def tampil_error(pesan: str, kode: int):
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"error": pesan, "name": name, "email": email},
            status_code=kode,
        )

    if not name:
        return tampil_error("Nama wajib diisi.", 400)
    if not email.endswith(EMAIL_DOMAIN):
        return tampil_error(f"Email harus berakhiran {EMAIL_DOMAIN}", 400)

    try:
        resp = api_register(name, email, password)
    except httpx.RequestError:
        return tampil_error("Server belum bisa dihubungi. Coba lagi sebentar lagi.", 503)

    if resp.status_code == 201:
        alamat_login = str(request.app.url_path_for("login_page"))
        return RedirectResponse(alamat_login + "?registered=1", status_code=303)
    if resp.status_code == 409:
        return tampil_error("Email ini sudah terdaftar. Silakan masuk.", 409)
    return tampil_error("Data belum valid. Periksa nama, email, dan password.", 400)
# ---------- Pengajuan Driver ----------

@router.get("/driver-application", response_class=HTMLResponse)
def driver_application_page(request: Request):
    user, tolak = cek_akses(request, ("CUSTOMER", "DRIVER"))
    if tolak:
        return tolak
    return templates.TemplateResponse(
        request,
        "auth/driver_application.html",
        {
            "user": user,
            "application": get_application(request),
            "driver_home": ROLE_HOME["DRIVER"],
        },
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
                "driver_home": ROLE_HOME["DRIVER"],
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
        return RedirectResponse(alamat(request, "driver_application_page"), status_code=303)
    if resp.status_code == 401:
        return RedirectResponse(alamat(request, "login_page"), status_code=303)
    if resp.status_code == 409:
        return tampil_error("Kamu sudah punya pengajuan yang masih aktif.", 409)
    if resp.status_code == 403:
        return tampil_error("Akunmu belum memenuhi syarat untuk mengajukan Driver.", 403)
    return tampil_error("Data pengajuan belum valid. Periksa lagi isianmu.", 422)