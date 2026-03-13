import json
from pathlib import Path

from flask import (
    abort,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from forms import CafeForm, ContactForm, UserForm
from kahvesiz_app.auth import hash_password, send_confirmation_email, verify_password
from kahvesiz_app.models import User
from kahvesiz_app.repositories import CafeRepository, ModeratorRepository, UserRepository
from kahvesiz_app.security import admin_required, user_can_edit_cafe
from kahvesiz_app.services import CafeService, parse_positive_int


def register_web_routes(app):
    solid_exact_paths = {
        "/",
        "/index",
        "/about",
        "/privacy",
        "/license",
        "/contact",
        "/contact_us",
        "/login",
        "/signup",
        "/admin",
        "/cafes",
    }

    def _is_solid_mode_enabled():
        return current_app.config.get("FRONTEND_RENDER_MODE") == "solid"

    def _solid_dist_dir():
        configured_dist_dir = current_app.config.get("SOLID_DIST_DIR", "frontend-solid/dist")
        dist_dir = Path(configured_dist_dir)
        if not dist_dir.is_absolute():
            dist_dir = Path(current_app.root_path) / dist_dir
        return dist_dir

    def _solid_auth_bootstrap_payload():
        if not current_user.is_authenticated:
            return {"user": None, "isAuthenticated": False}

        return {
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "isAdmin": bool(current_user.is_admin),
            },
            "isAuthenticated": True,
        }

    def _json_for_inline_script(payload):
        raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        return (
            raw_json.replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )

    def _render_solid_entry(dist_dir):
        index_file = dist_dir / "index.html"
        if not index_file.exists() or not index_file.is_file():
            return None

        index_html = index_file.read_text(encoding="utf-8")
        bootstrap_payload = _json_for_inline_script(_solid_auth_bootstrap_payload())
        bootstrap_script = f"<script>window.__KAHVESIZ_AUTH__={bootstrap_payload};</script>"

        if "</head>" in index_html:
            index_html = index_html.replace("</head>", f"{bootstrap_script}</head>", 1)
        else:
            index_html = f"{bootstrap_script}{index_html}"

        response = make_response(index_html, 200)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    def _should_serve_solid_for_path(path):
        normalized = path.rstrip("/") or "/"
        if normalized in solid_exact_paths:
            return True
        return normalized.startswith("/cafes/")

    def _maybe_render_solid_entry():
        if request.method != "GET" or not _is_solid_mode_enabled():
            return None

        if not _should_serve_solid_for_path(request.path):
            return None

        dist_dir = _solid_dist_dir()
        return _render_solid_entry(dist_dir)

    @app.route("/solid/<path:filename>")
    def solid_asset(filename):
        if not _is_solid_mode_enabled():
            abort(404)

        dist_dir = _solid_dist_dir()
        target_file = dist_dir / filename
        if not target_file.exists() or not target_file.is_file():
            abort(404)

        return send_from_directory(str(dist_dir), filename)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Çıkış yaptınız.", "info")
        return redirect(url_for("home"))

    @app.route("/admin/assign_moderator", methods=["GET", "POST"])
    @login_required
    @admin_required
    def assign_moderator_page():
        if request.method == "POST":
            user_id = request.form.get("user_id")
            cafe_id = request.form.get("cafe_id")

            user = UserRepository.get_by_id(int(user_id)) if user_id else None
            cafe = CafeRepository.get_by_id(int(cafe_id)) if cafe_id else None
            if not user or not cafe:
                flash("User or Cafe not found", "danger")
            else:
                ModeratorRepository.assign(user, cafe)
                flash("Moderator assigned successfully!", "success")

        users = UserRepository.list_all()
        cafes = CafeRepository.list_all()
        return render_template("admin_dashboard.html", users=users, cafes=cafes)

    @app.route("/cafes/update/<int:cafe_id>", methods=["GET", "POST"])
    @login_required
    def update_cafe(cafe_id):
        cafe = CafeRepository.get_by_id(cafe_id)
        if not cafe:
            return redirect(url_for("cafes"))
        if not user_can_edit_cafe(current_user, cafe):
            flash("Bu kafe için düzenleme yetkiniz yok.", "danger")
            return redirect(url_for("cafe_detail", cafe_id=cafe.id))

        form = CafeForm(obj=cafe)
        if form.validate_on_submit():
            cafe.name = form.name.data
            cafe.map_url = form.map_url.data
            cafe.img_url = form.img_url.data
            cafe.location = form.location.data
            cafe.has_sockets = form.has_sockets.data
            cafe.has_toilet = form.has_toilet.data
            cafe.has_wifi = form.has_wifi.data
            cafe.can_take_calls = form.can_take_calls.data
            cafe.seats = form.seats.data
            cafe.coffee_price = CafeService.normalize_coffee_price(form.coffee_price.data)
            cafe.details = CafeService.sanitize_rich_text(form.details.data)
            try:
                from kahvesiz_app.extensions import db

                db.session.commit()
                flash("Cafe updated successfully!", "success")
                return redirect(url_for("cafes"))
            except Exception as e:
                from kahvesiz_app.extensions import db

                db.session.rollback()
                flash(f"An error occurred: {e}", "error")

        return render_template(
            "update_cafe.html",
            form=form,
            cafe=cafe,
            tinymce_api_key=current_app.config["TINYMCE_API_KEY"],
        )

    @app.route("/add_cafe", methods=["GET", "POST"])
    @login_required
    @admin_required
    def add_cafe():
        form = CafeForm()
        if form.validate_on_submit():
            cafe = CafeService.new_from_payload(
                {
                    "name": form.name.data,
                    "map_url": form.map_url.data,
                    "img_url": form.img_url.data,
                    "location": form.location.data,
                    "has_sockets": form.has_sockets.data,
                    "has_toilet": form.has_toilet.data,
                    "has_wifi": form.has_wifi.data,
                    "can_take_calls": form.can_take_calls.data,
                    "seats": form.seats.data,
                    "coffee_price": form.coffee_price.data,
                    "details": form.details.data,
                }
            )
            try:
                CafeRepository.add(cafe)
                flash("Cafe added successfully!", "success")
                return redirect(url_for("home"))
            except Exception as e:
                from kahvesiz_app.extensions import db

                db.session.rollback()
                flash(f"An error occurred while adding the cafe: {e}", "error")
        elif request.method == "POST":
            flash("Form doğrulaması başarısız. Lütfen alanları kontrol edin.", "error")

        return render_template(
            "add_cafe.html",
            form=form,
            tinymce_api_key=current_app.config["TINYMCE_API_KEY"],
        )

    @app.route("/cafes", methods=["GET"])
    def cafes():
        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry

        try:
            page = parse_positive_int(request.args.get("page", 1), 1)
            per_page = current_app.config["CAFES_PER_PAGE"]
            pagination = CafeRepository.paginate(page=page, per_page=per_page)
            return render_template(
                "cafes.html",
                cafes=pagination.items,
                total_pages=pagination.pages,
                current_page=page,
            )
        except Exception:
            return render_template("cafes.html", cafes=[], error="An error occurred while retrieving cafes.")

    @app.route("/contact_us", methods=["GET", "POST"])
    def contact_us():
        if request.method == "GET":
            solid_entry = _maybe_render_solid_entry()
            if solid_entry:
                return solid_entry

        form = ContactForm()
        if form.validate_on_submit():
            flash("Your message has been sent successfully!", "success")
            return redirect(url_for("contact_us"))
        return render_template("contact_us.html", form=form)

    @app.route("/contact", methods=["GET"])
    def contact():
        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry
        return redirect(url_for("contact_us"))

    @app.route("/cafes/<int:cafe_id>")
    def cafe_detail(cafe_id):
        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry

        cafe = CafeRepository.get_by_id(cafe_id)
        if not cafe:
            return render_template("cafe_detail.html", cafe=None, error="Cafe not found.")
        return render_template("cafe_detail.html", cafe=CafeService.serialize(cafe))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry

        form = UserForm()
        if form.validate_on_submit():
            user = UserRepository.get_by_email(form.email.data)
            if user and verify_password(user.password, form.password.data):
                if user.is_confirmed:
                    login_user(user)
                    flash("Giriş başarılı! Ana sayfaya yönlendiriliyorsunuz.", "success")
                    return redirect(url_for("home"))
                flash(
                    "E-posta adresinizi doğrulamanız gerekiyor. Lütfen e-posta adresinizi kontrol edin.",
                    "warning",
                )
            else:
                flash("Geçersiz e-posta adresi veya şifre.", "danger")

        return render_template("login.html", form=form)

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry

        form = UserForm()
        if form.validate_on_submit():
            if UserRepository.get_by_email(form.email.data):
                flash("Email kullanılmakta.", "danger")
                return redirect(url_for("signup"))

            if len(form.password.data) < 8:
                flash("Şifre en az 8 karakter olmalı.", "danger")
                return redirect(url_for("signup"))

            new_user = UserRepository.add(
                User(
                    name=form.name.data,
                    email=form.email.data,
                    password=hash_password(form.password.data),
                    is_admin=False,
                    is_confirmed=False,
                )
            )
            send_confirmation_email(new_user.email)
            flash("Hesabınız başarıyla oluşturuldu! Lütfen e-posta adresinizi doğrulayın.", "success")
            return redirect(url_for("login"))

        return render_template("signup.html", form=form)

    @app.route("/about")
    def about():
        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry
        return render_template("about.html")

    @app.route("/privacy")
    def privacy():
        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry
        return render_template("privacy.html")

    @app.route("/license")
    def license():
        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry
        return render_template("license.html")

    @app.route("/index")
    @app.route("/")
    def home():
        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry
        return render_template("index.html")

    @app.route("/admin")
    @login_required
    @admin_required
    def admin_dashboard():
        solid_entry = _maybe_render_solid_entry()
        if solid_entry:
            return solid_entry
        return render_template("admin_dashboard.html")
