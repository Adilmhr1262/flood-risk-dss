-- ============================================================================
-- Flood Risk Prediction and Early Warning Decision Support System
-- Database Schema (PostgreSQL 15 + PostGIS)
-- ============================================================================
-- Master's-level research project: data-driven flood risk assessment,
-- machine learning-based prediction, and disaster decision support.
--
-- Apply with:
--   createdb flood_risk_dss
--   psql -d flood_risk_dss -f database/schema.sql
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PostGIS extension (required for geographic data)
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS postgis;
-- uuid-ossp installs uuid_generate_v4() etc.; gen_random_uuid() is built into
-- PostgreSQL 13+ and used as the UUID default below.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- Enums
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('authority', 'ngo', 'public', 'volunteer');
    END IF;
END
$$;

-- ----------------------------------------------------------------------------
-- updated_at maintenance trigger function
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- USERS
-- ============================================================================
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
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);

-- ============================================================================
-- GEOGRAPHIC_DATA
-- Base geographic / topographic / social-vulnerability data per location.
-- Each row represents a district-level assessment point.
-- ============================================================================
CREATE TABLE IF NOT EXISTS geographic_data (
    id                           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_name                VARCHAR(150) NOT NULL,
    province                     VARCHAR(100) NOT NULL,
    geom                         GEOMETRY(Point, 4326) NOT NULL,
    latitude                     DOUBLE PRECISION NOT NULL,
    longitude                    DOUBLE PRECISION NOT NULL,
    elevation_m                  DOUBLE PRECISION,      -- metres above sea level
    river_distance_km            DOUBLE PRECISION,      -- distance to nearest major river (Indus)
    slope_deg                    DOUBLE PRECISION,      -- average terrain slope in degrees
    population_density_per_km2   DOUBLE PRECISION,
    vulnerability_index          DOUBLE PRECISION,      -- composite social vulnerability, 0-1
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

DROP TRIGGER IF EXISTS trg_geographic_data_updated_at ON geographic_data;
CREATE TRIGGER trg_geographic_data_updated_at
    BEFORE UPDATE ON geographic_data
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Spatial index for map queries / proximity searches
CREATE INDEX IF NOT EXISTS idx_geographic_data_geom
    ON geographic_data USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_geographic_data_district
    ON geographic_data (district_name);

-- ============================================================================
-- FLOOD_EVENTS
-- Historical flood records used for model training and trend analysis.
-- ============================================================================
CREATE TABLE IF NOT EXISTS flood_events (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geographic_id      UUID NOT NULL REFERENCES geographic_data(id) ON DELETE CASCADE,
    event_date         DATE NOT NULL,
    rainfall_mm        DOUBLE PRECISION,   -- recorded rainfall around the event
    temperature_c      DOUBLE PRECISION,
    humidity_pct       DOUBLE PRECISION,
    severity           SMALLINT NOT NULL,  -- 1 (minor) .. 5 (catastrophic)
    flood_status       BOOLEAN NOT NULL DEFAULT TRUE,
    damage_description TEXT,
    affected_population INTEGER,
    source             VARCHAR(200),       -- e.g. 'NDMA report', 'PDMA Sindh'
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_severity CHECK (severity BETWEEN 1 AND 5),
    CONSTRAINT chk_rainfall CHECK (rainfall_mm >= 0),
    CONSTRAINT chk_temperature CHECK (temperature_c BETWEEN -20 AND 60),
    CONSTRAINT chk_humidity CHECK (humidity_pct BETWEEN 0 AND 100),
    CONSTRAINT chk_affected_population CHECK (affected_population >= 0)
);

DROP TRIGGER IF EXISTS trg_flood_events_updated_at ON flood_events;
CREATE TRIGGER trg_flood_events_updated_at
    BEFORE UPDATE ON flood_events
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_flood_events_geographic ON flood_events (geographic_id);
CREATE INDEX IF NOT EXISTS idx_flood_events_date ON flood_events (event_date);
CREATE INDEX IF NOT EXISTS idx_flood_events_severity ON flood_events (severity);

-- ============================================================================
-- PREDICTIONS
-- Machine learning-based risk predictions generated by the prediction engine.
-- input_features stores the feature vector used; main_factors and
-- recommendations are human-readable decision-support outputs.
-- ============================================================================
CREATE TABLE IF NOT EXISTS predictions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geographic_id   UUID NOT NULL REFERENCES geographic_data(id) ON DELETE CASCADE,
    model_version   VARCHAR(50) NOT NULL,   -- e.g. 'rf-v1.2', 'xgb-v1.2', 'ann-v1.0'
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

CREATE INDEX IF NOT EXISTS idx_predictions_geographic ON predictions (geographic_id);
CREATE INDEX IF NOT EXISTS idx_predictions_predicted_at ON predictions (predicted_at);
CREATE INDEX IF NOT EXISTS idx_predictions_risk_level ON predictions (risk_level);
CREATE INDEX IF NOT EXISTS idx_predictions_features ON predictions USING GIN (input_features);

-- ============================================================================
-- ALERTS
-- Early warning alerts issued for geographic areas.
-- ============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geographic_id UUID NOT NULL REFERENCES geographic_data(id) ON DELETE CASCADE,
    title         VARCHAR(255) NOT NULL,
    message       TEXT NOT NULL,
    severity      VARCHAR(20) NOT NULL DEFAULT 'info',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    issued_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at    TIMESTAMPTZ,
    -- Phase 6 early-warning provenance: which model scored the district and
    -- what evidence triggered the alert.
    model_version VARCHAR(64),
    probability   DOUBLE PRECISION,
    factors       JSONB,
    CONSTRAINT chk_alert_severity
        CHECK (severity IN ('info', 'watch', 'warning', 'emergency')),
    CONSTRAINT chk_alert_expiry CHECK (expires_at IS NULL OR expires_at > issued_at)
);

CREATE INDEX IF NOT EXISTS idx_alerts_geographic ON alerts (geographic_id);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts (is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_alerts_issued ON alerts (issued_at);

-- ============================================================================
-- SHELTERS
-- Emergency shelters / relief centres.
-- ============================================================================
CREATE TABLE IF NOT EXISTS shelters (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL,
    geographic_id UUID REFERENCES geographic_data(id) ON DELETE SET NULL,
    geom          GEOMETRY(Point, 4326),
    capacity      INTEGER,
    -- Phase W3: operational occupancy monitoring for the command center.
    current_occupancy INTEGER NOT NULL DEFAULT 0,
    status        VARCHAR(20) NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'full', 'closed', 'maintenance')),
    facilities    TEXT[],
    contact_phone VARCHAR(30),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_shelter_capacity CHECK (capacity IS NULL OR capacity >= 0)
);

DROP TRIGGER IF EXISTS trg_shelters_updated_at ON shelters;
CREATE TRIGGER trg_shelters_updated_at
    BEFORE UPDATE ON shelters
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_shelters_geom ON shelters USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_shelters_geographic ON shelters (geographic_id);

-- ============================================================================
-- EMERGENCY_CONTACTS
-- Rescue / relief contact directory (district level and national).
-- ============================================================================
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL,
    organization  VARCHAR(255),
    phone         VARCHAR(30) NOT NULL,
    district_name VARCHAR(150),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_emergency_contacts_updated_at ON emergency_contacts;
CREATE TRIGGER trg_emergency_contacts_updated_at
    BEFORE UPDATE ON emergency_contacts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_emergency_contacts_district
    ON emergency_contacts (district_name);

-- ============================================================================
-- Helpful view: latest prediction per location
-- ============================================================================
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

-- ============================================================================
-- Phase 4 — GIS decision support tables (also created by Alembic migration 0003)
-- ============================================================================

CREATE TABLE IF NOT EXISTS infrastructure (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(30)  NOT NULL
                    CHECK (type IN ('shelter', 'hospital', 'rescue_center', 'emergency_facility')),
    geographic_id   UUID REFERENCES geographic_data (id) ON DELETE SET NULL,
    geom            geometry(POINT, 4326),
    capacity        INTEGER,
    contact_phone   VARCHAR(30),
    operational_status VARCHAR(20) NOT NULL DEFAULT 'operational',
    is_sample_data  BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_infrastructure_geographic_id ON infrastructure (geographic_id);
CREATE INDEX IF NOT EXISTS ix_infrastructure_type ON infrastructure (type);
CREATE INDEX IF NOT EXISTS ix_infrastructure_geom ON infrastructure USING GIST (geom);

CREATE TABLE IF NOT EXISTS vulnerability_indicators (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geographic_id       UUID NOT NULL UNIQUE REFERENCES geographic_data (id) ON DELETE CASCADE,
    population_density  DOUBLE PRECISION,
    vulnerability_index DOUBLE PRECISION NOT NULL,
    poverty_proxy       DOUBLE PRECISION,
    healthcare_access_score DOUBLE PRECISION,
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS resource_allocations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geographic_id   UUID NOT NULL REFERENCES geographic_data (id) ON DELETE CASCADE,
    resource_type   VARCHAR(50) NOT NULL,
    quantity        INTEGER NOT NULL,
    allocated_by    UUID REFERENCES users (id) ON DELETE SET NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'planned',
    allocated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes           TEXT
);
CREATE INDEX IF NOT EXISTS ix_resource_allocations_geographic_id
    ON resource_allocations (geographic_id);

DROP TRIGGER IF EXISTS trg_infrastructure_updated_at ON infrastructure;
CREATE TRIGGER trg_infrastructure_updated_at
    BEFORE UPDATE ON infrastructure
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ----------------------------------------------------------------------------
-- citizen_reports: community flood sighting reports (Phase 5 mobile app)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS citizen_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id     UUID REFERENCES users (id) ON DELETE SET NULL,
    geographic_id   UUID NOT NULL REFERENCES geographic_data (id) ON DELETE CASCADE,
    geom            GEOMETRY(POINT, 4326),
    severity        INTEGER NOT NULL CHECK (severity BETWEEN 1 AND 5),
    description     TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'verified', 'rejected', 'resolved', 'dismissed')),
    -- Phase W3: triage priority for the authority command center.
    priority        VARCHAR(20) NOT NULL DEFAULT 'medium'
                    CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    -- Phase 6: report category, photo evidence, authority verification chain.
    category        VARCHAR(30),
    image_path      VARCHAR(500),
    verified_by     UUID REFERENCES users (id) ON DELETE SET NULL,
    verified_at     TIMESTAMPTZ,
    verification_note TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_citizen_reports_geographic_id ON citizen_reports (geographic_id);
CREATE INDEX IF NOT EXISTS ix_citizen_reports_geom ON citizen_reports USING GIST (geom);
CREATE INDEX IF NOT EXISTS ix_citizen_reports_status ON citizen_reports (status);

-- ============================================================================
-- device_tokens: FCM push-notification tokens (Phase 6 early warning)
-- ============================================================================
CREATE TABLE IF NOT EXISTS device_tokens (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    fcm_token  VARCHAR(512) NOT NULL UNIQUE,
    platform   VARCHAR(20) NOT NULL DEFAULT 'android',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_device_tokens_user_id ON device_tokens (user_id);

-- ============================================================================
-- weather_observations: time-series weather per district (Phase 2+; Phase 6
-- early-warning ingestion writes here). Natural-key UNIQUE for idempotent
-- imports.
-- ============================================================================
CREATE TABLE IF NOT EXISTS weather_observations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geographic_id   UUID NOT NULL REFERENCES geographic_data (id) ON DELETE CASCADE,
    observed_at     TIMESTAMPTZ NOT NULL,
    rainfall_mm     DOUBLE PRECISION CHECK (rainfall_mm IS NULL OR rainfall_mm >= 0),
    temperature_c   DOUBLE PRECISION CHECK (temperature_c IS NULL OR (temperature_c >= -20 AND temperature_c <= 60)),
    humidity_pct    DOUBLE PRECISION CHECK (humidity_pct IS NULL OR (humidity_pct >= 0 AND humidity_pct <= 100)),
    source          VARCHAR(200) NOT NULL DEFAULT 'unknown',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_weather_observations_natural
        UNIQUE (geographic_id, observed_at, source)
);
CREATE INDEX IF NOT EXISTS idx_weather_observations_geographic ON weather_observations (geographic_id);
CREATE INDEX IF NOT EXISTS idx_weather_observations_observed_at ON weather_observations (observed_at);

-- ============================================================================
-- district_boundaries: one MultiPolygon boundary per district (Phase 2 GIS)
-- ============================================================================
CREATE TABLE IF NOT EXISTS district_boundaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geographic_id   UUID NOT NULL UNIQUE REFERENCES geographic_data (id) ON DELETE CASCADE,
    geom            GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    source          VARCHAR(200),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_district_boundaries_geom ON district_boundaries USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_district_boundaries_geographic ON district_boundaries (geographic_id);
DROP TRIGGER IF EXISTS trg_district_boundaries_updated_at ON district_boundaries;
CREATE TRIGGER trg_district_boundaries_updated_at
    BEFORE UPDATE ON district_boundaries
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- incidents / incident_notes: operational incident records (Phase W3 command center)
-- Workflow: detected -> verified -> response_started -> resolved
-- ============================================================================
CREATE TABLE IF NOT EXISTS incidents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    geographic_id   UUID REFERENCES geographic_data (id) ON DELETE SET NULL,
    geom            GEOMETRY(POINT, 4326),
    status          VARCHAR(30) NOT NULL DEFAULT 'detected'
                    CHECK (status IN ('detected', 'verified', 'response_started', 'resolved')),
    severity        INTEGER NOT NULL DEFAULT 3 CHECK (severity BETWEEN 1 AND 5),
    source          VARCHAR(30) NOT NULL DEFAULT 'manual'
                    CHECK (source IN ('manual', 'alert', 'report')),
    source_id       UUID,
    created_by      UUID REFERENCES users (id) ON DELETE SET NULL,
    assigned_to     UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_incidents_geographic_id ON incidents (geographic_id);
CREATE INDEX IF NOT EXISTS ix_incidents_status ON incidents (status);
CREATE INDEX IF NOT EXISTS ix_incidents_geom ON incidents USING GIST (geom);
DROP TRIGGER IF EXISTS trg_incidents_updated_at ON incidents;
CREATE TRIGGER trg_incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS incident_notes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     UUID NOT NULL REFERENCES incidents (id) ON DELETE CASCADE,
    author_id       UUID REFERENCES users (id) ON DELETE SET NULL,
    note            TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_incident_notes_incident_id ON incident_notes (incident_id);

-- ============================================================================
-- response_teams: field response teams (Phase W3 command center)
-- ============================================================================
CREATE TABLE IF NOT EXISTS response_teams (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    team_type       VARCHAR(30) NOT NULL
                    CHECK (team_type IN ('rescue', 'medical', 'logistics', 'boat')),
    geographic_id   UUID REFERENCES geographic_data (id) ON DELETE SET NULL,
    members_count   INTEGER,
    status          VARCHAR(30) NOT NULL DEFAULT 'available'
                    CHECK (status IN ('available', 'deployed', 'standby')),
    contact_phone   VARCHAR(30),
    geom            GEOMETRY(POINT, 4326),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_response_teams_geographic_id ON response_teams (geographic_id);
CREATE INDEX IF NOT EXISTS ix_response_teams_geom ON response_teams USING GIST (geom);
DROP TRIGGER IF EXISTS trg_response_teams_updated_at ON response_teams;
CREATE TRIGGER trg_response_teams_updated_at
    BEFORE UPDATE ON response_teams
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
