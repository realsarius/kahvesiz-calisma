from datetime import datetime, timezone

from flask import request
from flask_login import current_user, login_user
from flask_wtf.csrf import generate_csrf

from kahvesiz_app.api_response import error_response, success_response
from kahvesiz_app.auth import hash_password, send_confirmation_email, verify_password
from kahvesiz_app.extensions import db
from kahvesiz_app.models import User
from kahvesiz_app.repositories import CafeRepository, ModeratorRepository, UserRepository
from kahvesiz_app.security import api_admin_required, api_login_required, user_can_edit_cafe
from kahvesiz_app.services import CafeService, UserService


def register_api_routes(app):
    def _build_moderated_cafes_payload(user):
        return {"cafes": [{"id": cafe.id, "name": cafe.name} for cafe in user.moderated_cafes]}

    def _remove_moderator(user_id, cafe_id):
        user = UserRepository.get_by_id(user_id)
        if not user:
            return error_response("User not found", status=404, code="USER_NOT_FOUND")

        cafe = CafeRepository.get_by_id(cafe_id)
        if not cafe:
            return error_response("Cafe not found", status=404, code="CAFE_NOT_FOUND")

        removed = ModeratorRepository.remove(user, cafe)
        if not removed:
            return error_response(
                "Cafe is not moderated by this user",
                status=400,
                code="MODERATION_NOT_FOUND",
            )
        return success_response({"success": True}, status=200)

    @app.route("/remove_moderator/<int:user_id>/<int:cafe_id>", methods=["DELETE"])
    @api_admin_required
    def remove_moderator(user_id, cafe_id):
        return _remove_moderator(user_id, cafe_id)

    @app.route("/api/moderators", methods=["POST"])
    @api_admin_required
    def api_assign_moderator():
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        cafe_id = data.get("cafe_id")

        if not user_id or not cafe_id:
            return error_response(
                "user_id and cafe_id are required",
                status=422,
                code="MISSING_FIELDS",
                details=["user_id", "cafe_id"],
            )

        try:
            user_id = int(user_id)
            cafe_id = int(cafe_id)
        except (TypeError, ValueError):
            return error_response("Invalid moderator assignment payload", status=422, code="INVALID_BODY")

        user = UserRepository.get_by_id(user_id)
        if not user:
            return error_response("User not found", status=404, code="USER_NOT_FOUND")

        cafe = CafeRepository.get_by_id(cafe_id)
        if not cafe:
            return error_response("Cafe not found", status=404, code="CAFE_NOT_FOUND")

        assigned = ModeratorRepository.assign(user, cafe)
        if not assigned:
            return success_response({"assigned": False, "message": "User is already a moderator."}, status=200)

        return success_response({"assigned": True, "message": "Moderator assigned successfully."}, status=201)

    @app.route("/api/moderators/<int:user_id>/<int:cafe_id>", methods=["DELETE"])
    @api_admin_required
    def api_remove_moderator(user_id, cafe_id):
        return _remove_moderator(user_id, cafe_id)

    @app.route("/moderated_cafes/<int:user_id>", methods=["GET"])
    @api_login_required
    def get_moderated_cafes(user_id):
        if not current_user.is_admin and current_user.id != user_id:
            return error_response(
                "You do not have permission to access this data.",
                status=403,
                code="FORBIDDEN",
            )

        user = UserRepository.get_by_id(user_id)
        if not user:
            return error_response("User not found", status=404, code="USER_NOT_FOUND")

        return success_response(_build_moderated_cafes_payload(user), status=200)

    @app.route("/api/moderators/<int:user_id>", methods=["GET"])
    @api_login_required
    def api_get_moderated_cafes(user_id):
        if not current_user.is_admin and current_user.id != user_id:
            return error_response(
                "You do not have permission to access this data.",
                status=403,
                code="FORBIDDEN",
            )

        user = UserRepository.get_by_id(user_id)
        if not user:
            return error_response("User not found", status=404, code="USER_NOT_FOUND")

        return success_response(_build_moderated_cafes_payload(user), status=200)

    @app.route("/api/cafes/<int:cafe_id>", methods=["PUT"])
    @api_login_required
    def api_update_cafe(cafe_id):
        data = request.get_json(silent=True)
        if not data:
            return error_response("No JSON data provided", status=400, code="INVALID_BODY")

        missing_fields = CafeService.validate_payload(data)
        if missing_fields:
            return error_response(
                "Missing fields",
                status=400,
                code="MISSING_FIELDS",
                details=missing_fields,
            )

        cafe = CafeRepository.get_by_id(cafe_id)
        if not cafe:
            return error_response("Cafe not found", status=404, code="CAFE_NOT_FOUND")

        if not user_can_edit_cafe(current_user, cafe):
            return error_response(
                "You do not have permission to update this cafe.",
                status=403,
                code="FORBIDDEN",
            )

        if CafeRepository.exists_by_name_except_id(data["name"], cafe_id):
            return error_response(
                "A cafe with this name already exists. Please choose a different name.",
                status=409,
                code="CAFE_NAME_EXISTS",
            )

        CafeService.apply_payload(cafe, data)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return error_response("Database error while updating cafe", status=500, code="DB_ERROR")

        return success_response({"message": "Cafe updated successfully!"}, status=200)

    @app.route("/api/cafes/<int:cafe_id>", methods=["DELETE"])
    @api_admin_required
    def api_delete_cafe(cafe_id):
        cafe = CafeRepository.get_by_id(cafe_id)
        if not cafe:
            return error_response("Cafe not found", status=404, code="CAFE_NOT_FOUND")

        try:
            CafeRepository.delete(cafe)
        except Exception:
            db.session.rollback()
            return error_response("Database error while deleting cafe", status=500, code="DB_ERROR")

        return success_response({"message": "Cafe deleted successfully!"}, status=200)

    @app.route("/api/cafes", methods=["POST"])
    @api_admin_required
    def api_add_cafe():
        data = request.get_json(silent=True)
        if not data:
            return error_response("No JSON data provided", status=400, code="INVALID_BODY")

        missing_fields = CafeService.validate_payload(data)
        if missing_fields:
            return error_response(
                "Missing fields",
                status=400,
                code="MISSING_FIELDS",
                details=missing_fields,
            )

        if CafeRepository.get_by_name(data["name"]):
            return error_response(
                "A cafe with this name already exists. Please choose a different name.",
                status=409,
                code="CAFE_NAME_EXISTS",
            )

        cafe = CafeService.new_from_payload(data)
        try:
            CafeRepository.add(cafe)
        except Exception:
            db.session.rollback()
            return error_response("Database error while creating cafe", status=500, code="DB_ERROR")

        return success_response({"message": "Cafe added successfully!"}, status=201)

    @app.route("/api/cafes/<int:cafe_id>", methods=["GET"])
    def get_cafe(cafe_id):
        cafe = CafeRepository.get_by_id(cafe_id)
        if not cafe:
            return error_response("Cafe not found", status=404, code="CAFE_NOT_FOUND")
        return success_response(CafeService.serialize(cafe), status=200)

    @app.route("/api/cafes", methods=["GET"])
    def get_all_cafes():
        search_query = request.args.get("search", "").strip()
        try:
            cafes = CafeRepository.list_all(search_query=search_query)
        except Exception:
            return error_response("An error occurred while retrieving cafes", status=500, code="DB_ERROR")

        payload = {"cafes": [CafeService.serialize(cafe) for cafe in cafes]}
        return success_response(payload, status=200)

    @app.route("/api/login", methods=["POST"])
    def api_login():
        data = request.get_json(silent=True) or {}
        email = data.get("email")
        password = data.get("password")

        if not email:
            return error_response("E-posta adresi gerekli.", status=422, code="EMAIL_REQUIRED")
        if not password:
            return error_response("Şifre gerekli.", status=422, code="PASSWORD_REQUIRED")

        user = UserRepository.get_by_email(email)
        if not user or not verify_password(user.password, password):
            return error_response(
                "Geçersiz e-posta adresi veya şifre.",
                status=401,
                code="INVALID_CREDENTIALS",
            )
        if not user.is_confirmed:
            return error_response(
                "Hesabınızı doğrulamanız gerekiyor.",
                status=403,
                code="EMAIL_NOT_CONFIRMED",
            )

        login_user(user)
        return success_response({"message": "Giriş başarılı!"}, status=200)

    @app.route("/api/csrf-token", methods=["GET"])
    def api_csrf_token():
        return success_response({"csrf_token": generate_csrf()}, status=200)

    @app.route("/api/auth/session", methods=["GET"])
    @api_login_required
    def api_auth_session():
        return success_response(
            {
                "user": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "email": current_user.email,
                    "is_admin": bool(current_user.is_admin),
                }
            },
            status=200,
        )

    @app.route("/api/signup", methods=["POST"])
    def api_signup():
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name:
            return error_response("İsim gerekli.", status=422, code="NAME_REQUIRED")
        if not email:
            return error_response("E-posta adresi gerekli.", status=422, code="EMAIL_REQUIRED")
        if not password:
            return error_response("Şifre gerekli.", status=422, code="PASSWORD_REQUIRED")
        if len(password) < 8:
            return error_response("Şifre en az 8 karakter olmalı.", status=422, code="PASSWORD_TOO_SHORT")

        if UserRepository.get_by_email(email):
            return error_response("E-posta adresi zaten kullanımda.", status=409, code="EMAIL_ALREADY_EXISTS")

        new_user = User(
            name=name,
            email=email,
            password=hash_password(password),
            is_admin=False,
            is_confirmed=False,
        )
        UserRepository.add(new_user)
        send_confirmation_email(email)

        return success_response(
            {"message": "Hesabınız başarıyla oluşturuldu! Lütfen e-posta adresinizi doğrulayın."},
            status=201,
        )

    @app.route("/api/users", methods=["GET"])
    @api_admin_required
    def get_all_users():
        search_query = request.args.get("search", "").strip()
        try:
            users = UserRepository.list_all(search_query=search_query)
        except Exception:
            return error_response("An error occurred while retrieving users", status=500, code="DB_ERROR")

        payload = {"users": [UserService.serialize(user) for user in users]}
        return success_response(payload, status=200)

    @app.route("/confirm/<token>")
    def confirm_email(token):
        from kahvesiz_app.auth import verify_verification_token
        from flask import flash, redirect, url_for

        email = verify_verification_token(token)
        if email is None:
            flash("Onaylama bağlantısı geçersiz veya süresi dolmuş.", "danger")
            return redirect(url_for("signup"))

        user = UserRepository.get_by_email(email)
        if not user:
            flash("Kullanıcı bulunamadı.", "danger")
            return redirect(url_for("signup"))

        if user.is_confirmed:
            flash("Hesap zaten onaylanmış. Lütfen giriş yapın.", "success")
        else:
            user.is_confirmed = True
            user.confirmed_on = datetime.now(timezone.utc)
            db.session.commit()
            flash("Hesabınız onaylandı! Şimdi giriş yapabilirsiniz.", "success")

        return redirect(url_for("login"))
