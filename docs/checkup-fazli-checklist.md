# Kahvesiz Calisma - Fazli Teknik Checkup Checklist

Tarih: 10 Mart 2026
Kapsam: Backend (Flask/Python), Frontend (Template + JS), NPM bagimliliklari, guvenlik, SOLID/REST/Clean/DRY, hardcoded degerler.

## Faz 0 - Kritik Guvenlik ve Erisim Kontrolu (Once)

- [x] `api_update_cafe`, `api_add_cafe`, `api_delete_cafe` endpointlerine yetki kontrolu ekle (`@login_required` + rol kontrolu).
  - Kanit: `main.py:268`, `main.py:356`, `main.py:373`
  - Risk: Giris yapmamis/izinsiz kullanici veri degistirebilir/silebilir.

- [x] `update_cafe` sayfasinda yalnizca admin veya ilgili moderatorun guncelleme yapabildigini backend tarafinda da zorunlu kil.
  - Kanit: `main.py:244-266`
  - Risk: UI gizlense bile URL ile yetkisiz erisim mümkün.

- [x] XSS riskini kapat: `cafe.details | safe` kullanimi icin server-side sanitize uygula (izinli tag listesi ile).
  - Kanit: `templates/cafe_detail.html:361`
  - Risk: Kalici (stored) XSS.
  - Not: Ilk adimda `|safe` kaldirilarak HTML render kapatildi; whitelist sanitize sonraki adimda zengin metin ihtiyacina gore eklenebilir.

- [x] API/JS tarafinda `innerHTML` ile dinamik veri basilan yerlerde escape/sanitize uygula.
  - Kanit: `static/src/scripts/cafes.js:43`, `static/src/scripts/admin_dashboard.js:49`, `static/src/scripts/admin_dashboard.js:81`
  - Risk: DOM XSS.

- [ ] JSON endpointlerinde CSRF stratejisi netlestir (cookie tabanli session kullaniminda kritik).
  - Kanit: `api_*` endpointleri JSON aliyor, global CSRF korumasi yok.
  - Not: `update_cafe.js` token gonderiyor ama backendde dogrulama gorunmuyor.

## Faz 1 - REST API Sozlesmesi ve Davranis Tutarliligi

- [ ] Endpoint isimlerini REST'e uygun hale getir (fiil degil kaynak odakli).
  - Su an: `/api/add_cafe`, `/api/update_cafe/<id>`, `/api/delete_cafe/<id>`
  - Oneri: `/api/cafes` (POST), `/api/cafes/<id>` (PUT/PATCH/DELETE)
  - Kanit: `main.py:268`, `main.py:356`, `main.py:373`

- [ ] Bos liste donuslerini 404 yerine 200 + bos dizi olacak sekilde standardize et.
  - Kanit: `main.py:470-471`, `main.py:683-684`
  - Risk: Frontend kosullari karmasiklasir, API kontrati zayiflar.

- [ ] Hata kodlarini semantik olarak duzelt (`401/403/404/409/422` ayrimi).
  - Ornek: login hatasinda 400 yerine 401/403 degerlendir.
  - Kanit: `main.py:537`

- [ ] API response formatini standardize et (`data`, `error`, `meta` gibi tek bicim).
  - Kanit: API'lerde farkli donus formatlari mevcut.

## Faz 2 - Hardcoded Degerler ve Konfigurasyon

- [ ] Veritabani baglantisini hardcoded `sqlite:///cafes.db` yerine ortam degiskeniyle yonet.
  - Kanit: `main.py:22`

- [ ] Uygulamanin kendi API'sine `http://localhost:5000` ile HTTP cagrisi yapma; dogrudan servis/repository katmanini kullan.
  - Kanit: `main.py:482`, `main.py:510`
  - Risk: Ortama bagli kirilganlik, gereksiz network overhead.

- [ ] `MAIL_PORT` ve benzeri config alanlarinda fail-safe default/validasyon ekle.
  - Kanit: `main.py:25`
  - Risk: Env yoksa app acilisinda crash.

- [ ] Para birimi sembolunu hardcoded (`"£"`) yerine ayarlanabilir config/data model'e tasi.
  - Kanit: `main.py:339`, `main.py:400`

- [ ] `per_page = 20` gibi sabitleri merkezi ayarlara tasi.
  - Kanit: `main.py:481`

## Faz 3 - SOLID, Clean, DRY Refactor Altyapisi

- [ ] `main.py` icindeki tek dosyada toplu sorumluluklari katmanlara ayir.
  - Kanit: `main.py` 719 satir; route + is kurali + DB + mail + auth tek yerde.
  - Oneri: `routes/`, `services/`, `repositories/`, `schemas/`, `auth/` ayirimi.

- [ ] Tekrarlanan is kurallarini ortak fonksiyon/servise cek.
  - Kanit: cafe ekleme/guncelleme alan mapleme tekrari (`main.py:288-299`, `main.py:390-402`)
  - Kanit: login/signup API + web route tarafinda benzer dogrulama akislari (`main.py:521+`, `main.py:540+`, `main.py:576+`, `main.py:606+`)

- [ ] DB transactionlari tek commit ve tutarli hata yonetimi ile sadeleştir.
  - Kanit: `assign_moderator` icinde cift commit (`main.py:185`, `main.py:189`)

- [ ] Tarih defaultlarindaki bug'i duzelt: callable kullan.
  - Kanit: `Cafe.created_at` ve `Cafe.updated_at` degerleri anlik degil import aninda hesaplanmis (`main.py:134-136`)
  - Risk: Tum kayitlarda ayni/yanlis timestamp davranisi.

- [ ] `db.create_all()` kullanimini migration akisindan ayir.
  - Kanit: `main.py:168-169`
  - Risk: migration ile drift/cakisma.

## Faz 4 - Frontend Kod Kalitesi ve Guvenlik

- [x] Admin panelde tanimsiz fonksiyon cagri referanslarini temizle veya implement et.
  - Kanit: `onclick="editUser(...)"`, `deleteUser`, `editCafe`, `deleteCafe` referanslari kaldirildi.
  - Kanit dosya: `static/src/scripts/admin_dashboard.js`

- [ ] Form validasyonunu sadece frontendde degil backendde de zorunlu tut.
  - Kanit: `add_cafe` route'unda `validate_on_submit()` yerine sadece method kontrolu var (`main.py:316`)

- [ ] `request.json` null gelebilecek API'lerde guvenli parse + erken validasyon ekle.
  - Kanit: `main.py:523`, `main.py:578`
  - Risk: `NoneType` hatasiyla 500.

## Faz 5 - NPM Bagimlilik ve Build Zinciri (10 Mart 2026)

Calistirilan komutlar:
- `npm install`
- `npm audit --json`
- `npm query "[deprecated]" --json`
- `npm outdated --long`

Sonuc:
- [ ] 12 zafiyet var: `1 low`, `6 moderate`, `5 high`.
- [ ] Dogrudan etkilenen paket: `webpack` (mevcut: `5.93.0`, istenen/guvenli hat: `5.105.4`).
- [ ] Transitif riskli paketler: `terser-webpack-plugin`, `serialize-javascript`, `minimatch`, `glob`, `cross-spawn`, `ajv`, `micromatch`, `nanoid`, `@babel/helpers`, `@babel/runtime`, `brace-expansion`.
- [x] Deprecated paket tespiti: yok (`npm query` sonucu bos liste).

Yapilacaklar:
- [ ] `npm audit fix` (kontrollu) + lockfile degisikligi inceleme.
- [ ] Gerekirse major gecisler icin manuel update + build regresyon testi.
- [ ] `webpack` ve `babel` paketlerini hedeflenen surume cekip tekrar audit al.

## Faz 6 - Smoke Test Oncesi Minimum Kabul Kriteri

- [ ] Yetkisiz kullanici `POST/PUT/DELETE /api/cafes*` cagrilarinda 401/403 aliyor.
- [ ] `cafe.details` icine script eklenince sanitize ediliyor, JS calismiyor.
- [ ] `GET /api/cafes` bos durumda 200 + `[]` (veya `{ cafes: [] }`) donuyor.
- [ ] `cafes` sayfasi local API'ye HTTP yerine dogrudan servisle veri cekiyor.
- [ ] `npm audit` sonucu kritik/yuksek riskler kapatildi veya bilincli istisna dokumante edildi.

---

## Notlar

- Bu dokuman sadece checkup bulgulari ve fazli aksiyon listesidir.
- Kod degisikligi bu asamada yapilmadi.
