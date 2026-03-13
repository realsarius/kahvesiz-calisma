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
# Stack'i başlat (api + db + redis + nginx)
docker compose up -d --build

# İlk kurulumda migration uygula
docker compose run --rm api python -m alembic upgrade head

# Health check
curl -fsS http://127.0.0.1/api/v1/health

# Loglar
docker compose logs -f api

# Kapat
docker compose down
```

Not: Eski `flask/tailwind/webpack` container'ları daha önce çalıştıysa `docker compose down --remove-orphans` kullanabilirsiniz.

### 1.2 Lokal (Docker'sız) FastAPI çalıştırma

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

- `api`: FastAPI (internal `:8000`)
- `db`: PostgreSQL 16 (internal `:5432`)
- `redis`: Redis 7 (internal `:6379`)
- `nginx`: Reverse proxy (external `:80`)

Compose tanımı: [docker-compose.yaml](docker-compose.yaml)

## 3. API Yüzeyi (v1)

Base path: `/api/v1`

### Health

- `GET /health`

### Auth

- `POST /auth/register`
- `POST /auth/magic-link`
- `POST /auth/verify`
- `POST /auth/logout`

### Cafes

- `GET /cafes`
  - Query: `cursor`, `limit`, `neighborhood`, `wifi`, `noise_level`
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

# Docker
docker compose run --rm api python -m alembic upgrade head
```

## 5. Ortam Değişkenleri

Örnek değerler:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/kahvesiz
REDIS_URL=redis://redis:6379/0

SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=15
SESSION_EXPIRE_DAYS=30
MAGIC_LINK_EXPIRE_MINUTES=15

RESEND_API_KEY=
RESEND_FROM_EMAIL=noreply@kahvesizcalisma.com

ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173
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

