# Kahvesiz Çalışma

> Uzaktan çalışanlar için kafe keşif platformu. Strangler Pattern ile Flask (legacy) + FastAPI (v1) birlikte çalışır.

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

## 0. Hızlı Kurulum

### Docker ile (Önerilen)

```bash
# 1) Ortam değişkenlerini hazırla
cp .env.example .env

# 2) Development stack'ini başlat
docker compose --profile dev up -d --build

# 3) Test servislerini (DB + Redis) başlat
docker compose --profile test up -d --build

# 4) İsteğe bağlı migration
docker compose --profile dev run --rm api-dev python -m alembic upgrade head

# 5) Kapat
docker compose --profile dev --profile test down
```

### Erişim Adresleri (Dev)

- Uygulama (Nginx): <http://localhost>
- SolidJS Vite Dev Server: <http://localhost:5173>
- FastAPI Swagger: <http://localhost/docs>
- FastAPI Health: <http://localhost/api/v1/health>

---

## 1. Proje Kapsamı

**Kimlik Doğrulama (Magic Link + Session Cookie)**
`/api/v1/auth/*` altında register, magic-link, verify, session ve logout akışları bulunur. `verify` sonrası HttpOnly `session_token` cookie set edilir. CSRF middleware write endpoint'leri korur.

**Kafe Keşfi ve Detay Deneyimi**
Cursor tabanlı kafe listeleme, filtreleme (`wifi`, `neighborhood`, `noise_level`, `has_outlet`) ve detay sayfasında amenity/saat/görsel/koltuk/yorum birleşik payload üretilir.

**Yorum Sistemi ve Oylama**
Kullanıcılar kafe yorumu oluşturabilir, silebilir; helpful/unhelpful oylayabilir. Listeleme cursor tabanlıdır.

**Hesap Silme ve PII Purge**
`DELETE /api/v1/users/me` ile kullanıcı soft-delete, PII hard-delete, yorum anonimleştirme ve aktif session invalidation tek servis akışında yönetilir.

**Cookie Rıza Yönetimi**
SolidJS tarafında banner ile tercih alınır; backend `PATCH /api/v1/users/me/consent` ile `consent_given_at` ve `consent_version` güncellenir.

**KVKK Odaklı PII Koruma**
`pii.user_pii` kritik alanları uygulama katmanında `KVKK_ENCRYPTION_KEY` / `KVKK_HASH_PEPPER` ile korunarak yazılır.

**Strangler Geçiş Mimarisi**
Legacy Flask kodu anında kaldırılmamaktadır. Yeni FastAPI endpoint'leri hazır oldukça Nginx `location` bloğu ile trafik yönlendirilir. Bir route tamamen geçince legacy kod devre dışı bırakılır.

## 2. Teknoloji Yığını

| Kategori | Teknoloji | Kullanım Amacı |
|---|---|---|
| **Backend API** | FastAPI | Versiyonlu REST API (`/api/v1`), async native, otomatik OpenAPI |
| **ORM** | SQLAlchemy 2.0 (async) | Declarative modeller, veri erişimi |
| **Migration** | Alembic | Şema versiyonlama, code-first akış |
| **Validation** | Pydantic v2 | Request/response doğrulama, PII sızıntısını compile-time'da önleme |
| **Veritabanı** | PostgreSQL 16 | Ana veri deposu |
| **Cache / Session** | Redis 7 | Session store, rate limiting, koltuk sayısı atomic ops, cursor cache |
| **Frontend** | SolidJS + Vite + TypeScript | Modern SPA deneyimi, infinite scroll |
| **Reverse Proxy** | Nginx 1.27 | Strangler routing, security header'ları |
| **Legacy Katman** | Flask + Gunicorn | Geçiş sürecinde `/api/*` uyumluluğu |
| **Email** | Resend | Magic link ve transactional email |
| **Container** | Docker Compose | Dev / test / prod ortam orkestrasyonu |
| **Test** | Python `unittest` | Kontrat, servis ve güvenlik testleri |

## 3. Veritabanı Tasarımı

PostgreSQL şeması Alembic ile yönetilir. DBML diyagramı: [docs/database-schema.dbml](docs/database-schema.dbml)

### 3.1 Entity Listesi

1. **users** — Sistem kullanıcıları (soft-delete destekli).
2. **auth_tokens** — Magic link / email doğrulama / şifre sıfırlama token'ları (SHA-256 hash'li).
3. **user_sessions** — Aktif oturumlar; token hash PostgreSQL'de, cache Redis'te.
4. **pii.user_pii** — KVKK kapsamındaki kişisel veriler (ad, telefon, adres, rıza zamanı). Ayrı schema'da tutulur.
5. **neighborhoods** — Semt/mahalle tanımları.
6. **cafes** — Kafe profilleri; `avg_rating` / `review_count` trigger ile güncellenir.
7. **cafe_amenities** — Kafenin olanakları (wifi, priz, gürültü seviyesi, klima vb.), cafes ile 1-to-1.
8. **cafe_hours** — Haftalık çalışma saatleri (gün bazlı).
9. **cafe_images** — Kafe görselleri ve URL'leri.
10. **cafe_seats** — Masa/koltuk tipleri ve anlık doluluk (`available_count` Redis'te atomic).
11. **reviews** — Kullanıcı yorumları; kullanıcı başına kafe başına bir yorum.
12. **review_votes** — Yorum helpful/unhelpful oylaması.
13. **bookmarks** — Kullanıcı kafe favorileri.

### 3.2 Migration Komutları

**Entity Framework Core Code-First** yerine **Alembic Code-First** metodolojisi kullanılır.

```bash
# Lokal
python3 -m alembic upgrade head

# Docker (dev)
docker compose --profile dev run --rm api-dev python -m alembic upgrade head

# Yeni migration oluştur
python3 -m alembic revision --autogenerate -m "migration_adi"
```

## 4. API Tasarımı ve Standartlar

### 4.1 Genel Kurallar

- **Base path:** `/api/v1`
- **HTTP Metotları:** `GET`, `POST`, `PATCH`, `DELETE`
- **Pagination:** Cursor tabanlı (`created_at + id` composite), `OFFSET` kullanılmaz
- **Auth:** HttpOnly session cookie + CSRF koruması
- **Versiyonlama:** Breaking change'ler `/api/v2` altında açılır; `v1` geriye dönük uyumlu kalır

### 4.2 Response ve Hata Modeli

**Başarılı Cevaplar:**

```json
{
  "success": true,
  "message": "İşlem başarılı",
  "data": {}
}
```

**Hata Cevapları:**
Tüm hatalar merkezi `ExceptionHandlingMiddleware` tarafından yakalanır.

```json
{
  "detail": "Kaynak bulunamadı.",
  "error_code": "NOT_FOUND"
}
```

### 4.3 Pagination (Cursor Tabanlı)

Liste dönen endpoint'lerde cursor tabanlı sayfalama kullanılır.

- **Request:** `?cursor=<opaque_token>&limit=20`
- **Cursor formatı:** `base64(created_at::timestamp + ":" + id::uuid)`
- **Response Metadata:**

    ```json
    {
      "items": [],
      "next_cursor": "eyJjcmVhdGVkX...",
      "total_count": 150
    }
    ```

### 4.4 Endpoint Özeti

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
- `GET /api/v1/cafes` — `cursor`, `limit`, `neighborhood`, `wifi`, `noise_level`, `has_outlet` parametreleri
- `GET /api/v1/cafes/{slug}` — amenities + hours + images + seats birleşik detay

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

### 4.5 Swagger UI

API dokümantasyonu: `http://localhost/docs` (dev) veya `http://localhost:8000/docs` (lokal)

## 5. Güvenlik ve KVKK

### 5.1 Tamamlanan Başlıklar

- Hesap silme akışı ve `pii.user_pii` hard-delete
- Cookie rıza yönetimi ve consent alanlarının akışa bağlanması
- Nginx production security header'ları
- FastAPI CSRF middleware (write endpoint'ler için)
- `verify` response body'sinden `session_token` kaldırılması
- PII alanları için uygulama seviyesinde şifreleme (env anahtarı ile)

### 5.2 CSRF Davranışı

- Session cookie bulunan write isteklerinde CSRF zorunlu
- Header: `X-CSRFToken` veya `X-CSRF-Token`
- Cookie: `csrf_token`
- Token üretimi: `GET /api/v1/auth/csrf`
- Frontend `apiRequest` katmanı CSRF token'ı otomatik ekler

### 5.3 Nginx Security Header'ları (Prod)

- `Strict-Transport-Security`
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- Başlangıç seviyesi `Content-Security-Policy`

### 5.4 PII Koruma

- Anahtarlar: `KVKK_ENCRYPTION_KEY`, `KVKK_HASH_PEPPER`
- Korunan alanlar: ad-soyad, telefon, adres satırları, şehir, ilçe, posta kodu
- Anahtar placeholder ise koruma pasif kalır; prod ortamında mutlaka gerçek değer kullanılmalıdır
- `KVKK_CONSENT_VERSION` ile KVKK metni güncellendiğinde yeni onay toplanması sağlanır

## 6. Test Stratejisi

Testler `tests/` altında Python `unittest` ile çalışır.

### 6.1 Test Kümeleri

| Dosya | Kapsam |
|---|---|
| `test_fastapi_v1_contract.py` | FastAPI v1 endpoint kontrat testleri |
| `test_fastapi_csrf_contract.py` | CSRF middleware davranışı |
| `test_account_deletion_service.py` | Hesap silme ve PII purge akışı |
| `test_users_router_contract.py` | Users endpoint kontratları |
| `test_reviews_router_contract.py` | Reviews endpoint kontratları |
| `test_pii_protection.py` | PII şifreleme ve maskeleme |
| `test_api_hardening.py` | Legacy Flask güvenlik regresyonları |
| `test_frontend_cutover.py` | Nginx strangler routing doğrulaması |

### 6.2 Test Komutları

```bash
# Tüm testleri çalıştır
npm test

# Doğrudan Python testleri
python3 -m unittest discover -s tests -p "test_*.py"

# Frontend build doğrulaması
npm --prefix frontend-solid run build
```

### 6.3 Test Ortamı

Test servisleri (PostgreSQL + Redis) izole container'larda çalışır:

```bash
docker compose --profile test up -d
```

Test veritabanı: `kahvesiz_test` (port `55432`), Redis (port `56379`)

## 7. Kurulum ve Çalıştırma

### 7.1 Gereksinimler

- [Docker & Docker Compose](https://docs.docker.com/compose/) (önerilen)
- Lokal çalışma için: Python 3.9+, Node.js 20+

### 7.2 Environment Değişkenleri

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyerek aşağıdaki kritik değerleri doldurun:

```bash
# PostgreSQL (Dev)
DATABASE_URL_DEV=postgresql+asyncpg://user:pass@db-dev:5432/kahvesiz_dev

# Redis (Dev)
REDIS_URL_DEV=redis://redis-dev:6379/0

# Auth
SECRET_KEY=<32-byte-random>
ACCESS_TOKEN_EXPIRE_MINUTES=15
SESSION_EXPIRE_DAYS=30

# Email (Resend)
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=noreply@kahvesizcalisma.com

# KVKK
KVKK_ENCRYPTION_KEY=<32-char-min>
KVKK_HASH_PEPPER=<random-string>
KVKK_CONSENT_VERSION=v1
```

### 7.3 Docker Compose ile Çalıştırma (Önerilen)

```bash
# Development ortamını başlat
docker compose --profile dev up -d --build

# Test servislerini başlat
docker compose --profile test up -d

# Production ortamını başlat
docker compose --profile prod up -d --build

# Tüm servisleri durdur
docker compose --profile dev --profile test --profile prod down
```

**Servis Erişim Adresleri (Dev):**

| Servis | Port | URL |
|--------|------|-----|
| Nginx (reverse proxy) | 80 | <http://localhost> |
| SolidJS Vite Dev Server | 5173 | <http://localhost:5173> |
| FastAPI Swagger | 80 | <http://localhost/docs> |
| FastAPI Health | 80 | <http://localhost/api/v1/health> |
| PostgreSQL (sadece test dışarıdan) | - | internal |
| Redis | - | internal |

### 7.4 Manuel Kurulum (Lokal)

**Gereksinimler:** Python 3.9+, PostgreSQL 16, Redis 7, Node.js 20+

```bash
# 1. Python bağımlılıklarını yükle
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Veritabanı migration'larını uygula
python3 -m alembic upgrade head

# 3. API'yi başlat
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Frontend'i başlat
cd frontend-solid
npm install
npm run dev
```

- API: <http://127.0.0.1:8000/api/v1/health>
- Swagger: <http://127.0.0.1:8000/docs>

### 7.5 Seed Data (Örnek Veriler)

`api-dev` container'ı başladığında seed script `--if-empty` flag'i ile otomatik çalışır.

```bash
# Dry-run (sadece görmek için)
docker compose --profile dev run --rm api-dev python scripts/seed_dev_data.py --dry-run

# Gerçek seed
docker compose --profile dev run --rm api-dev python scripts/seed_dev_data.py

# Sadece boş DB ise seed et
docker compose --profile dev run --rm api-dev python scripts/seed_dev_data.py --if-empty
```

Seed script idempotent çalışacak şekilde tasarlanmıştır.

### 7.6 Örnek Kullanım Akışı (cURL)

```bash
# 1. Kayıt ol
curl -X POST "http://localhost/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@test.com","username":"demouser"}'

# 2. Magic link iste
curl -X POST "http://localhost/api/v1/auth/magic-link" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@test.com"}'

# 3. Token ile doğrula (emailden gelen token)
curl "http://localhost/api/v1/auth/verify?token=<TOKEN>"
# → session_token cookie set edilir

# 4. Kafeleri listele
curl "http://localhost/api/v1/cafes?limit=10&wifi=true"

# 5. Kafe detayı
curl "http://localhost/api/v1/cafes/moda-coffee-house"

# 6. Yorum yaz (session cookie gerekli)
curl -X POST "http://localhost/api/v1/cafes/<cafe_id>/reviews" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf_token>" \
  --cookie "session_token=<TOKEN>" \
  -d '{"rating":5,"body":"Harika wifi ve sakin ortam."}'
```

## 8. Frontend (SolidJS)

React değil SolidJS + Vite + TypeScript tabanlı SPA. Kaynak kodu: `frontend-solid/`

```bash
# Development
npm --prefix frontend-solid run dev

# Production build
npm --prefix frontend-solid run build

# Preview (prod build)
npm --prefix frontend-solid run preview
```

**Klasör Yapısı:**

```
frontend-solid/src/
├── components/    # UI bileşenleri
├── lib/           # API client (cafes.ts, auth.ts vb.)
├── pages/         # Sayfa bileşenleri
└── types/         # TypeScript tipleri
```

**Sayfalar:** `HomePage`, `CafesPage`, `CafeDetailPage`, `SignupPage`, `LoginPage`, `AuthVerifyPage`, `AdminPage`, `PrivacyPage`, `ContactPage`

**Infinite Scroll:** `createResource + signal + IntersectionObserver` ile cursor-based pagination. Son kart görünüme girince `next_cursor` ile yeni istek tetiklenir.

## 9. Production Notları

### 9.1 Strangler Routing (Nginx)

```
İstek → Nginx
    ├─ /api/v1/*  → FastAPI (yeni, :8000)
    ├─ /api/*     → Flask legacy (:5040, kademeli azalacak)
    └─ /*         → SolidJS static build
```

Nginx config dosyaları: `nginx/dev.conf`, `nginx/prod.conf`

### 9.2 Deploy ve Migration

```bash
# Ön kontrol
scripts/preflight_prod.sh

# Production stack
docker compose --profile prod up -d --build

# Migration (prod)
docker compose --profile prod run --rm api-prod python -m alembic upgrade head
```

### 9.3 Operasyonel Sağlık Kontrolleri

```bash
# Temel sağlık
curl -fsS http://localhost/api/v1/health

# Swagger erişimi (dev/staging)
curl -fsS http://localhost/docs >/dev/null

# Servis durumu
docker compose --profile prod ps
```

> Not: HSTS'nin etkili olması için uygulama TLS termination ile çalıştırılmalıdır.

### 9.4 Kritik Ortam Değişkenleri (Prod)

```bash
DATABASE_URL_PROD=postgresql+asyncpg://...
REDIS_URL_PROD=redis://...
SECRET_KEY=<32-byte-random>
KVKK_ENCRYPTION_KEY=<32-char-min>
KVKK_HASH_PEPPER=<random-string>
RESEND_API_KEY=re_...
ENVIRONMENT=production
```

### 9.5 SQLite → PostgreSQL Veri Migrasyonu (gerekirse)

Eğer legacy `instance/cafes.db` içindeki verinin korunması gerekiyorsa:

```bash
# 1. SQLite'ı dışa aktar
sqlite3 instance/cafes.db .dump > legacy_dump.sql

# 2. Tip farklarını düzelt (AUTOINCREMENT → UUID vb.)

# 3. PostgreSQL'e aktar
psql $DATABASE_URL < legacy_dump_converted.sql
```

> Eğer legacy veri kritik değilse (test verisi ise) bu adımı atlayın ve PostgreSQL'i temiz başlatın.

## 10. Lisans

Bu proje [MIT License](LICENSE) ile lisanslanmıştır.
