from datetime import datetime, timezone

from flask_login import UserMixin

from kahvesiz_app.extensions import db


user_cafe = db.Table(
    "user_cafe",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("cafe_id", db.Integer, db.ForeignKey("cafe.id"), primary_key=True),
)


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    moderated_cafes = db.relationship("Cafe", secondary="user_cafe", back_populates="moderators")

    def __repr__(self):
        return f"<User {self.name}>"

    def is_moderator_of(self, cafe_id):
        return any(cafe.id == cafe_id for cafe in self.moderated_cafes)

    def get_default_cafe_id(self):
        if self.moderated_cafes:
            return self.moderated_cafes[0].id
        return None


class Cafe(db.Model):
    __tablename__ = "cafe"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    map_url = db.Column(db.String(255), unique=True, nullable=False)
    img_url = db.Column(db.String(255), unique=True, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    has_sockets = db.Column(db.Boolean, default=False)
    has_toilet = db.Column(db.Boolean, default=False)
    has_wifi = db.Column(db.Boolean, default=False)
    can_take_calls = db.Column(db.Boolean, default=False)
    seats = db.Column(db.String(100), nullable=False)
    coffee_price = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    moderators = db.relationship("User", secondary="user_cafe", back_populates="moderated_cafes")

    def __repr__(self):
        return f"<Cafe {self.name}>"

