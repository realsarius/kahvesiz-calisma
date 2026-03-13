# Kahvesiz Çalışma

> Durum (13 Mart 2026): Proje Flask tabanından FastAPI + PostgreSQL + Redis mimarisine geçiştedir.

## İçindekiler

- [1. Hızlı Başlangıç](#1-hızlı-başlangıç)
- [2. Güncel Mimari](#2-güncel-mimari)
- [3. API Yüzeyi (v1)](#3-api-yüzeyi-v1)
- [4. Veritabanı ve Migration](#4-veritabanı-ve-migration)
- [5. Ortam Değişkenleri](#5-ortam-değişkenleri)
- [6. Frontend (SolidJS)](#6-frontend-solidjs)
- [7. Test ve Doğrulama](#7-test-ve-doğrulama)
- [8. Legacy Notları](#8-legacy-notları)

## 1. Hızlı Başlangıç

### 1.1 Docker Compose (önerilen)

```bash
# DEV stack'i başlat (api + legacy + db + redis + frontend + nginx)
docker compose --profile dev up -d --build

# Gerekirse migration'ı manuel tetikle (api-dev zaten açılışta upgrade head çalıştırır)
docker compose --profile dev run --rm api-dev python -m alembic upgrade head

# Health check
curl -fsS http://127.0.0.1/api/v1/health

# Frontend dev server (direkt)
# http://127.0.0.1:5173
# Frontend nginx üstünden
# http://127.0.0.1

# Loglar
docker compose --profile dev logs -f api-dev
docker compose --profile dev logs -f legacy-dev

# Kapat
docker compose --profile dev down
```

### 1.2 Prod (Hetzner) çalıştırma

```bash
# PROD stack'i başlat
docker compose --profile prod up -d --build

# PROD migration uygula
docker compose --profile prod run --rm api-prod python -m alembic upgrade head

# Kapat
docker compose --profile prod down
```

### 1.3 Lokal (Docker'sız) FastAPI çalıştırma

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- API health: `http://127.0.0.1:8000/api/v1/health`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

## 2. Güncel Mimari

### Backend

- Framework: `FastAPI`
- ORM: `SQLAlchemy 2.0` (async)
- Migration: `Alembic`
- Auth: magic-link tabanlı token + session akışı

### Altyapı

- `dev` profili: `api-dev`, `legacy-dev`, `db-dev`, `redis-dev`, `frontend-dev`, `nginx-dev`
- `prod` profili: `api-prod`, `db-prod`, `redis-prod`, `frontend-prod`, `nginx-prod`
- `test` profili: `db-test`, `redis-test`

Compose tanımı: [docker-compose.yaml](docker-compose.yaml)

Dev strangler routing:

- `/api/v1/*` -> `api-dev` (FastAPI)
- `/api/*` -> `legacy-dev` (Flask)
- `/*` -> `frontend-dev` (Vite proxy)
- `frontend-dev` içindeki Vite proxy hedefi: `nginx-dev` (böylece `/api/v1/*` ve `/api/*` ayrımı korunur)

## 3. API Yüzeyi (v1)

Base path: `/api/v1`

### Health

- `GET /health`

### Auth

- `POST /auth/register`
- `POST /auth/magic-link`
- `POST /auth/verify`
- `GET /auth/verify?token=<plain_token>`
- `POST /auth/logout`
- `GET /auth/session`

### Cafes

- `GET /cafes`
  - Query: `cursor`, `limit`, `neighborhood`, `wifi`, `noise_level`, `has_outlet`
  - Cursor tabanlı pagination (`created_at + id`)
- `GET /cafes/{slug}`

## 4. Veritabanı ve Migration

Alembic revision:

- `20260313_0001` (initial schema)

Kapsanan ana tablolar:

- `users`, `auth_tokens`, `user_sessions`
- `neighborhoods`, `cafes`, `cafe_amenities`, `cafe_hours`, `cafe_images`, `cafe_seats`
- `reviews`, `review_votes`, `bookmarks`
- `pii.user_pii` (KVKK ayrımı)

Migration komutları:

```bash
# Lokal
python3 -m alembic upgrade head

# Docker (dev)
docker compose --profile dev run --rm api-dev python -m alembic upgrade head
```

## 5. Ortam Değişkenleri

Örnek değerler:

```env
# DEV
DATABASE_URL_DEV=postgresql+asyncpg://user:pass@db-dev:5432/kahvesiz_dev
REDIS_URL_DEV=redis://redis-dev:6379/0
FRONTEND_URL_DEV=http://localhost:5173
ALLOWED_ORIGINS_DEV=http://localhost:5173,http://localhost
LEGACY_SQLALCHEMY_DATABASE_URI=sqlite:///cafes.db

# PROD
DATABASE_URL_PROD=postgresql+asyncpg://user:pass@db-prod:5432/kahvesiz
REDIS_URL_PROD=redis://redis-prod:6379/0
FRONTEND_URL_PROD=https://kahvesizcalisma.com
ALLOWED_ORIGINS_PROD=https://kahvesizcalisma.com

SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=15
SESSION_EXPIRE_DAYS=30
MAGIC_LINK_EXPIRE_MINUTES=15

RESEND_API_KEY=
RESEND_FROM_EMAIL=noreply@kahvesizcalisma.com

# Opsiyonel port override'ları
FRONTEND_DEV_PORT=5173
NGINX_DEV_PORT=80
NGINX_PROD_PORT=80
```

## 6. Frontend (SolidJS)

Frontend kaynak kodu: `frontend-solid/`

Temel komutlar:

```bash
# Geliştirme
npm --prefix frontend-solid run dev

# Production build
npm --prefix frontend-solid run build
```

Docker ile frontend erişimi:

- `dev` profile: `http://127.0.0.1:5173` (Vite)
- `dev` nginx: `http://127.0.0.1` (proxy)

Yeni veri akışı:

- `CafesPage` -> `/api/v1/cafes` (cursor-based infinite scroll)
- `CafeDetailPage` -> `/api/v1/cafes/:slug`

## 7. Test ve Doğrulama

### Testler

```bash
npm test
```

Mevcut test dosyaları:

- `tests/test_api_hardening.py` (legacy Flask API güvenlik/regresyon)
- `tests/test_frontend_cutover.py` (Solid cutover davranışı)
- `tests/test_fastapi_v1_contract.py` (FastAPI v1 kontrat testleri)

### Sık kullanılan smoke komutları

```bash
curl -fsS http://127.0.0.1/api/v1/health
npm --prefix frontend-solid run build
npm test
```

## 8. Legacy Notları

- Repo içinde Flask tabanlı legacy modüller halen bulunmaktadır (`main.py`, `kahvesiz_app/*`).
- Geçiş tamamlanana kadar legacy testleri ve bazı route/senaryolar korunmaktadır.
- Yeni geliştirme hedefi FastAPI `app/` dizini ve `/api/v1/*` yüzeyidir.

### 8.1 SQLite -> PostgreSQL aktarım scripti

Legacy `instance/cafes.db` verisini yeni PostgreSQL şemasına taşımak için:

```bash
# Dry-run (yazmadan planı gör)
docker compose --profile dev run --rm api-dev \
  python scripts/migrate_sqlite_to_postgres.py --dry-run

# Gerçek aktarım
docker compose --profile dev run --rm api-dev \
  python scripts/migrate_sqlite_to_postgres.py
```

Notlar:
- Script idempotent çalışır; daha önce taşınmış `legacy_cafe_id` satırlarını atlar.
- `DATABASE_URL_DEV` / `DATABASE_URL` otomatik okunur; gerekirse `--pg-url` verilebilir.
