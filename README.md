# Kahvesiz Çalışma

> Durum: 14 Mart 2026 itibariyle proje, Strangler yaklaşımıyla Flask (legacy) + FastAPI (v1) birlikte çalışacak şekilde ilerliyor.

## İçindekiler

- [0. Hızlı Kurulum](#0-hızlı-kurulum)
- [1. Proje Kapsamı](#1-proje-kapsamı)
- [2. Teknoloji Yığını](#2-teknoloji-yığını)
- [3. Veritabanı Tasarımı](#3-veritabanı-tasarımı)
- [4. API Tasarımı ve Standartlar](#4-api-tasarımı-ve-standartlar)
- [5. Güvenlik ve KVKK](#5-güvenlik-ve-kvkk)
- [6. Test Stratejisi](#6-test-stratejisi)
- [7. Kurulum ve Çalıştırma](#7-kurulum-ve-çalıştırma)
- [8. Frontend (SolidJS)](#8-frontend-solidjs)
- [9. Production Notları](#9-production-notları)
- [10. Lisans](#10-lisans)
- [Ek Dokümanlar](#ek-dokümanlar)

## 0. Hızlı Kurulum

### Docker ile (Önerilen)

```bash
# 1) Ortam değişkenlerini hazırla
cp .env.example .env

# 2) Development stack'i başlat
docker compose --profile dev up -d --build

# 3) Test servislerini (db/redis) başlat
docker compose --profile test up -d --build

# 4) İsteğe bağlı migration
docker compose --profile dev run --rm api-dev python -m alembic upgrade head

# 5) Kapat
docker compose --profile dev --profile test down
```

### Erişim Adresleri (Dev)

- Uygulama (Nginx): <http://localhost>
- SolidJS Vite: <http://localhost:5173>
- FastAPI Swagger: <http://localhost/docs>
- FastAPI Health: <http://localhost/api/v1/health>

---

## 1. Proje Kapsamı

**Kimlik Doğrulama (Magic Link + Session Cookie)**  
`/api/v1/auth/*` altında register, magic-link, verify, session ve logout akışları bulunur. `verify` sonrası HttpOnly `session_token` cookie set edilir.

**Kafe Keşfi ve Detay Deneyimi**  
Cursor bazlı kafe listeleme, filtreleme (`wifi`, `neighborhood`, `noise_level`, `has_outlet`) ve detay sayfasında amenity/saat/görsel/koltuk/yorum birleşik payload üretilir.

**Yorum Sistemi ve Oylama**  
Kullanıcılar kafe yorumu oluşturabilir, silebilir, helpful/unhelpful oylayabilir; listeleme cursor tabanlıdır.

**Hesap Silme ve PII Purge**  
`DELETE /api/v1/users/me` ile kullanıcı soft-delete, PII hard-delete, yorum anonimleştirme ve aktif session invalidation tek servis akışında yönetilir.

**Cookie Rıza Yönetimi**  
SolidJS tarafında banner ile tercih alınır; backend tarafında `PATCH /api/v1/users/me/consent` ile `consent_given_at` ve `consent_version` güncellenir.

**KVKK Odaklı PII Koruma**  
`pii.user_pii` kritik alanları, uygulama katmanında `KVKK_ENCRYPTION_KEY`/`KVKK_HASH_PEPPER` ile korunarak yazılır.

## 2. Teknoloji Yığını

| Kategori | Teknoloji | Kullanım Amacı |
|---|---|---|
| Backend API | FastAPI | Versiyonlu REST API (`/api/v1`) |
| ORM | SQLAlchemy 2.0 (async) | Veri erişimi ve modelleme |
| Migration | Alembic | Şema versiyonlama |
| Veritabanı | PostgreSQL 16 | Ana veri deposu |
| Cache/Infra | Redis 7 | Session/cache altyapısı |
| Frontend | SolidJS + Vite + TypeScript | Modern SPA deneyimi |
| Reverse Proxy | Nginx | Strangler routing ve güvenlik header'ları |
| Legacy Katman | Flask + Gunicorn | Geçiş sürecinde `/api/*` uyumluluğu |
| Container | Docker Compose | Dev/prod/test ortam orkestrasyonu |
| Test | Python `unittest` | Kontrat, servis ve güvenlik testleri |

## 3. Veritabanı Tasarımı

PostgreSQL şeması Alembic ile yönetilir. İlk FastAPI migration: `20260313_0001`.

### 3.1 Ana Entity Grupları

1. `users`
2. `auth_tokens`
3. `user_sessions`
4. `pii.user_pii`
5. `neighborhoods`
6. `cafes`
7. `cafe_amenities`
8. `cafe_hours`
9. `cafe_images`
10. `cafe_seats`
11. `reviews`
12. `review_votes`
13. `bookmarks`

### 3.2 Migration Komutları

```bash
# Lokal
python3 -m alembic upgrade head

# Docker (dev)
docker compose --profile dev run --rm api-dev python -m alembic upgrade head
```

## 4. API Tasarımı ve Standartlar

### 4.1 Genel Kurallar

- Base path: `/api/v1`
- HTTP metotları: `GET`, `POST`, `PATCH`, `DELETE`
- Pagination: cursor tabanlı (`created_at + id`) yapı kullanılır
- Auth: Cookie tabanlı session + CSRF koruması

### 4.2 Endpoint Özeti

**Health**
- `GET /api/v1/health`

**Auth**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/magic-link`
- `POST /api/v1/auth/verify`
- `GET /api/v1/auth/verify?token=...`
- `GET /api/v1/auth/csrf`
- `GET /api/v1/auth/session`
- `POST /api/v1/auth/logout`

**Cafes**
- `GET /api/v1/cafes`
- `GET /api/v1/cafes/{slug}`

**Reviews**
- `GET /api/v1/cafes/{cafe_id}/reviews`
- `POST /api/v1/cafes/{cafe_id}/reviews`
- `DELETE /api/v1/reviews/{review_id}`
- `POST /api/v1/reviews/{review_id}/vote`
- `DELETE /api/v1/reviews/{review_id}/vote`

**Users**
- `DELETE /api/v1/users/me`
- `PATCH /api/v1/users/me/consent`
- `DELETE /api/v1/admin/users/{user_id}`

## 5. Güvenlik ve KVKK

### 5.1 Tamamlanan Başlıklar

- Hesap silme akışı ve `pii.user_pii` hard-delete
- Cookie rıza yönetimi ve consent alanlarının akışa bağlanması
- Nginx production security header'ları
- FastAPI CSRF middleware (write endpoint'ler için)
- `verify` response body içinden `session_token` kaldırılması
- PII alanları için uygulama seviyesinde koruma (env anahtarıyla)

### 5.2 CSRF Davranışı

- Session cookie bulunan write isteklerinde CSRF zorunlu
- Header: `X-CSRFToken` veya `X-CSRF-Token`
- Cookie: `csrf_token`
- Token üretimi: `GET /api/v1/auth/csrf`
- Uyum: frontend `apiRequest` katmanı CSRF token ekleyecek şekilde çalışır

### 5.3 Nginx Security Header'ları (prod)

- `Strict-Transport-Security`
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- Başlangıç seviyesi `Content-Security-Policy`

### 5.4 PII Koruma Notu

- Anahtarlar: `KVKK_ENCRYPTION_KEY`, `KVKK_HASH_PEPPER`
- Korunan alanlar: ad-soyad, telefon, adres satırları, şehir, ilçe, posta kodu
- Anahtar placeholder ise koruma pasif kalır; prod ortamında gerçek değer kullanılmalıdır.

## 6. Test Stratejisi

Testler `tests/` altında `unittest` tabanlı yürür.

Öne çıkan test kümeleri:
- `test_fastapi_v1_contract.py`
- `test_fastapi_csrf_contract.py`
- `test_account_deletion_service.py`
- `test_users_router_contract.py`
- `test_reviews_router_contract.py`
- `test_pii_protection.py`
- legacy regressions: `test_api_hardening.py`, `test_frontend_cutover.py`

Komutlar:

```bash
# Tüm testler
npm test

# Doğrudan Python testleri
python3 -m unittest discover -s tests -p "test_*.py"

# Frontend build doğrulaması
npm --prefix frontend-solid run build
```

## 7. Kurulum ve Çalıştırma

### 7.1 Gereksinimler

- Docker + Docker Compose (önerilen)
- Lokal çalışma için: Python 3.9+, Node.js 20+

### 7.2 Lokal FastAPI Çalıştırma

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m alembic upgrade head
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API: <http://127.0.0.1:8000/api/v1/health>
- Swagger: <http://127.0.0.1:8000/docs>

### 7.3 Seed Data

```bash
# Dry-run
docker compose --profile dev run --rm api-dev python scripts/seed_dev_data.py --dry-run

# Gerçek seed
docker compose --profile dev run --rm api-dev python scripts/seed_dev_data.py

# Sadece boş DB ise seed
docker compose --profile dev run --rm api-dev python scripts/seed_dev_data.py --if-empty
```

Seed script idempotent çalışacak şekilde tasarlanmıştır.

## 8. Frontend (SolidJS)

Frontend kaynak kodu: `frontend-solid/`

```bash
# Development
npm --prefix frontend-solid run dev

# Production build
npm --prefix frontend-solid run build

# Preview
npm --prefix frontend-solid run preview
```

Temel sayfalar:
- `HomePage`, `CafesPage`, `CafeDetailPage`
- `SignupPage`, `LoginPage`, `AuthVerifyPage`
- `AdminPage`, `PrivacyPage`, `ContactPage`

## 9. Production Notları

### 9.1 Strangler Routing

- `/api/v1/*` -> FastAPI
- `/api/*` -> Legacy Flask
- `/*` -> SolidJS frontend

### 9.2 Preflight ve Deploy

```bash
# Ön kontrol
scripts/preflight_prod.sh

# Prod stack
docker compose --profile prod up -d --build

# Migration
docker compose --profile prod run --rm api-prod python -m alembic upgrade head
```

### 9.3 Operasyonel Sağlık Kontrolü

```bash
curl -fsS http://localhost/api/v1/health
curl -fsS http://localhost/docs >/dev/null
docker compose --profile prod ps
```

Not: HSTS'nin etkili olması için uygulama TLS termination ile çalıştırılmalıdır.

## 10. Lisans

Bu proje [MIT License](LICENSE) ile lisanslanmıştır.

## Ek Dokümanlar

- [Fazlı Güvenlik Checklist](docs/checkup-fazli-checklist.md)
- [Veritabanı Şema Diyagramı (DBML)](docs/database-schema.dbml)
