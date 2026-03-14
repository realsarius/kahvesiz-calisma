"""Add admin-specific cafe metadata and cafe_moderators table.

Revision ID: 20260314_0003
Revises: 20260313_0002
Create Date: 2026-03-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260314_0003"
down_revision: Union[str, Sequence[str], None] = "20260313_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cafes", sa.Column("location", sa.Text(), nullable=True))
    op.add_column("cafes", sa.Column("map_url", sa.Text(), nullable=True))
    op.add_column("cafes", sa.Column("img_url", sa.Text(), nullable=True))
    op.add_column("cafes", sa.Column("has_sockets", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("cafes", sa.Column("has_toilet", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("cafes", sa.Column("has_wifi", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("cafes", sa.Column("can_take_calls", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("cafes", sa.Column("seats", sa.Text(), nullable=True))
    op.add_column("cafes", sa.Column("coffee_price", sa.Text(), nullable=True))
    op.add_column("cafes", sa.Column("details", sa.Text(), nullable=True))

    op.create_table(
        "cafe_moderators",
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cafe_id"], ["cafes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "cafe_id", name="uq_cafe_moderators_user_cafe"),
    )


def downgrade() -> None:
    op.drop_table("cafe_moderators")
    op.drop_column("cafes", "details")
    op.drop_column("cafes", "coffee_price")
    op.drop_column("cafes", "seats")
    op.drop_column("cafes", "can_take_calls")
    op.drop_column("cafes", "has_wifi")
    op.drop_column("cafes", "has_toilet")
    op.drop_column("cafes", "has_sockets")
    op.drop_column("cafes", "img_url")
    op.drop_column("cafes", "map_url")
    op.drop_column("cafes", "location")
