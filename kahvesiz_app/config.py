import os


def get_env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_env_int(name, default):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def load_app_config():
    return {
        "SQLALCHEMY_DATABASE_URI": os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///cafes.db"),
        "SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-key-change-me"),
        "MAIL_SERVER": os.getenv("MAIL_SERVER"),
        "MAIL_PORT": get_env_int("MAIL_PORT", 587),
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME"),
        "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD"),
        "MAIL_USE_TLS": get_env_bool("MAIL_USE_TLS", True),
        "MAIL_USE_SSL": get_env_bool("MAIL_USE_SSL", False),
        "WTF_CSRF_ENABLED": get_env_bool("WTF_CSRF_ENABLED", True),
        "WTF_CSRF_TIME_LIMIT": get_env_int("WTF_CSRF_TIME_LIMIT", 3600),
        "TINYMCE_API_KEY": os.getenv("TINYMCE_API_KEY", ""),
        "CAFES_PER_PAGE": get_env_int("CAFES_PER_PAGE", 20),
        "COFFEE_CURRENCY_SYMBOL": os.getenv("COFFEE_CURRENCY_SYMBOL", "£"),
        "AUTO_CREATE_SCHEMA": get_env_bool("AUTO_CREATE_SCHEMA", False),
    }

