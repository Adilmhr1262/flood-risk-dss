"""0001 - initial schema baseline.

Reproduces database/schema.sql exactly: PostGIS/uuid-ossp extensions, the
user_role enum, all 7 tables, updated_at triggers, indexes, and the
v_latest_predictions view. This is the baseline migration; new schema changes
go in later revisions.
"""

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Extensions
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ------------------------------------------------------------------
    # user_role enum (guarded DO block, as in schema.sql)
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                CREATE TYPE user_role AS ENUM ('authority', 'ngo', 'public');
            END IF;
        END
        $$;
        """
    )

    # ------------------------------------------------------------------
    # updated_at trigger function
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name          VARCHAR(150) NOT NULL,
            email         VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role          user_role NOT NULL,
            location_name VARCHAR(150),
            phone         VARCHAR(30),
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')
        );
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users")
    op.execute(
        """
        CREATE TRIGGER trg_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users (role)")

    # ------------------------------------------------------------------
    # geographic_data
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS geographic_data (
            id                           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            district_name                VARCHAR(150) NOT NULL,
            province                     VARCHAR(100) NOT NULL,
            geom                         GEOMETRY(Point, 4326) NOT NULL,
            latitude                     DOUBLE PRECISION NOT NULL,
            longitude                    DOUBLE PRECISION NOT NULL,
            elevation_m                  DOUBLE PRECISION,
            river_distance_km            DOUBLE PRECISION,
            slope_deg                    DOUBLE PRECISION,
            population_density_per_km2   DOUBLE PRECISION,
            vulnerability_index          DOUBLE PRECISION,
            created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT chk_latitude  CHECK (latitude  BETWEEN -90 AND 90),
            CONSTRAINT chk_longitude CHECK (longitude BETWEEN -180 AND 180),
            CONSTRAINT chk_elevation CHECK (elevation_m >= 0),
            CONSTRAINT chk_river_distance CHECK (river_distance_km >= 0),
            CONSTRAINT chk_slope     CHECK (slope_deg >= 0 AND slope_deg <= 90),
            CONSTRAINT chk_pop_density CHECK (population_density_per_km2 >= 0),
            CONSTRAINT chk_vulnerability_index
                CHECK (vulnerability_index >= 0 AND vulnerability_index <= 1)
        );
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_geographic_data_updated_at ON geographic_data")
    op.execute(
        """
        CREATE TRIGGER trg_geographic_data_updated_at
            BEFORE UPDATE ON geographic_data
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_geographic_data_geom "
        "ON geographic_data USING GIST (geom)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_geographic_data_district "
        "ON geographic_data (district_name)"
    )

    # ------------------------------------------------------------------
    # flood_events
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS flood_events (
            id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            geographic_id      UUID NOT NULL REFERENCES geographic_data(id) ON DELETE CASCADE,
            event_date         DATE NOT NULL,
            rainfall_mm        DOUBLE PRECISION,
            temperature_c      DOUBLE PRECISION,
            humidity_pct       DOUBLE PRECISION,
            severity           SMALLINT NOT NULL,
            flood_status       BOOLEAN NOT NULL DEFAULT TRUE,
            damage_description TEXT,
            affected_population INTEGER,
            source             VARCHAR(200),
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT chk_severity CHECK (severity BETWEEN 1 AND 5),
            CONSTRAINT chk_rainfall CHECK (rainfall_mm >= 0),
            CONSTRAINT chk_temperature CHECK (temperature_c BETWEEN -20 AND 60),
            CONSTRAINT chk_humidity CHECK (humidity_pct BETWEEN 0 AND 100),
            CONSTRAINT chk_affected_population CHECK (affected_population >= 0)
        );
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_flood_events_updated_at ON flood_events")
    op.execute(
        """
        CREATE TRIGGER trg_flood_events_updated_at
            BEFORE UPDATE ON flood_events
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_flood_events_geographic "
        "ON flood_events (geographic_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_flood_events_date ON flood_events (event_date)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_flood_events_severity "
        "ON flood_events (severity)"
    )

    # ------------------------------------------------------------------
    # predictions
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            geographic_id   UUID NOT NULL REFERENCES geographic_data(id) ON DELETE CASCADE,
            model_version   VARCHAR(50) NOT NULL,
            probability     DOUBLE PRECISION NOT NULL,
            risk_level      VARCHAR(10) NOT NULL,
            input_features  JSONB,
            main_factors    TEXT[],
            recommendations TEXT[],
            predicted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
            CONSTRAINT chk_probability CHECK (probability >= 0 AND probability <= 1),
            CONSTRAINT chk_risk_level CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH'))
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_predictions_geographic "
        "ON predictions (geographic_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_predictions_predicted_at "
        "ON predictions (predicted_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_predictions_risk_level "
        "ON predictions (risk_level)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_predictions_features "
        "ON predictions USING GIN (input_features)"
    )

    # ------------------------------------------------------------------
    # alerts
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            geographic_id UUID NOT NULL REFERENCES geographic_data(id) ON DELETE CASCADE,
            title         VARCHAR(255) NOT NULL,
            message       TEXT NOT NULL,
            severity      VARCHAR(20) NOT NULL DEFAULT 'info',
            is_active     BOOLEAN NOT NULL DEFAULT TRUE,
            issued_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at    TIMESTAMPTZ,
            CONSTRAINT chk_alert_severity
                CHECK (severity IN ('info', 'watch', 'warning', 'emergency')),
            CONSTRAINT chk_alert_expiry CHECK (expires_at IS NULL OR expires_at > issued_at)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_alerts_geographic ON alerts (geographic_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts (is_active) "
        "WHERE is_active = TRUE"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_alerts_issued ON alerts (issued_at)"
    )

    # ------------------------------------------------------------------
    # shelters
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS shelters (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name          VARCHAR(255) NOT NULL,
            geographic_id UUID REFERENCES geographic_data(id) ON DELETE SET NULL,
            geom          GEOMETRY(Point, 4326),
            capacity      INTEGER,
            facilities    TEXT[],
            contact_phone VARCHAR(30),
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT chk_shelter_capacity CHECK (capacity IS NULL OR capacity >= 0)
        );
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_shelters_updated_at ON shelters")
    op.execute(
        """
        CREATE TRIGGER trg_shelters_updated_at
            BEFORE UPDATE ON shelters
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_shelters_geom ON shelters USING GIST (geom)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_shelters_geographic "
        "ON shelters (geographic_id)"
    )

    # ------------------------------------------------------------------
    # emergency_contacts
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name          VARCHAR(255) NOT NULL,
            organization  VARCHAR(255),
            phone         VARCHAR(30) NOT NULL,
            district_name VARCHAR(150),
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_emergency_contacts_updated_at "
        "ON emergency_contacts"
    )
    op.execute(
        """
        CREATE TRIGGER trg_emergency_contacts_updated_at
            BEFORE UPDATE ON emergency_contacts
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_emergency_contacts_district "
        "ON emergency_contacts (district_name)"
    )

    # ------------------------------------------------------------------
    # v_latest_predictions view
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE VIEW v_latest_predictions AS
        SELECT DISTINCT ON (p.geographic_id)
            p.id,
            p.geographic_id,
            g.district_name,
            g.province,
            p.model_version,
            p.probability,
            p.risk_level,
            p.main_factors,
            p.recommendations,
            p.predicted_at
        FROM predictions p
        JOIN geographic_data g ON g.id = p.geographic_id
        ORDER BY p.geographic_id, p.predicted_at DESC;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_latest_predictions")
    for table in (
        "emergency_contacts",
        "shelters",
        "alerts",
        "predictions",
        "flood_events",
        "geographic_data",
        "users",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at() CASCADE")
    op.execute("DROP TYPE IF EXISTS user_role")
    # Extensions are intentionally left installed: other databases or tools
    # may rely on postgis / uuid-ossp.
