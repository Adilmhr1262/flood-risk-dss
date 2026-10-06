"""0003 - GIS decision support tables: infrastructure, vulnerability indicators, resource allocations.

Adds three tables supporting the Phase 4 GIS intelligence and decision
support layers:

- infrastructure: hospitals, rescue centres and emergency facilities
  (shelters already live in the `shelters` table and are not duplicated).
- vulnerability_indicators: one row per district with population density
  and a composite vulnerability index.
- resource_allocations: planned/dispatched relief resources per district.

Seed data provenance:
- vulnerability_indicators rows are seeded from the Phase 3 research
  dataset `data/processed/sindh_training_2010_2024.csv` (latest year, 2024,
  per district). That index is the composite documented in
  `data/processed/DATA_CARD.md`.
- infrastructure rows are clearly-marked SAMPLE data (is_sample_data=true)
  with plausible names and locations offset from district centroids.
  Replace with authoritative PDMA/Health Department registries before
  operational use.
"""

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    # infrastructure
    op.create_table(
        "infrastructure",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("geographic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("geographic_data.id", ondelete="SET NULL")),
        sa.Column("geom", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("capacity", sa.Integer),
        sa.Column("contact_phone", sa.String(30)),
        sa.Column("operational_status", sa.String(20), nullable=False, server_default="operational"),
        sa.Column("is_sample_data", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("type IN ('shelter', 'hospital', 'rescue_center', 'emergency_facility')", name="ck_infrastructure_type"),
    )
    op.create_index("ix_infrastructure_geographic_id", "infrastructure", ["geographic_id"])
    op.create_index("ix_infrastructure_geom", "infrastructure", ["geom"], postgresql_using="gist")
    op.create_index("ix_infrastructure_type", "infrastructure", ["type"])

    # vulnerability_indicators
    op.create_table(
        "vulnerability_indicators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("geographic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("geographic_data.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("population_density", sa.Float),
        sa.Column("vulnerability_index", sa.Float, nullable=False),
        sa.Column("poverty_proxy", sa.Float),
        sa.Column("healthcare_access_score", sa.Float),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("notes", sa.Text),
    )

    # resource_allocations
    op.create_table(
        "resource_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("geographic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("geographic_data.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("allocated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("allocated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("notes", sa.Text),
    )
    op.create_index("ix_resource_allocations_geographic_id", "resource_allocations", ["geographic_id"])

    # ---- seed: vulnerability indicators (Phase 3 dataset, 2024 per district) ----
    conn = op.get_bind()
    geo_ids = {r[0]: r[1] for r in conn.execute(sa.text("SELECT district_name, id FROM geographic_data")).fetchall()}
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Badin'], "p": 265.0, "v": 0.0899, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Dadu'], "p": 268.0, "v": 0.3315, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Dera Ghazi Khan'], "p": 245.0, "v": 0.3333, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Ghotki'], "p": 255.0, "v": 0.347, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Hyderabad'], "p": 610.0, "v": 0.4493, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Jacobabad'], "p": 375.0, "v": 0.3482, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Karachi'], "p": 3650.0, "v": 0.8, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Larkana'], "p": 420.0, "v": 0.2745, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Rajanpur'], "p": 160.0, "v": 0.2815, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Shikarpur'], "p": 480.0, "v": 0.4084, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Sukkur'], "p": 530.0, "v": 0.3912, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    conn.execute(sa.text("INSERT INTO vulnerability_indicators (geographic_id, population_density, vulnerability_index, notes) VALUES (:g, :p, :v, :n)"), {"g": geo_ids['Thatta'], "p": 175.0, "v": 0.1377, "n": "Seeded from data/processed/sindh_training_2010_2024.csv (2024 row); composite index documented in data/processed/DATA_CARD.md"})
    # ---- seed: infrastructure (clearly-marked sample data) ----
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Badin Civil Hospital', "t": 'hospital', "g": geo_ids['Badin'], "lo": 68.8500, "la": 24.6800, "c": 200, "p": '+92-21-9900000', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Badin', "t": 'rescue_center', "g": geo_ids['Badin'], "lo": 68.8220, "la": 24.6480, "c": 40, "p": '+92-300-1100000', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Badin Relief Depot', "t": 'emergency_facility', "g": geo_ids['Badin'], "lo": 68.8150, "la": 24.6950, "c": 500, "p": '+92-21-9910000', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Dadu Civil Hospital', "t": 'hospital', "g": geo_ids['Dadu'], "lo": 67.7900, "la": 26.7500, "c": 240, "p": '+92-21-9900001', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Dadu', "t": 'rescue_center', "g": geo_ids['Dadu'], "lo": 67.7620, "la": 26.7180, "c": 45, "p": '+92-300-1100001', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Dadu Relief Depot', "t": 'emergency_facility', "g": geo_ids['Dadu'], "lo": 67.7550, "la": 26.7650, "c": 600, "p": '+92-21-9910001', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Dera Ghazi Khan Civil Hospital', "t": 'hospital', "g": geo_ids['Dera Ghazi Khan'], "lo": 70.6500, "la": 30.0800, "c": 280, "p": '+92-21-9900002', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Dera Ghazi Khan', "t": 'rescue_center', "g": geo_ids['Dera Ghazi Khan'], "lo": 70.6220, "la": 30.0480, "c": 50, "p": '+92-300-1100002', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Dera Ghazi Khan Relief Depot', "t": 'emergency_facility', "g": geo_ids['Dera Ghazi Khan'], "lo": 70.6150, "la": 30.0950, "c": 700, "p": '+92-21-9910002', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Ghotki Civil Hospital', "t": 'hospital', "g": geo_ids['Ghotki'], "lo": 69.3300, "la": 28.0200, "c": 320, "p": '+92-21-9900003', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Ghotki', "t": 'rescue_center', "g": geo_ids['Ghotki'], "lo": 69.3020, "la": 27.9880, "c": 55, "p": '+92-300-1100003', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Ghotki Relief Depot', "t": 'emergency_facility', "g": geo_ids['Ghotki'], "lo": 69.2950, "la": 28.0350, "c": 800, "p": '+92-21-9910003', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Hyderabad Civil Hospital', "t": 'hospital', "g": geo_ids['Hyderabad'], "lo": 68.3800, "la": 25.4200, "c": 360, "p": '+92-21-9900004', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Hyderabad', "t": 'rescue_center', "g": geo_ids['Hyderabad'], "lo": 68.3520, "la": 25.3880, "c": 60, "p": '+92-300-1100004', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Hyderabad Relief Depot', "t": 'emergency_facility', "g": geo_ids['Hyderabad'], "lo": 68.3450, "la": 25.4350, "c": 900, "p": '+92-21-9910004', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Jacobabad Civil Hospital', "t": 'hospital', "g": geo_ids['Jacobabad'], "lo": 68.4500, "la": 28.3000, "c": 400, "p": '+92-21-9900005', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Jacobabad', "t": 'rescue_center', "g": geo_ids['Jacobabad'], "lo": 68.4220, "la": 28.2680, "c": 65, "p": '+92-300-1100005', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Jacobabad Relief Depot', "t": 'emergency_facility', "g": geo_ids['Jacobabad'], "lo": 68.4150, "la": 28.3150, "c": 1000, "p": '+92-21-9910005', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Karachi Civil Hospital', "t": 'hospital', "g": geo_ids['Karachi'], "lo": 67.0200, "la": 24.8800, "c": 440, "p": '+92-21-9900006', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Karachi', "t": 'rescue_center', "g": geo_ids['Karachi'], "lo": 66.9920, "la": 24.8480, "c": 70, "p": '+92-300-1100006', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Karachi Relief Depot', "t": 'emergency_facility', "g": geo_ids['Karachi'], "lo": 66.9850, "la": 24.8950, "c": 1100, "p": '+92-21-9910006', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Karachi Jinnah Medical Complex', "t": 'hospital', "g": geo_ids['Karachi'], "lo": 67.0320, "la": 24.8300, "c": 650, "p": '+92-21-99201234', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Larkana Civil Hospital', "t": 'hospital', "g": geo_ids['Larkana'], "lo": 68.2200, "la": 27.5800, "c": 480, "p": '+92-21-9900007', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Larkana', "t": 'rescue_center', "g": geo_ids['Larkana'], "lo": 68.1920, "la": 27.5480, "c": 75, "p": '+92-300-1100007', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Larkana Relief Depot', "t": 'emergency_facility', "g": geo_ids['Larkana'], "lo": 68.1850, "la": 27.5950, "c": 1200, "p": '+92-21-9910007', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rajanpur Civil Hospital', "t": 'hospital', "g": geo_ids['Rajanpur'], "lo": 70.3300, "la": 29.1200, "c": 520, "p": '+92-21-9900008', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Rajanpur', "t": 'rescue_center', "g": geo_ids['Rajanpur'], "lo": 70.3020, "la": 29.0880, "c": 80, "p": '+92-300-1100008', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Rajanpur Relief Depot', "t": 'emergency_facility', "g": geo_ids['Rajanpur'], "lo": 70.2950, "la": 29.1350, "c": 1300, "p": '+92-21-9910008', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Shikarpur Civil Hospital', "t": 'hospital', "g": geo_ids['Shikarpur'], "lo": 68.6500, "la": 27.9800, "c": 560, "p": '+92-21-9900009', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Shikarpur', "t": 'rescue_center', "g": geo_ids['Shikarpur'], "lo": 68.6220, "la": 27.9480, "c": 85, "p": '+92-300-1100009', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Shikarpur Relief Depot', "t": 'emergency_facility', "g": geo_ids['Shikarpur'], "lo": 68.6150, "la": 27.9950, "c": 1400, "p": '+92-21-9910009', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Sukkur Civil Hospital', "t": 'hospital', "g": geo_ids['Sukkur'], "lo": 68.8700, "la": 27.7200, "c": 600, "p": '+92-21-9900010', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Sukkur', "t": 'rescue_center', "g": geo_ids['Sukkur'], "lo": 68.8420, "la": 27.6880, "c": 90, "p": '+92-300-1100010', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Sukkur Relief Depot', "t": 'emergency_facility', "g": geo_ids['Sukkur'], "lo": 68.8350, "la": 27.7350, "c": 1500, "p": '+92-21-9910010', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Thatta Civil Hospital', "t": 'hospital', "g": geo_ids['Thatta'], "lo": 67.9300, "la": 24.7700, "c": 640, "p": '+92-21-9900011', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'Rescue 1122 Station Thatta', "t": 'rescue_center', "g": geo_ids['Thatta'], "lo": 67.9020, "la": 24.7380, "c": 95, "p": '+92-300-1100011', "s": 'operational'})
    conn.execute(sa.text("INSERT INTO infrastructure (name, type, geographic_id, geom, capacity, contact_phone, operational_status, is_sample_data) VALUES (:n, :t, :g, ST_SetSRID(ST_MakePoint(:lo, :la), 4326), :c, :p, :s, true)"), {"n": 'PDMA Thatta Relief Depot', "t": 'emergency_facility', "g": geo_ids['Thatta'], "lo": 67.8950, "la": 24.7850, "c": 1600, "p": '+92-21-9910011', "s": 'operational'})
    # ---- seed: sample resource allocations ----
    auth_id = conn.execute(sa.text("SELECT id FROM users WHERE role = 'authority' ORDER BY created_at LIMIT 1")).scalar()
    conn.execute(sa.text("INSERT INTO resource_allocations (geographic_id, resource_type, quantity, allocated_by, status, notes) VALUES (:g, :r, :q, :a, :s, :n)"), {"g": geo_ids['Dadu'], "r": 'relief_kits', "q": 8000, "a": auth_id, "s": 'planned', "n": 'Pre-positioned for monsoon response'})
    conn.execute(sa.text("INSERT INTO resource_allocations (geographic_id, resource_type, quantity, allocated_by, status, notes) VALUES (:g, :r, :q, :a, :s, :n)"), {"g": geo_ids['Dadu'], "r": 'medical_teams', "q": 10, "a": auth_id, "s": 'planned', "n": 'Requested by district health office'})
    conn.execute(sa.text("INSERT INTO resource_allocations (geographic_id, resource_type, quantity, allocated_by, status, notes) VALUES (:g, :r, :q, :a, :s, :n)"), {"g": geo_ids['Larkana'], "r": 'relief_kits', "q": 7000, "a": auth_id, "s": 'dispatched', "n": 'Dispatched to district depot'})
    conn.execute(sa.text("INSERT INTO resource_allocations (geographic_id, resource_type, quantity, allocated_by, status, notes) VALUES (:g, :r, :q, :a, :s, :n)"), {"g": geo_ids['Jacobabad'], "r": 'boats', "q": 25, "a": auth_id, "s": 'planned', "n": 'Flood rescue boats'})
    conn.execute(sa.text("INSERT INTO resource_allocations (geographic_id, resource_type, quantity, allocated_by, status, notes) VALUES (:g, :r, :q, :a, :s, :n)"), {"g": geo_ids['Thatta'], "r": 'relief_kits', "q": 5500, "a": auth_id, "s": 'planned', "n": 'Coastal belt contingency stock'})
    conn.execute(sa.text("INSERT INTO resource_allocations (geographic_id, resource_type, quantity, allocated_by, status, notes) VALUES (:g, :r, :q, :a, :s, :n)"), {"g": geo_ids['Badin'], "r": 'medical_teams', "q": 6, "a": auth_id, "s": 'planned', "n": 'Mobile health units'})


def downgrade() -> None:
    op.drop_table("resource_allocations")
    op.drop_table("vulnerability_indicators")
    op.drop_table("infrastructure")
