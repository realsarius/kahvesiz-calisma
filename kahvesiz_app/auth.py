import itsdangerous
from flask import current_app, url_for
from flask_mail import Message
from werkzeug.security import check_password_hash, generate_password_hash

from kahvesiz_app.extensions import mail


def _serializer():
    return itsdangerous.URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_verification_token(email):
    return _serializer().dumps(email, salt="email-confirm")


def verify_verification_token(token, expiration=3600):
    try:
        return _serializer().loads(token, salt="email-confirm", max_age=expiration)
    except (itsdangerous.SignatureExpired, itsdangerous.BadSignature):
        return None


def send_confirmation_email(user_email):
    token = generate_verification_token(user_email)
    confirm_url = url_for("confirm_email", token=token, _external=True)
    msg = Message(
        "Please confirm your email",
        sender=current_app.config["MAIL_USERNAME"],
        recipients=[user_email],
    )
    msg.body = f"Your link is {confirm_url}"
    mail.send(msg)


def hash_password(password):
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(hashed_password, plain_password):
    return check_password_hash(hashed_password, plain_password)

