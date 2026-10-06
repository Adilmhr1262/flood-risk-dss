"""0002 - weather observations and district boundaries.

Adds two tables supporting real environmental datasets and GIS layers:

- weather_observations: time-series weather records per district, with a
  natural-key UNIQUE constraint for duplicate-safe imports.
- district_boundaries: one MultiPolygon boundary per district for the GIS
  risk-layer rendering.
"""

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    # ------------------------------------------------------------------
    # weather_observations
    # ------------------------------------------------------------------
    op.create_table(
        "weather_observations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "geographic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("geographic_data.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rainfall_mm", sa.Float),
        sa.Column("temperature_c", sa.Float),
        sa.Column("humidity_pct", sa.Float),
        # NOT NULL with a default so the natural-key UNIQUE constraint is
        # effective (NULL values never conflict in PostgreSQL UNIQUE).
        sa.Column(
            "source",
            sa.String(200),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint(
            "geographic_id",
            "observed_at",
            "source",
            name="uq_weather_observations_natural",
        ),
        sa.CheckConstraint("rainfall_mm IS NULL OR rainfall_mm >= 0",
                           name="chk_wo_rainfall"),
        sa.CheckConstraint(
            "temperature_c IS NULL OR (temperature_c >= -20 AND temperature_c <= 60)",
            name="chk_wo_temperature",
        ),
        sa.CheckConstraint(
            "humidity_pct IS NULL OR (humidity_pct >= 0 AND humidity_pct <= 100)",
            name="chk_wo_humidity",
        ),
    )
    op.create_index(
        "idx_weather_observations_geographic",
        "weather_observations",
        ["geographic_id"],
    )
    op.create_index(
        "idx_weather_observations_observed_at",
        "weather_observations",
        ["observed_at"],
    )

    # ------------------------------------------------------------------
    # district_boundaries
    # ------------------------------------------------------------------
    op.create_table(
        "district_boundaries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "geographic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("geographic_data.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # NOTE: spatial_index=False because the GIST index is created
        # explicitly below (matching the naming convention of 0001).
        sa.Column("geom", Geometry("MULTIPOLYGON", srid=4326, spatial_index=False),
                  nullable=False),
        sa.Column("source", sa.String(200)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_district_boundaries_geom",
        "district_boundaries",
        ["geom"],
        postgresql_using="gist",
    )
    op.create_index(
        "idx_district_boundaries_geographic",
        "district_boundaries",
        ["geographic_id"],
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_district_boundaries_updated_at "
        "ON district_boundaries"
    )
    op.execute(
        """
        CREATE TRIGGER trg_district_boundaries_updated_at
            BEFORE UPDATE ON district_boundaries
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_district_boundaries_updated_at "
        "ON district_boundaries"
    )
    op.drop_table("district_boundaries")
    op.drop_table("weather_observations")
