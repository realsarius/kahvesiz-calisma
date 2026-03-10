import bleach
from flask import current_app

from kahvesiz_app.models import Cafe


class CafeService:
    REQUIRED_FIELDS = [
        "name",
        "map_url",
        "img_url",
        "location",
        "has_sockets",
        "has_toilet",
        "has_wifi",
        "can_take_calls",
        "seats",
        "coffee_price",
    ]

    @staticmethod
    def normalize_coffee_price(raw_price):
        symbol = current_app.config["COFFEE_CURRENCY_SYMBOL"]
        value = str(raw_price or "").strip()
        if not value:
            return value
        if value.startswith(symbol):
            return value
        return f"{symbol}{value}"

    @staticmethod
    def sanitize_rich_text(value):
        if not value:
            return None
        allowed_tags = [
            "p",
            "br",
            "strong",
            "em",
            "u",
            "ul",
            "ol",
            "li",
            "blockquote",
            "code",
            "pre",
            "a",
            "h1",
            "h2",
            "h3",
            "h4",
        ]
        allowed_attributes = {"a": ["href", "title", "target", "rel"]}
        allowed_protocols = ["http", "https", "mailto"]
        return bleach.clean(
            str(value),
            tags=allowed_tags,
            attributes=allowed_attributes,
            protocols=allowed_protocols,
            strip=True,
        )

    @classmethod
    def validate_payload(cls, data):
        missing = [field for field in cls.REQUIRED_FIELDS if field not in data]
        return missing

    @classmethod
    def apply_payload(cls, cafe, data):
        cafe.name = data["name"]
        cafe.map_url = data["map_url"]
        cafe.img_url = data["img_url"]
        cafe.location = data["location"]
        cafe.has_sockets = data["has_sockets"]
        cafe.has_toilet = data["has_toilet"]
        cafe.has_wifi = data["has_wifi"]
        cafe.can_take_calls = data["can_take_calls"]
        cafe.seats = data["seats"]
        cafe.coffee_price = cls.normalize_coffee_price(data["coffee_price"])
        cafe.details = cls.sanitize_rich_text(data.get("details"))
        return cafe

    @classmethod
    def new_from_payload(cls, data):
        return cls.apply_payload(Cafe(), data)

    @classmethod
    def serialize(cls, cafe):
        return {
            "id": cafe.id,
            "name": cafe.name,
            "map_url": cafe.map_url,
            "img_url": cafe.img_url,
            "location": cafe.location,
            "has_sockets": cafe.has_sockets,
            "has_toilet": cafe.has_toilet,
            "has_wifi": cafe.has_wifi,
            "can_take_calls": cafe.can_take_calls,
            "seats": cafe.seats,
            "coffee_price": cafe.coffee_price,
            "details": cls.sanitize_rich_text(cafe.details),
        }


class UserService:
    @staticmethod
    def serialize(user):
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": bool(user.is_admin),
            "is_confirmed": bool(user.is_confirmed),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }


def parse_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
