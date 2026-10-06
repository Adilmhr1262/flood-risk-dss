"""0004 - volunteer role + citizen_reports table (Phase 5 mobile app).

- Adds 'volunteer' to the native user_role enum. ALTER TYPE ... ADD VALUE
  cannot run inside a transaction block, so the migration commits Alembic's
  open transaction first (PostgreSQL 12+ supports IF NOT EXISTS).
- Creates the citizen_reports table for community flood sighting reports
  submitted from the mobile app (POST /mobile/report-event).
"""

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block; commit
    # Alembic's transaction first. The context manager's final commit is a
    # harmless no-op afterwards, and subsequent DDL runs in a new transaction.
    op.execute(sa.text("COMMIT"))
    op.execute(sa.text("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'volunteer'"))

    op.create_table(
        "citizen_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("geographic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("geographic_data.id", ondelete="CASCADE"), nullable=False),
        sa.Column("geom", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("severity", sa.Integer, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("severity BETWEEN 1 AND 5", name="ck_citizen_reports_severity"),
        sa.CheckConstraint("status IN ('pending', 'verified', 'dismissed')", name="ck_citizen_reports_status"),
    )
    op.create_index("ix_citizen_reports_geographic_id", "citizen_reports", ["geographic_id"])
    op.create_index("ix_citizen_reports_geom", "citizen_reports", ["geom"], postgresql_using="gist")
    op.create_index("ix_citizen_reports_status", "citizen_reports", ["status"])


def downgrade() -> None:
    op.drop_table("citizen_reports")
    # NOTE: PostgreSQL cannot remove a single enum value; 'volunteer' stays in
    # user_role after downgrade (harmless — it is simply unused).
