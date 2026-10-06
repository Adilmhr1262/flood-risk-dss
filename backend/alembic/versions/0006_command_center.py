"""0006 - authority command center (Phase W3).

- incidents: operational incident records with a controlled status workflow
  (detected -> verified -> response_started -> resolved), optional district
  link, severity 1-5, and provenance (manual entry, alert, or citizen report).
- incident_notes: timestamped authority notes appended to an incident.
- response_teams: rescue / medical / logistics / boat teams with district,
  size, availability status, and contact details.
- shelters: add current_occupancy and operational status so the command
  center can monitor capacity vs. availability.
- citizen_reports: add priority (low / medium / high / urgent) for triage.
"""

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("geographic_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("geographic_data.id", ondelete="SET NULL"),
                  nullable=True, index=True),
        sa.Column("geom", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="detected"),
        sa.Column("severity", sa.Integer, nullable=False, server_default="3"),
        sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('detected', 'verified', 'response_started', 'resolved')",
            name="ck_incidents_status",
        ),
        sa.CheckConstraint("severity BETWEEN 1 AND 5", name="ck_incidents_severity"),
        sa.CheckConstraint(
            "source IN ('manual', 'alert', 'report')", name="ck_incidents_source"
        ),
    )
    op.create_index("ix_incidents_status", "incidents", ["status"])

    op.create_table(
        "incident_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False,
                  index=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("note", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    op.create_table(
        "response_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("team_type", sa.String(30), nullable=False),
        sa.Column("geographic_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("geographic_data.id", ondelete="SET NULL"),
                  nullable=True, index=True),
        sa.Column("members_count", sa.Integer, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="available"),
        sa.Column("contact_phone", sa.String(30), nullable=True),
        sa.Column("geom", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "team_type IN ('rescue', 'medical', 'logistics', 'boat')",
            name="ck_response_teams_type",
        ),
        sa.CheckConstraint(
            "status IN ('available', 'deployed', 'standby')",
            name="ck_response_teams_status",
        ),
    )

    op.add_column("shelters", sa.Column(
        "current_occupancy", sa.Integer, nullable=False, server_default="0"))
    op.add_column("shelters", sa.Column(
        "status", sa.String(20), nullable=False, server_default="open"))
    op.execute(sa.text(
        "ALTER TABLE shelters ADD CONSTRAINT ck_shelters_status "
        "CHECK (status IN ('open', 'full', 'closed', 'maintenance'))"
    ))

    op.add_column("citizen_reports", sa.Column(
        "priority", sa.String(20), nullable=False, server_default="medium"))
    op.execute(sa.text(
        "ALTER TABLE citizen_reports ADD CONSTRAINT ck_citizen_reports_priority "
        "CHECK (priority IN ('low', 'medium', 'high', 'urgent'))"
    ))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE citizen_reports DROP CONSTRAINT ck_citizen_reports_priority"))
    op.drop_column("citizen_reports", "priority")
    op.execute(sa.text("ALTER TABLE shelters DROP CONSTRAINT ck_shelters_status"))
    op.drop_column("shelters", "status")
    op.drop_column("shelters", "current_occupancy")
    op.drop_table("response_teams")
    op.drop_table("incident_notes")
    op.drop_table("incidents")
