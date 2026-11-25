# AnterinDong Frontend

Starter frontend server-side rendered dengan Python, FastAPI, Jinja2, HTML, dan CSS.
Struktur mengikuti Panduan Proyek dan Tim v1.3. Endpoint, payload, dan logika bisnis
Backend sengaja belum dibuat; gunakan API Contract yang sudah disepakati.

## Struktur

```text
app/
├── main.py                 # Inisialisasi FastAPI dan halaman awal
├── config.py               # Konfigurasi bersama dari environment/.env
├── router/                 # Satu router per area fitur
│   ├── auth.py
│   ├── customer.py
│   ├── driver.py
│   ├── chat.py
│   └── admin.py
├── services/
│   └── api_client.py       # Client bersama untuk integrasi Backend
├── templates/
│   ├── base.html
│   └── index.html
│   ├── auth/login.html
│   ├── customer/dashboard.html
│   ├── driver/dashboard.html
│   ├── chat/index.html
│   └── admin/dashboard.html
└── static/
    └── css/style.css
tests/
└── test_app.py
```

Frontend per fitur dikembangkan di `app/templates/<fitur>/` untuk HTML/Jinja2 dan
`app/router/<fitur>.py` untuk URL serta pengolahan data tampilan. Starter tiap fitur
bisa dibuka dari halaman utama. Jinja2 berisi tampilan saja; pengolahan data berada
di Python. Gunakan `app/templates/base.html` dan `app/static/css/style.css` untuk
layout serta styling bersama.

## Menjalankan secara lokal

Gunakan Python 3.11 atau lebih baru.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Buka `http://127.0.0.1:8000`. Dokumentasi OpenAPI tersedia di `/docs`.

## Konfigurasi sebelum dibagikan

Salin `.env.example` menjadi `.env`, lalu ubah nilai yang sesuai. `.env` tidak
masuk Git; bagikan `.env.example` tanpa kredensial.

| Variabel | Fungsi |
| --- | --- |
| `APP_NAME` | Nama aplikasi pada halaman dan dokumentasi API |
| `APP_ENV` | Nama environment, misalnya `development` atau `production` |
| `APP_DEBUG` | Mode debug FastAPI |
| `APP_BACKEND_API_BASE_URL` | URL dasar Backend setelah dikonfirmasi |
| `APP_BACKEND_API_TIMEOUT_SECONDS` | Batas waktu request ke Backend |

Client Backend akan meminta `APP_BACKEND_API_BASE_URL` secara eksplisit saat
digunakan. Jangan menambah endpoint atau payload sampai kontraknya tersedia.

## Pembagian kerja fitur

| Area | Modul router | Ruang lingkup awal |
| --- | --- | --- |
| Auth | `app/router/auth.py` | Login; registrasi jika disepakati |
| Customer | `app/router/customer.py` | Dashboard, antar-jemput, jasa titip, detail, riwayat |
| Driver | `app/router/driver.py` | Dashboard, pengajuan, ketersediaan |
| Chat | `app/router/chat.py` | Tampilan chat sesuai kontrak |
| Admin | `app/router/admin.py` | Dashboard dan katalog lokasi |
| Shared | `app/config.py`, `app/services/`, `app/templates/base.html`, `app/static/` | Konfigurasi, integrasi, layout, styling |

| Starter halaman | URL lokal |
| --- | --- |
| Auth | `/auth/login` |
| Customer | `/customer/` |
| Driver | `/driver/` |
| Chat | `/chat/` |
| Admin | `/admin/` |

Isi tabel ini sebelum membagikan starter ke tim:

| Area | PIC | Anggota | Reviewer |
| --- | --- | --- | --- |
| Auth | Isi nama | Isi nama | Isi nama |
| Customer | Isi nama | Isi nama | Isi nama |
| Driver | Isi nama | Isi nama | Isi nama |
| Chat | Isi nama | Isi nama | Isi nama |
| Admin | Isi nama | Isi nama | Isi nama |
| Shared dan integrasi | Isi nama | Isi nama | Isi nama |

Untuk tim 10+ orang, bagi tugas menjadi issue kecil di dalam area tersebut;
hindari dua orang mengubah file bersama yang sama tanpa koordinasi. Koordinator
Frontend dan Tech Lead menyetujui perubahan pada konfigurasi bersama, layout dasar,
serta integrasi API.

## Aturan integrasi

- Ikuti API Contract dan koordinasikan perubahan kontrak dengan tim Backend.
- Frontend tidak mengakses database atau menduplikasi business logic Backend.
- Pertahankan form HTML semantik, label yang jelas, pesan validasi, dan layout
  responsif.
- Gunakan template inheritance dari `base.html`; jangan menaruh business logic di
  template.
- JavaScript bersifat opsional dan minimal. Tidak ada React, Vite, TypeScript,
  Tailwind, atau peta interaktif pada starter MVP.
- Buka pull request kecil per fitur, minta review, dan sertakan cara uji.

## Pengujian

```powershell
python -m unittest discover -s tests
```