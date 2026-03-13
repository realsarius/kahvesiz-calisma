# Kahvesiz Çalışma API

> Bu repo adı eski olsa da proje, kafe/laptop çalışma deneyimi odaklı bir Flask web + API uygulamasıdır.

## İçindekiler

- [0. Hızlı Kurulum](#0-hızlı-kurulum)
- [1. Kapsam](#1-kapsam)
- [2. Teknoloji Yığını](#2-teknoloji-yığını-technology-stack)
- [3. Veritabanı Tasarımı](#3-veritabanı-tasarımı-database-design)
- [4. API Tasarımı](#4-api-tasarımı-ve-standartlar-api-design)
- [5. Loglama ve Hata Yönetimi](#5-loglama-i̇zlenebilirlik-ve-hata-yönetimi-observability)
- [6. Test Stratejisi](#6-test-stratejisi-testing)
- [7. Kurulum ve Çalıştırma](#7-kurulum-ve-çalıştırma)
- [8. Frontend](#8-frontend)
- [9. Production Notes](#9-production-notes)
- [10. Lisans ve Kullanım Notu](#10-lisans-ve-kullanım-notu)
- [Ek Dokümanlar](#ek-dokümanlar)

## 0. Hızlı Kurulum

### Docker ile (Önerilen)

```bash
# 1) Uygulamayı container ile başlat
# (Flask + Tailwind watch + Webpack watch)
docker compose up -d --build

# 2) Logları takip et
docker compose logs -f flask

# 3) Tüm servisleri kapat
docker compose down
```

### Erişim Adresleri

- Web UI (Frontend): <http://localhost:5040>
- API Base: <http://localhost:5040/api>
- API Örnek Listeleme: <http://localhost:5040/api/cafes>

---

## 1. Kapsam

**Kullanıcı Kimlik Akışı**: Kayıt (`/signup`, `/api/signup`), giriş (`/login`, `/api/login`), çıkış (`/logout`) ve e-posta doğrulama (`/confirm/<token>`) akışları mevcut.

**Rol ve Yetki Yönetimi**: Admin/normal kullanıcı ayrımı var. Admin kullanıcılar kafe CRUD ve moderatör atama/çıkarma işlemlerini yönetebilir.

**Kafe Yönetimi**: Kafe ekleme, güncelleme, silme ve listeleme hem web arayüzünden hem de JSON API üzerinden yapılabilir.

**Moderatör Modeli**: Kullanıcılar belirli kafelere moderatör olarak atanabilir; ilgili kafelerde düzenleme yetkisi kazanırlar.

**Güvenlik Temelleri**:
- Şifreler hashlenerek saklanır (`pbkdf2:sha256`)
- State-changing isteklerde CSRF koruması aktif
- Rich text alanı (`details`) `bleach` ile sanitize edilir

## 2. Teknoloji Yığını (Technology Stack)

| Kategori | Teknoloji / Kütüphane | Kullanım Amacı |
|---|---|---|
| **Backend Core** | Flask 3 | Web uygulaması ve API katmanı |
| **Data Access** | SQLAlchemy, Flask-SQLAlchemy | ORM ve veritabanı işlemleri |
| **Migration** | Alembic, Flask-Migrate | Şema migrasyon altyapısı |
| **Auth & Session** | Flask-Login, Werkzeug Security | Oturum yönetimi ve parola hash doğrulama |
| **Validation / Form** | Flask-WTF, WTForms | Web form doğrulama ve CSRF koruması |
| **Email** | Flask-Mail, itsdangerous | Hesap doğrulama e-postası ve token üretimi |
| **Sanitization** | Bleach | Zengin metin XSS riskini azaltma |
| **Frontend Rendering** | Jinja2 + SolidJS (cutover mode) | Geçişli render stratejisi ve SPA taşıma |
| **Frontend Tooling** | Tailwind CSS, Webpack, Babel, Vite, SolidJS | Stil/JS derleme ve Solid build akışı |
| **Runtime / Deploy** | Gunicorn, Docker, Docker Compose | Üretim sunumu ve container tabanlı çalışma |

## 3. Veritabanı Tasarımı (Database Design)

### 3.1 Entity Listesi

1. **User**: Kullanıcı bilgileri, rol (`is_admin`), doğrulama durumu (`is_confirmed`) ve zaman alanları.
2. **Cafe**: Kafe metadata alanları (konum, imkanlar, fiyat, açıklama vb.).
3. **user_cafe**: User-Cafe many-to-many ilişki tablosu (moderasyon yetkisi için).

### 3.2 Migration ve Şema Yönetimi

Proje `Flask-Migrate` altyapısını içerir; ayrıca geliştirme kolaylığı için `AUTO_CREATE_SCHEMA` desteği bulunur.

- `AUTO_CREATE_SCHEMA=True` olduğunda uygulama açılışında `db.create_all()` çalışır.
- Üretim/staging için migration tabanlı akış önerilir.
- Varsayılan veritabanı URI: `sqlite:///cafes.db`.
- PostgreSQL kullanmak için `SQLALCHEMY_DATABASE_URI` değişkeni override edilmelidir.

## 4. API Tasarımı ve Standartlar (API Design)

Tutarlılık için JSON API cevapları ortak envelope yapısı kullanır:

### 4.1 Response ve Hata Modeli

**Başarılı Cevaplar (Success):**

```json
{
  "data": {
    "cafes": []
  },
  "error": null,
  "meta": {}
}
```

**Hata Cevapları (Error):**

```json
{
  "data": null,
  "error": {
    "message": "Authentication required.",
    "code": "AUTH_REQUIRED",
    "details": null
  },
  "meta": {}
}
```

### 4.2 Endpoint Yüzeyi

**Kafe API**

- `GET /api/cafes`
- `GET /api/cafes/<int:cafe_id>`
- `POST /api/cafes` (admin)
- `PUT /api/cafes/<int:cafe_id>` (admin/moderatör)
- `DELETE /api/cafes/<int:cafe_id>` (admin)

**Kimlik / Kullanıcı API**

- `POST /api/login`
- `POST /api/signup`
- `GET /api/users` (admin)

**Moderasyon Yardımcı Endpointleri**

- `GET /moderated_cafes/<int:user_id>`
- `DELETE /remove_moderator/<int:user_id>/<int:cafe_id>`

**E-posta Onay Endpointi**

- `GET /confirm/<token>`

### 4.3 Güvenlik Semantiği

- API yazma işlemlerinde CSRF koruması aktiftir (`X-CSRFToken` header).
- Kimlik doğrulama session/cookie temellidir (JWT kullanılmıyor).
- Admin kontrolü `api_admin_required`, giriş kontrolü `api_login_required` dekoratörleriyle uygulanır.
- Rich text payload’lar `bleach` ile sanitize edilir.

### 4.4 Sayfalama Notu

- Web tarafında `/cafes?page=` akışı `CAFES_PER_PAGE` ile paginated çalışır.
- API tarafında `/api/cafes` şu an tüm sonuçları döner (pagination henüz uygulanmadı).

## 5. Loglama, İzlenebilirlik ve Hata Yönetimi (Observability)

### 5.1 Hata Modeli Standardizasyonu

`success_response` / `error_response` yardımcılarıyla API hata cevabı tek tipte döndürülür.

### 5.2 CSRF Hata Yönetimi

Global CSRF error handler bulunur:

- `/api/*` isteklerinde JSON hata cevabı (`CSRF_ERROR`) döner.
- Web sayfalarında kullanıcıya flash mesaj gösterilip önceki sayfaya yönlendirilir.

### 5.3 Mevcut Durum ve Geliştirme Alanı

- Structured logging (örn. Serilog benzeri merkezi log altyapısı) henüz yok.
- Trace/correlation id standartı henüz tanımlı değil.
- İleri fazda merkezi loglama + request tracing eklenmesi önerilir.

## 6. Test Stratejisi (Testing)

### 6.1 Mevcut Testler

`tests/test_api_hardening.py` içinde şu alanlar doğrulanır:

- Boş kafe listesi cevabı
- Legacy endpoint’lerin kaldırılmış olması
- CSRF’siz write isteklerinin reddi
- Admin olmayan kullanıcının yetki reddi
- `details` alanı sanitization davranışı
- Duplicate signup ve invalid login senaryoları

### 6.2 Test Komutları

```bash
# Python unittest (package.json script)
npm test

# Doğrudan unittest
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## 7. Kurulum ve Çalıştırma

### 7.1 Gereksinimler

- Python 3.12+
- Node.js LTS + npm
- (Opsiyonel) Docker + Docker Compose

### 7.2 Environment Değişkenleri

`.env` dosyanıza aşağıdaki değerleri ekleyin:

```bash
# App
SECRET_KEY=change-me
SQLALCHEMY_DATABASE_URI=sqlite:///cafes.db
AUTO_CREATE_SCHEMA=False

# Mail
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-mail@example.com
MAIL_PASSWORD=your-password
MAIL_USE_TLS=True
MAIL_USE_SSL=False

# UI / Forms
TINYMCE_API_KEY=
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
CAFES_PER_PAGE=20
COFFEE_CURRENCY_SYMBOL=£

# Frontend cutover
FRONTEND_RENDER_MODE=jinja
SOLID_DIST_DIR=frontend-solid/dist
```

### 7.3 Docker Compose ile Çalıştırma (Önerilen)

```bash
docker compose up -d --build
```

**Servis Erişim Adresleri:**

| Servis | Port | URL |
|---|---|---|
| Flask Web + API | 5040 | <http://localhost:5040> |
| API Örnek | 5040 | <http://localhost:5040/api/cafes> |

### 7.4 Manuel Kurulum

```bash
# 1) Python bağımlılıkları
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2) Node bağımlılıkları
npm install

# 3) Frontend asset watch süreçleri
npx tailwindcss -i ./static/src/css/styles.css -o ./static/dist/css/output.css --watch
npx webpack --watch

# 4) Uygulamayı başlat
flask --app main run --host=0.0.0.0 --port=5040 --debug
```

### 7.5 Uygulama URL’leri

- Home: `http://localhost:5040/`
- Cafes: `http://localhost:5040/cafes`
- Login: `http://localhost:5040/login`
- Admin: `http://localhost:5040/admin`
- API: `http://localhost:5040/api/cafes`

### 7.6 Frontend Render Mode (Jinja / Solid)

Uygulama iki render modunda calisabilir:

- `FRONTEND_RENDER_MODE=jinja`: Legacy Jinja template akisi (default)
- `FRONTEND_RENDER_MODE=solid`: Solid build cikisi (`frontend-solid/dist`) servis edilir

Lokal Solid cutover kontrolu:

```bash
# Solid build al
npm run solid:build

# Solid smoke
FRONTEND_RENDER_MODE=solid flask --app main run --host=0.0.0.0 --port=5040
npm run solid:smoke -- http://127.0.0.1:5040
```

Gorsel regresyon kontrolu (desktop + mobile):

```bash
npm run solid:visual -- http://127.0.0.1:5040
```

Not: Screenshot artefactlari `output/playwright/solid-visual-*` altina yazilir.

Component backlog guncelleme:

```bash
npm run solid:backlog
```

Not: Cikti `frontend-solid/component-backlog.json` dosyasina yazilir.

Rollback kontrolu:

```bash
FRONTEND_RENDER_MODE=jinja flask --app main run --host=0.0.0.0 --port=5040
npm run jinja:smoke -- http://127.0.0.1:5040
```

Tek komutla dry-run:

```bash
npm run frontend:dryrun
```

## 8. Frontend

Frontend katmani su anda **hibrit** durumda calisir: legacy Jinja + yeni SolidJS.

**Template Dosyaları (`templates/`)**

- `index.html`, `cafes.html`, `cafe_detail.html`
- `login.html`, `signup.html`
- `admin_dashboard.html`, `assign_moderator.html`
- `add_cafe.html`, `update_cafe.html`

**Statik Kaynaklar (`static/`)**

- `static/src/css/styles.css` (Tailwind input)
- `static/dist/css/output.css` (derlenmiş çıktı)
- `static/src/scripts/*.js` (kaynak JS)
- `static/dist/js/bundle.js` (Webpack bundle)

**Solid Frontend (`frontend-solid/`)**

- `frontend-solid/src/App.tsx` route tanimlari
- `frontend-solid/src/pages/*` public/auth/admin ekranlari
- `frontend-solid/src/lib/api.ts` ortak API client (timeout + credential policy)
- `frontend-solid/dist/` cutover aninda Flask tarafindan `/solid/*` altinda servis edilir

**Solid UI Notlari**

- Navbar fixed davranisindadir; asagi scroll'da gizlenir, yukari scroll'da tekrar gorunur.
- Header ve footer blur etkisi icin `backdrop-filter` + Firefox fallback katmani uygulanmistir.
- `Kafeler` sayfasinda kullanici gorunumu `Tablo` ve `Grid` modlari arasinda degistirebilir.

## 9. Production Notes

### 9.1 Sunum ve Çalıştırma

- `Procfile` içinde production process: `web: gunicorn main:app`
- Production ortamında `debug` kapalı ve güçlü `SECRET_KEY` zorunlu olmalı.

### 9.2 Veritabanı

- Varsayılan SQLite geliştirme içindir.
- Üretimde PostgreSQL gibi harici bir DB kullanılması önerilir (`SQLALCHEMY_DATABASE_URI`).

### 9.3 Güvenlik Kontrolleri

- `WTF_CSRF_ENABLED=True` bırakılmalı.
- Mail doğrulama akışı açık olmalı (`MAIL_*` değişkenleri).
- Admin hesaplarının parolaları güçlü ve benzersiz tutulmalı.

### 9.4 Hızlı Smoke Kontrol

```bash
curl -fsS http://localhost:5040/ >/dev/null
curl -fsS http://localhost:5040/api/cafes >/dev/null
npm test
npm run frontend:dryrun
npm run solid:visual -- http://127.0.0.1:5040
```

## 10. Lisans ve Kullanım Notu

Bu proje MIT lisansı ile lisanslanmıştır.

- Lisans metni için kök dizindeki [`LICENSE`](LICENSE) dosyasına bakabilirsiniz.
- Üçüncü parti kütüphaneler kendi lisans koşullarına tabidir.

## Ek Dokümanlar

- [Fazlı Checkup Checklist](docs/checkup-fazli-checklist.md)
