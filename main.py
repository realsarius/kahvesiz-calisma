from dotenv import load_dotenv
from flask import Flask, flash, redirect, request, url_for
from flask_wtf.csrf import CSRFError, generate_csrf

from kahvesiz_app.api_response import error_response
from kahvesiz_app.config import load_app_config
from kahvesiz_app.extensions import csrf, db, login_manager, mail, migrate
from kahvesiz_app.repositories import UserRepository
from kahvesiz_app.routes_api import register_api_routes
from kahvesiz_app.routes_web import register_web_routes


load_dotenv()

app = Flask(__name__)
app.config.update(load_app_config())

db.init_app(app)
migrate.init_app(app, db, render_as_batch=True)
mail.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

# Models must be imported after db init to register metadata.
from kahvesiz_app.models import User  # noqa: E402


@login_manager.user_loader
def load_user(user_id):
    return UserRepository.get_by_id(int(user_id))


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": generate_csrf}


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    if request.path.startswith("/api/"):
        return error_response("CSRF token missing or invalid.", status=400, code="CSRF_ERROR")
    flash("CSRF doğrulaması başarısız. Lütfen tekrar deneyin.", "danger")
    return redirect(request.referrer or url_for("home"))


register_api_routes(app)
register_web_routes(app)

if app.config["AUTO_CREATE_SCHEMA"]:
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    app.run(debug=False, port=5040)
