# Kahvesiz Çalışma

> A cafe discovery platform for remote workers. Runs Flask (legacy) + FastAPI (v1) side by side via the Strangler Pattern.

## Table of Contents

- [0. Quick Start](#0-quick-start)
- [1. Project Scope](#1-project-scope)
- [2. Technology Stack](#2-technology-stack)
- [3. Database Design](#3-database-design)
- [4. API Design and Standards](#4-api-design-and-standards)
- [5. Security and KVKK (GDPR equivalent)](#5-security-and-kvkk)
- [6. Testing Strategy](#6-testing-strategy)
- [7. Setup and Running](#7-setup-and-running)
- [8. Frontend (SolidJS)](#8-frontend-solidjs)
- [9. Production Notes](#9-production-notes)
- [10. License](#10-license)
- [Additional Documentation](#additional-documentation)

## 0. Quick Start

### With Docker (Recommended)

```bash
# 1) Prepare environment variables
cp .env.example .env

# 2) Start the development stack
docker compose --profile dev up -d --build

# 3) Start test services (DB + Redis)
docker compose --profile test up -d --build

# 4) Optional: run migrations manually
docker compose --profile dev run --rm api-dev python -m alembic upgrade head

# 5) Stop everything
docker compose --profile dev --profile test down
```

### Access URLs (Dev)

- Application (Nginx): <http://localhost>
- SolidJS Vite Dev Server: <http://localhost:5173>
- FastAPI Swagger: <http://localhost/docs>
- FastAPI Health: <http://localhost/api/v1/health>

---

## 1. Project Scope

**Authentication (Magic Link + Session Cookie)**
Register, magic-link, verify, session, and logout flows live under `/api/v1/auth/*`. After `verify`, an HttpOnly `session_token` cookie is set. CSRF middleware protects all write endpoints.

**Cafe Discovery and Detail Experience**
Cursor-based cafe listing, filtering by `wifi`, `neighborhood`, `noise_level`, `has_outlet`, and a combined amenity/hours/images/seats/reviews payload on the detail page.

**Review System and Voting**
Users can create and delete cafe reviews and cast helpful/unhelpful votes. Listing is cursor-based.

**Account Deletion and PII Purge**
`DELETE /api/v1/users/me` handles soft-delete of the user, hard-delete of PII, review anonymisation, and active session invalidation in a single service flow.

**Cookie Consent Management**
A banner in SolidJS collects user preference; the backend updates `consent_given_at` and `consent_version` via `PATCH /api/v1/users/me/consent`.

**KVKK-Focused PII Protection**
Critical fields in `pii.user_pii` are written with application-level encryption using `KVKK_ENCRYPTION_KEY` / `KVKK_HASH_PEPPER`.

**Strangler Migration Architecture**
Legacy Flask code is not removed immediately. As new FastAPI endpoints become ready, Nginx `location` blocks redirect traffic. Once a route is fully migrated, the legacy code for that route is disabled.

## 2. Technology Stack

| Category | Technology | Purpose |
|---|---|---|
| **Backend API** | FastAPI | Versioned REST API (`/api/v1`), async-native, automatic OpenAPI |
| **ORM** | SQLAlchemy 2.0 (async) | Declarative models, data access |
| **Migration** | Alembic | Schema versioning, code-first workflow |
| **Validation** | Pydantic v2 | Request/response validation, compile-time PII leak prevention |
| **Database** | PostgreSQL 16 | Primary data store |
| **Cache / Session** | Redis 7 | Session store, rate limiting, atomic seat count ops, cursor cache |
| **Frontend** | SolidJS + Vite + TypeScript | Modern SPA experience, infinite scroll |
| **Reverse Proxy** | Nginx 1.27 | Strangler routing, security headers |
| **Legacy Layer** | Flask + Gunicorn | `/api/*` compatibility during transition |
| **Email** | Resend | Magic link and transactional email delivery |
| **Container** | Docker Compose | Dev / test / prod environment orchestration |
| **Testing** | Python `unittest` | Contract, service, and security tests |

## 3. Database Design

The PostgreSQL schema is managed by Alembic. DBML diagram: [docs/database-schema.dbml](docs/database-schema.dbml)

### 3.1 Entity List

1. **users** — System users (soft-delete supported).
2. **auth_tokens** — Magic link / email verification / password reset tokens (SHA-256 hashed).
3. **user_sessions** — Active sessions; token hash in PostgreSQL, cache in Redis.
4. **pii.user_pii** — KVKK-scoped personal data (name, phone, address, consent timestamp). Stored in a separate schema.
5. **neighborhoods** — District / neighbourhood definitions.
6. **cafes** — Cafe profiles; `avg_rating` / `review_count` updated by trigger.
7. **cafe_amenities** — Cafe facilities (wifi, outlets, noise level, AC, etc.), 1-to-1 with cafes.
8. **cafe_hours** — Weekly operating hours (per day).
9. **cafe_images** — Cafe photos and their URLs.
10. **cafe_seats** — Seat types and real-time availability (`available_count` is atomic in Redis).
11. **reviews** — User reviews; one review per user per cafe.
12. **review_votes** — Helpful/unhelpful votes on reviews.
13. **bookmarks** — User cafe favourites.

### 3.2 Migration Commands

The project uses an **Alembic Code-First** methodology.

```bash
# Local
python3 -m alembic upgrade head

# Docker (dev)
docker compose --profile dev run --rm api-dev python -m alembic upgrade head

# Create a new migration
python3 -m alembic revision --autogenerate -m "migration_name"
```

## 4. API Design and Standards

### 4.1 General Rules

- **Base path:** `/api/v1`
- **HTTP Methods:** `GET`, `POST`, `PATCH`, `DELETE`
- **Pagination:** Cursor-based (`created_at + id` composite); `OFFSET` is not used
- **Auth:** HttpOnly session cookie + CSRF protection
- **Versioning:** Breaking changes open under `/api/v2`; `v1` remains backward-compatible

### 4.2 Response and Error Model

**Successful Responses:**

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

**Error Responses:**
All errors are caught by the central `ExceptionHandlingMiddleware`.

```json
{
  "detail": "Resource not found.",
  "error_code": "NOT_FOUND"
}
```

### 4.3 Pagination (Cursor-Based)

All list endpoints use cursor-based pagination.

- **Request:** `?cursor=<opaque_token>&limit=20`
- **Cursor format:** `base64(created_at::timestamp + ":" + id::uuid)`
- **Response Metadata:**

    ```json
    {
      "items": [],
      "next_cursor": "eyJjcmVhdGVkX...",
      "total_count": 150
    }
    ```

### 4.4 Endpoint Summary

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
- `GET /api/v1/cafes` — supports `cursor`, `limit`, `neighborhood`, `wifi`, `noise_level`, `has_outlet`
- `GET /api/v1/cafes/{slug}` — combined detail payload: amenities + hours + images + seats

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

API documentation: `http://localhost/docs` (dev) or `http://localhost:8000/docs` (local)

## 5. Security and KVKK

### 5.1 Completed Items

- Account deletion flow and `pii.user_pii` hard-delete
- Cookie consent management and consent field wiring
- Nginx production security headers
- FastAPI CSRF middleware for write endpoints
- Removed `session_token` from `verify` response body
- Application-level PII field encryption (env key)

### 5.2 CSRF Behaviour

- CSRF is required on write requests when a session cookie is present
- Header: `X-CSRFToken` or `X-CSRF-Token`
- Cookie: `csrf_token`
- Token generation: `GET /api/v1/auth/csrf`
- The frontend `apiRequest` layer automatically attaches the CSRF token

### 5.3 Nginx Security Headers (Prod)

- `Strict-Transport-Security`
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- Baseline `Content-Security-Policy`

### 5.4 PII Protection

- Keys: `KVKK_ENCRYPTION_KEY`, `KVKK_HASH_PEPPER`
- Protected fields: full name, phone, address lines, city, district, postal code
- If the key is a placeholder, protection remains passive; real values must be used in production
- `KVKK_CONSENT_VERSION` ensures re-consent is collected when the privacy policy is updated

## 6. Testing Strategy

Tests run with Python `unittest` under the `tests/` directory.

### 6.1 Test Suites

| File | Coverage |
|---|---|
| `test_fastapi_v1_contract.py` | FastAPI v1 endpoint contract tests |
| `test_fastapi_csrf_contract.py` | CSRF middleware behaviour |
| `test_account_deletion_service.py` | Account deletion and PII purge flow |
| `test_users_router_contract.py` | Users endpoint contracts |
| `test_reviews_router_contract.py` | Reviews endpoint contracts |
| `test_pii_protection.py` | PII encryption and masking |
| `test_api_hardening.py` | Legacy Flask security regressions |
| `test_frontend_cutover.py` | Nginx strangler routing validation |

### 6.2 Test Commands

```bash
# Run all tests
npm test

# Python tests directly
python3 -m unittest discover -s tests -p "test_*.py"

# Frontend build validation
npm --prefix frontend-solid run build
```

### 6.3 Test Environment

Test services (PostgreSQL + Redis) run in isolated containers:

```bash
docker compose --profile test up -d
```

Test database: `kahvesiz_test` (port `55432`), Redis (port `56379`)

## 7. Setup and Running

### 7.1 Requirements

- [Docker & Docker Compose](https://docs.docker.com/compose/) (recommended)
- For local development: Python 3.9+, Node.js 20+

### 7.2 Environment Variables

```bash
cp .env.example .env
```

Fill in the following critical values in your `.env` file:

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

### 7.3 Running with Docker Compose (Recommended)

```bash
# Start development environment
docker compose --profile dev up -d --build

# Start test services
docker compose --profile test up -d

# Start production environment
docker compose --profile prod up -d --build

# Stop all services
docker compose --profile dev --profile test --profile prod down
```

**Service Access URLs (Dev):**

| Service | Port | URL |
|---------|------|-----|
| Nginx (reverse proxy) | 80 | <http://localhost> |
| SolidJS Vite Dev Server | 5173 | <http://localhost:5173> |
| FastAPI Swagger | 80 | <http://localhost/docs> |
| FastAPI Health | 80 | <http://localhost/api/v1/health> |
| PostgreSQL (test only exposed) | - | internal |
| Redis | - | internal |

### 7.4 Manual Local Setup

**Requirements:** Python 3.9+, PostgreSQL 16, Redis 7, Node.js 20+

```bash
# 1. Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run database migrations
python3 -m alembic upgrade head

# 3. Start the API
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Start the frontend
cd frontend-solid
npm install
npm run dev
```

- API: <http://127.0.0.1:8000/api/v1/health>
- Swagger: <http://127.0.0.1:8000/docs>

### 7.5 Seed Data

The `api-dev` container runs the seed script automatically with the `--if-empty` flag on startup.

```bash
# Dry-run (preview only)
docker compose --profile dev run --rm api-dev python scripts/seed_dev_data.py --dry-run

# Real seed
docker compose --profile dev run --rm api-dev python scripts/seed_dev_data.py

# Only seed if DB is empty
docker compose --profile dev run --rm api-dev python scripts/seed_dev_data.py --if-empty
```

The seed script is designed to run idempotently.

### 7.6 Example Usage Flow (cURL)

```bash
# 1. Register
curl -X POST "http://localhost/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@test.com","username":"demouser"}'

# 2. Request a magic link
curl -X POST "http://localhost/api/v1/auth/magic-link" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@test.com"}'

# 3. Verify using the token from the email
curl "http://localhost/api/v1/auth/verify?token=<TOKEN>"
# → session_token cookie is set

# 4. List cafes
curl "http://localhost/api/v1/cafes?limit=10&wifi=true"

# 5. Cafe detail
curl "http://localhost/api/v1/cafes/moda-coffee-house"

# 6. Post a review (session cookie required)
curl -X POST "http://localhost/api/v1/cafes/<cafe_id>/reviews" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf_token>" \
  --cookie "session_token=<TOKEN>" \
  -d '{"rating":5,"body":"Great wifi and quiet atmosphere."}'
```

## 8. Frontend (SolidJS)

SPA built with SolidJS + Vite + TypeScript (not React). Source: `frontend-solid/`

```bash
# Development
npm --prefix frontend-solid run dev

# Production build
npm --prefix frontend-solid run build

# Preview production build
npm --prefix frontend-solid run preview
```

**Folder Structure:**

```
frontend-solid/src/
├── components/    # UI components
├── lib/           # API client (cafes.ts, auth.ts, etc.)
├── pages/         # Page components
└── types/         # TypeScript types
```

**Pages:** `HomePage`, `CafesPage`, `CafeDetailPage`, `SignupPage`, `LoginPage`, `AuthVerifyPage`, `AdminPage`, `PrivacyPage`, `ContactPage`

**Infinite Scroll:** Implemented with `createResource + signal + IntersectionObserver` and cursor-based pagination. When the last card enters the viewport, a new request is triggered using `next_cursor`.

## 9. Production Notes

### 9.1 Strangler Routing (Nginx)

```
Request → Nginx
    ├─ /api/v1/*  → FastAPI (new, :8000)
    ├─ /api/*     → Flask legacy (:5040, gradually being removed)
    └─ /*         → SolidJS static build
```

Nginx config files: `nginx/dev.conf`, `nginx/prod.conf`

### 9.2 Deploy and Migration

```bash
# Pre-flight check
scripts/preflight_prod.sh

# Production stack
docker compose --profile prod up -d --build

# Run migrations (prod)
docker compose --profile prod run --rm api-prod python -m alembic upgrade head
```

### 9.3 Operational Health Checks

```bash
# Basic health
curl -fsS http://localhost/api/v1/health

# Swagger access (dev/staging)
curl -fsS http://localhost/docs >/dev/null

# Service status
docker compose --profile prod ps
```

> Note: HSTS takes effect only when the application runs behind TLS termination.

### 9.4 Critical Environment Variables (Prod)

```bash
DATABASE_URL_PROD=postgresql+asyncpg://...
REDIS_URL_PROD=redis://...
SECRET_KEY=<32-byte-random>
KVKK_ENCRYPTION_KEY=<32-char-min>
KVKK_HASH_PEPPER=<random-string>
RESEND_API_KEY=re_...
ENVIRONMENT=production
```

### 9.5 SQLite → PostgreSQL Data Migration (if needed)

If the legacy data in `instance/cafes.db` must be preserved:

```bash
# 1. Export SQLite
sqlite3 instance/cafes.db .dump > legacy_dump.sql

# 2. Fix type differences (AUTOINCREMENT → UUID, etc.)

# 3. Import into PostgreSQL
psql $DATABASE_URL < legacy_dump_converted.sql
```

> If the legacy data is not critical (e.g. test data), skip this step and start PostgreSQL clean.

## 10. License

This project is licensed under the [MIT License](LICENSE).

## Additional Documentation

- [Decision Log & Migration Roadmap](docs/decisions-and-roadmap.md)
- [Architecture and Database Plan](docs/architecture-plan.md)
- [Security & KVKK Implementation Plan](docs/guvenlik-kvkk-fazli-uygulama-plani.md)
- [SolidJS Frontend Migration Plan](docs/solidjs-frontend-gecis-plani.md)
- [Review System Plan](docs/review-sistemi-fazli-plan.md)
- [Homepage Section Plan](docs/homepage-solid-sections-plan.md)
- [Security Checklist](docs/checkup-fazli-checklist.md)
- [Database Schema DBML](docs/database-schema.dbml)
