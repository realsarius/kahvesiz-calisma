from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

from kahvesiz_app.api_response import error_response


def user_can_edit_cafe(user, cafe):
    return user.is_authenticated and (user.is_admin or user.is_moderator_of(cafe.id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)

    return decorated_function


def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return error_response("Authentication required.", status=401, code="AUTH_REQUIRED")
        return f(*args, **kwargs)

    return decorated_function


def api_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return error_response("Authentication required.", status=401, code="AUTH_REQUIRED")
        if not current_user.is_admin:
            return error_response("Admin access required.", status=403, code="ADMIN_REQUIRED")
        return f(*args, **kwargs)

    return decorated_function

