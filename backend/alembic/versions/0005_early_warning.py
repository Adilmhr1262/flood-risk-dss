"""0005 - early warning automation (Phase 6).

- device_tokens: FCM push-notification tokens registered by mobile clients.
- alerts: add model_version / probability / factors columns so the alert
  engine can record which model and evidence triggered each alert.
- citizen_reports: add category (flood_water, road_blockage, rescue_request,
  medical_emergency), image_path, verified_by / verified_at /
  verification_note; extend the status check constraint with 'rejected' and
  'resolved' for the authority verification workflow.
"""

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    op.create_table(
        "device_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fcm_token", sa.String(512), nullable=False, unique=True),
        sa.Column("platform", sa.String(20), nullable=False, server_default="android"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_device_tokens_user_id", "device_tokens", ["user_id"])

    op.add_column("alerts", sa.Column("model_version", sa.String(64), nullable=True))
    op.add_column("alerts", sa.Column("probability", sa.Float, nullable=True))
    op.add_column("alerts", sa.Column("factors", postgresql.JSONB, nullable=True))

    op.add_column("citizen_reports", sa.Column("category", sa.String(30), nullable=True))
    op.add_column("citizen_reports", sa.Column("image_path", sa.String(500), nullable=True))
    op.add_column("citizen_reports", sa.Column("verified_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("citizen_reports", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("citizen_reports", sa.Column("verification_note", sa.Text, nullable=True))
    op.execute(sa.text("ALTER TABLE citizen_reports DROP CONSTRAINT ck_citizen_reports_status"))
    op.execute(sa.text(
        "ALTER TABLE citizen_reports ADD CONSTRAINT ck_citizen_reports_status "
        "CHECK (status IN ('pending', 'verified', 'rejected', 'resolved', 'dismissed'))"
    ))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE citizen_reports DROP CONSTRAINT ck_citizen_reports_status"))
    op.execute(sa.text(
        "ALTER TABLE citizen_reports ADD CONSTRAINT ck_citizen_reports_status "
        "CHECK (status IN ('pending', 'verified', 'dismissed'))"
    ))
    op.drop_column("citizen_reports", "verification_note")
    op.drop_column("citizen_reports", "verified_at")
    op.drop_column("citizen_reports", "verified_by")
    op.drop_column("citizen_reports", "image_path")
    op.drop_column("citizen_reports", "category")
    op.drop_column("alerts", "factors")
    op.drop_column("alerts", "probability")
    op.drop_column("alerts", "model_version")
    op.drop_index("ix_device_tokens_user_id", table_name="device_tokens")
    op.drop_table("device_tokens")
