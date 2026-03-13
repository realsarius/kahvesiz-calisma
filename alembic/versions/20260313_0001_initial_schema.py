"""Initial PostgreSQL schema for FastAPI migration.

Revision ID: 20260313_0001
Revises:
Create Date: 2026-03-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260313_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE SCHEMA IF NOT EXISTS pii")

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default=sa.text("'user'")),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )

    op.create_table(
        "user_pii",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("address_line1", sa.String(length=255), nullable=True),
        sa.Column("address_line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=10), nullable=True),
        sa.Column("country_code", sa.CHAR(length=2), nullable=False, server_default=sa.text("'TR'")),
        sa.Column("consent_given_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consent_ip", postgresql.INET(), nullable=True),
        sa.Column("consent_version", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["public.users.id"], ondelete="CASCADE"),
        schema="pii",
    )

    op.create_table(
        "auth_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("token_type", sa.String(length=30), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_auth_tokens_token_hash"),
    )

    op.create_table(
        "user_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_token_hash", sa.String(length=64), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("session_token_hash", name="uq_user_sessions_session_token_hash"),
    )

    op.create_table(
        "neighborhoods",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("slug", name="uq_neighborhoods_slug"),
    )

    op.create_table(
        "cafes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("neighborhood_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 8), nullable=False),
        sa.Column("longitude", sa.Numeric(11, 8), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("instagram", sa.String(length=100), nullable=True),
        sa.Column("google_maps_url", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("total_capacity", sa.Integer(), nullable=True),
        sa.Column("indoor_capacity", sa.Integer(), nullable=True),
        sa.Column("outdoor_capacity", sa.Integer(), nullable=True),
        sa.Column("avg_rating", sa.Numeric(3, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["neighborhood_id"], ["neighborhoods.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug", name="uq_cafes_slug"),
    )

    op.create_table(
        "cafe_amenities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("cafe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wifi_available", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("wifi_speed_mbps", sa.Integer(), nullable=True),
        sa.Column("outlet_count", sa.Integer(), nullable=True),
        sa.Column("outlet_accessibility", sa.String(length=20), nullable=True),
        sa.Column("noise_level", sa.String(length=20), nullable=True),
        sa.Column("has_natural_light", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_ac", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_heating", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_parking", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_accessible_entry", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allows_laptop", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_spend_try", sa.Numeric(8, 2), nullable=True),
        sa.Column("has_food", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_alcohol", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pet_friendly", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["cafe_id"], ["cafes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("cafe_id", name="uq_cafe_amenities_cafe_id"),
    )

    op.create_table(
        "cafe_hours",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("cafe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("opens_at", sa.Time(), nullable=True),
        sa.Column("closes_at", sa.Time(), nullable=True),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["cafe_id"], ["cafes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("cafe_id", "day_of_week", name="uq_cafe_hours_cafe_id_day_of_week"),
    )

    op.create_table(
        "cafe_images",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("cafe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("alt_text", sa.String(length=200), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["cafe_id"], ["cafes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "cafe_seats",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("cafe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seat_type", sa.String(length=30), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("available_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("has_outlet", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["cafe_id"], ["cafes.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "reviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cafe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("noise_rating", sa.SmallInteger(), nullable=True),
        sa.Column("wifi_rating", sa.SmallInteger(), nullable=True),
        sa.Column("outlet_rating", sa.SmallInteger(), nullable=True),
        sa.Column("visited_at", sa.Date(), nullable=True),
        sa.Column("is_verified_visit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
        sa.CheckConstraint("noise_rating BETWEEN 1 AND 5", name="ck_reviews_noise_rating_range"),
        sa.CheckConstraint("wifi_rating BETWEEN 1 AND 5", name="ck_reviews_wifi_rating_range"),
        sa.CheckConstraint("outlet_rating BETWEEN 1 AND 5", name="ck_reviews_outlet_rating_range"),
        sa.ForeignKeyConstraint(["cafe_id"], ["cafes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", "cafe_id", name="uq_reviews_user_id_cafe_id"),
    )

    op.create_table(
        "review_votes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vote", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("review_id", "user_id", name="uq_review_votes_review_id_user_id"),
    )

    op.create_table(
        "bookmarks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cafe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["cafe_id"], ["cafes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "cafe_id", name="uq_bookmarks_user_id_cafe_id"),
    )

    op.create_index(
        "idx_cafes_neighborhood_active",
        "cafes",
        ["neighborhood_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "idx_sessions_token",
        "user_sessions",
        ["session_token_hash"],
        unique=False,
    )

    op.execute(
        "CREATE INDEX idx_cafes_avg_rating ON cafes(avg_rating DESC) WHERE is_active = true"
    )
    op.execute(
        "CREATE INDEX idx_cafes_created_at ON cafes(created_at DESC) WHERE is_active = true"
    )
    op.execute(
        "CREATE INDEX idx_cafes_cursor ON cafes(created_at DESC, id DESC) WHERE is_active = true"
    )
    op.execute(
        "CREATE INDEX idx_reviews_cafe_id ON reviews(cafe_id) WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX idx_auth_tokens_hash ON auth_tokens(token_hash) WHERE used_at IS NULL"
    )
    op.execute(
        "CREATE INDEX idx_cafes_deleted ON cafes(deleted_at) WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    op.drop_index("idx_users_deleted", table_name="users")
    op.drop_index("idx_cafes_deleted", table_name="cafes")
    op.drop_index("idx_auth_tokens_hash", table_name="auth_tokens")
    op.drop_index("idx_reviews_cafe_id", table_name="reviews")
    op.drop_index("idx_cafes_cursor", table_name="cafes")
    op.drop_index("idx_cafes_created_at", table_name="cafes")
    op.drop_index("idx_cafes_avg_rating", table_name="cafes")
    op.drop_index("idx_sessions_token", table_name="user_sessions")
    op.drop_index("idx_cafes_neighborhood_active", table_name="cafes")

    op.drop_table("bookmarks")
    op.drop_table("review_votes")
    op.drop_table("reviews")
    op.drop_table("cafe_seats")
    op.drop_table("cafe_images")
    op.drop_table("cafe_hours")
    op.drop_table("cafe_amenities")
    op.drop_table("cafes")
    op.drop_table("neighborhoods")
    op.drop_table("user_sessions")
    op.drop_table("auth_tokens")
    op.drop_table("user_pii", schema="pii")
    op.drop_table("users")
    op.execute("DROP SCHEMA IF EXISTS pii")
