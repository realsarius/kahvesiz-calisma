"""Add missing indexes and trigger-based maintenance.

Revision ID: 20260313_0002
Revises: 20260313_0001
Create Date: 2026-03-13
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260313_0002"
down_revision: Union[str, None] = "20260313_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_updated_at_trigger(trigger_name: str, table_name: str, schema: str | None = None) -> None:
    qualified_table = f"{schema}.{table_name}" if schema else table_name
    op.execute(
        f"""
        CREATE TRIGGER {trigger_name}
        BEFORE UPDATE ON {qualified_table}
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )


def _drop_updated_at_trigger(trigger_name: str, table_name: str, schema: str | None = None) -> None:
    qualified_table = f"{schema}.{table_name}" if schema else table_name
    op.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {qualified_table}")


def upgrade() -> None:
    op.create_index("idx_cafe_images_cafe_id", "cafe_images", ["cafe_id"], unique=False)
    op.create_index("idx_cafe_seats_cafe_id", "cafe_seats", ["cafe_id"], unique=False)
    op.create_index("idx_sessions_user_id", "user_sessions", ["user_id"], unique=False)
    op.create_index("idx_auth_tokens_user_id", "auth_tokens", ["user_id"], unique=False)

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    _create_updated_at_trigger("trg_users_updated_at", "users")
    _create_updated_at_trigger("trg_user_pii_updated_at", "user_pii", schema="pii")
    _create_updated_at_trigger("trg_cafes_updated_at", "cafes")
    _create_updated_at_trigger("trg_cafe_amenities_updated_at", "cafe_amenities")
    _create_updated_at_trigger("trg_cafe_seats_updated_at", "cafe_seats")
    _create_updated_at_trigger("trg_reviews_updated_at", "reviews")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION refresh_cafe_review_stats(p_cafe_id uuid)
        RETURNS void AS $$
        BEGIN
            UPDATE cafes
            SET
                avg_rating = COALESCE(
                    (
                        SELECT ROUND(AVG(r.rating)::numeric, 2)
                        FROM reviews r
                        WHERE r.cafe_id = p_cafe_id AND r.deleted_at IS NULL
                    ),
                    0
                ),
                review_count = (
                    SELECT COUNT(*)
                    FROM reviews r
                    WHERE r.cafe_id = p_cafe_id AND r.deleted_at IS NULL
                )
            WHERE id = p_cafe_id;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_reviews_sync_cafe_stats()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                PERFORM refresh_cafe_review_stats(OLD.cafe_id);
                RETURN OLD;
            END IF;

            PERFORM refresh_cafe_review_stats(NEW.cafe_id);

            IF TG_OP = 'UPDATE' AND OLD.cafe_id IS DISTINCT FROM NEW.cafe_id THEN
                PERFORM refresh_cafe_review_stats(OLD.cafe_id);
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_reviews_refresh_cafe_stats
        AFTER INSERT OR UPDATE OR DELETE ON reviews
        FOR EACH ROW
        EXECUTE FUNCTION trg_reviews_sync_cafe_stats();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_reviews_refresh_cafe_stats ON reviews")

    _drop_updated_at_trigger("trg_reviews_updated_at", "reviews")
    _drop_updated_at_trigger("trg_cafe_seats_updated_at", "cafe_seats")
    _drop_updated_at_trigger("trg_cafe_amenities_updated_at", "cafe_amenities")
    _drop_updated_at_trigger("trg_cafes_updated_at", "cafes")
    _drop_updated_at_trigger("trg_user_pii_updated_at", "user_pii", schema="pii")
    _drop_updated_at_trigger("trg_users_updated_at", "users")

    op.execute("DROP FUNCTION IF EXISTS trg_reviews_sync_cafe_stats()")
    op.execute("DROP FUNCTION IF EXISTS refresh_cafe_review_stats(uuid)")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    op.drop_index("idx_auth_tokens_user_id", table_name="auth_tokens")
    op.drop_index("idx_sessions_user_id", table_name="user_sessions")
    op.drop_index("idx_cafe_seats_cafe_id", table_name="cafe_seats")
    op.drop_index("idx_cafe_images_cafe_id", table_name="cafe_images")
