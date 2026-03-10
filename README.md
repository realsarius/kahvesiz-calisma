# Kahvesiz Çalisma

Kafelerde laptop ile calisma deneyimini degerlendirmek icin gelistirilmis bir Flask uygulamasi.
Uygulama, kafe detaylarini listeleme/arama, kullanici kayit-giris, moderator ve admin yonetimi gibi akislari icerir.

## Proje Yapisi

- `main.py`: Flask uygulamasi, route'lar ve is kurallari
- `forms.py`: WTForms tanimlari
- `templates/`: Jinja2 template dosyalari
- `static/src/scripts/`: frontend JavaScript dosyalari
- `static/src/css/`: kaynak CSS
- `static/dist/`: build ciktisi (`bundle.js`, `output.css`)

## Gereksinimler

- Python 3.12+
- Node.js 18+ ve npm
- (Opsiyonel) Docker + Docker Compose

## Ortam Degiskenleri

Asagidaki degiskenleri `.env` dosyasinda tanimlayin:

```env
SECRET_KEY=change-me
SQLALCHEMY_DATABASE_URI=sqlite:///cafes.db
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-mail@example.com
MAIL_PASSWORD=your-password
MAIL_USE_TLS=True
MAIL_USE_SSL=False
TINYMCE_API_KEY=your-tinymce-key
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
CAFES_PER_PAGE=20
COFFEE_CURRENCY_SYMBOL=£
AUTO_CREATE_SCHEMA=False
```

Not: `AUTO_CREATE_SCHEMA=False` ile migration tabanli akış tavsiye edilir.

## Lokal Gelistirme Kurulumu

1. Python bagimliliklarini kurun:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Node bagimliliklarini kurun:

```bash
npm install
```

3. Frontend build sureclerini calistirin:

```bash
npx tailwindcss -i ./static/src/css/styles.css -o ./static/dist/css/output.css --watch
npx webpack --watch
```

4. Flask uygulamasini baslatin:

```bash
flask --app main run --host=0.0.0.0 --port=5000 --debug
```

## Docker ile Calistirma

```bash
docker compose up --build
```

Servisler:
- `flask`: uygulama sunucusu
- `tailwind`: CSS watch
- `webpack`: JS bundle watch

## API Ozeti

- `GET /api/cafes`: tum kafeleri listeler (opsiyonel `search`)
- `GET /api/cafes/<id>`: tek kafe detayi
- `POST /api/cafes`: yeni kafe ekler (admin)
- `PUT /api/cafes/<id>`: kafe gunceller (admin veya moderator)
- `DELETE /api/cafes/<id>`: kafe siler (admin)
- `POST /api/login`: API tabanli giris
- `POST /api/signup`: API tabanli kayit

## Ekran Goruntuleri

![ss1](https://github.com/realsarius/kahvesiz-calisma/blob/main/static/src/assets/screenshots/ss1.png?raw=true)
![ss2](https://github.com/realsarius/kahvesiz-calisma/blob/main/static/src/assets/screenshots/ss2.png?raw=true)
![ss3](https://github.com/realsarius/kahvesiz-calisma/blob/main/static/src/assets/screenshots/ss3.png?raw=true)
![ss4](https://github.com/realsarius/kahvesiz-calisma/blob/main/static/src/assets/screenshots/ss4.png?raw=true)
![ss5](https://github.com/realsarius/kahvesiz-calisma/blob/main/static/src/assets/screenshots/ss5.png?raw=true)
![ss6](https://github.com/realsarius/kahvesiz-calisma/blob/main/static/src/assets/screenshots/ss6.png?raw=true)

## Lisans

MIT
