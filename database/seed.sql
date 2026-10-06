-- ============================================================================
-- Flood Risk Prediction and Early Warning Decision Support System
-- Seed Data (Pakistan — Sindh focus + southern Punjab)
-- ============================================================================
-- Historical references: 2010 super floods, 2011 Sindh floods,
-- 2020 Karachi urban flooding, 2022 Pakistan floods.
--
-- Apply after schema.sql:
--   psql -d flood_risk_dss -f database/seed.sql
--
-- NOTE: demo password hashes are placeholders ('$2b$12$y/YmC7hEoTS15clks1lLH.lPAGIu.F.mHsbxn.vuBRi6tIUkHgPtK').
-- Replace with real bcrypt hashes before any deployment.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. GEOGRAPHIC DATA (12 assessment points, approximate real coordinates)
--    lon/lat are approximate district-centre values; elevation and Indus
--    river distances are plausible planning figures.
-- ----------------------------------------------------------------------------
INSERT INTO geographic_data
    (district_name, province, geom, latitude, longitude,
     elevation_m, river_distance_km, slope_deg,
     population_density_per_km2, vulnerability_index)
VALUES
    ('Dadu',     'Sindh',  ST_SetSRID(ST_MakePoint(67.78, 26.73), 4326), 26.73, 67.78, 62,  14.0, 1.2,  268, 0.82),
    ('Larkana',  'Sindh',  ST_SetSRID(ST_MakePoint(68.21, 27.56), 4326), 27.56, 68.21, 51,  26.0, 1.0,  420, 0.79),
    ('Sukkur',   'Sindh',  ST_SetSRID(ST_MakePoint(68.86, 27.70), 4326), 27.70, 68.86, 64,   3.5, 0.8,  530, 0.61),
    ('Hyderabad','Sindh',  ST_SetSRID(ST_MakePoint(68.37, 25.40), 4326), 25.40, 68.37, 21,  18.0, 0.9,  610, 0.66),
    ('Thatta',   'Sindh',  ST_SetSRID(ST_MakePoint(67.92, 24.75), 4326), 24.75, 67.92, 16,  24.0, 0.6,  175, 0.74),
    ('Badin',    'Sindh',  ST_SetSRID(ST_MakePoint(68.84, 24.66), 4326), 24.66, 68.84, 11,  38.0, 0.5,  265, 0.77),
    ('Ghotki',   'Sindh',  ST_SetSRID(ST_MakePoint(69.32, 28.00), 4326), 28.00, 69.32, 84,  10.0, 1.1,  255, 0.58),
    ('Karachi',  'Sindh',  ST_SetSRID(ST_MakePoint(67.01, 24.86), 4326), 24.86, 67.01,  8,  62.0, 0.7, 3650, 0.69),
    ('Jacobabad','Sindh',  ST_SetSRID(ST_MakePoint(68.44, 28.28), 4326), 28.28, 68.44, 55,  34.0, 0.9,  375, 0.81),
    ('Shikarpur','Sindh',  ST_SetSRID(ST_MakePoint(68.64, 27.96), 4326), 27.96, 68.64, 56,  19.0, 1.0,  480, 0.72),
    ('Rajanpur', 'Punjab', ST_SetSRID(ST_MakePoint(70.32, 29.10), 4326), 29.10, 70.32, 122,  9.0, 1.4,  160, 0.76),
    ('Dera Ghazi Khan', 'Punjab', ST_SetSRID(ST_MakePoint(70.64, 30.06), 4326), 30.06, 70.64, 137, 11.0, 1.6,  245, 0.71);

-- ----------------------------------------------------------------------------
-- 2. DEMO USERS (one per role)
-- ----------------------------------------------------------------------------
INSERT INTO users (name, email, password_hash, role, location_name, phone)
VALUES
    ('Farhan Iqbal',      'authority.demo@flooddss.pk', '$2b$12$y/YmC7hEoTS15clks1lLH.lPAGIu.F.mHsbxn.vuBRi6tIUkHgPtK', 'authority', 'Karachi, Sindh', '+92-21-9920-1234'),
    ('Sadia Rahman',      'ngo.demo@flooddss.pk',       '$2b$12$y/YmC7hEoTS15clks1lLH.lPAGIu.F.mHsbxn.vuBRi6tIUkHgPtK', 'ngo',       'Hyderabad, Sindh', '+92-22-921-5678'),
    ('Bilal Ahmed',       'public.demo@flooddss.pk',    '$2b$12$y/YmC7hEoTS15clks1lLH.lPAGIu.F.mHsbxn.vuBRi6tIUkHgPtK', 'public',    'Dadu, Sindh', '+92-300-1234567');

-- ----------------------------------------------------------------------------
-- 3. FLOOD EVENTS (49 rows across 2010, 2011, 2015, 2019-2024)
--    district_name lookups keep the seed readable.
-- ----------------------------------------------------------------------------

-- 2022 Pakistan floods (heavy coverage)
INSERT INTO flood_events (geographic_id, event_date, rainfall_mm, temperature_c, humidity_pct, severity, flood_status, damage_description, affected_population, source) VALUES
((SELECT id FROM geographic_data WHERE district_name='Dadu'),     '2022-08-21', 320.5, 33.2, 88.0, 5, TRUE, 'Monsoon cloudburst; Manchar Lake overflow inundated surrounding union councils.', 450000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Dadu'),     '2022-09-02', 285.0, 32.8, 90.0, 5, TRUE, 'Continued inflows; widespread displacement from low-lying villages.', 380000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Dadu'),     '2022-07-15', 140.2, 34.5, 82.0, 4, TRUE, 'Early monsoon flooding of seasonal streams.', 95000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Larkana'),  '2022-08-22', 298.4, 33.0, 89.0, 5, TRUE, 'Severe flooding in rural talukas; standing crops destroyed.', 410000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Larkana'),  '2022-09-01', 175.6, 32.5, 87.0, 4, TRUE, 'Prolonged waterlogging; road links cut off.', 180000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Thatta'),   '2022-08-24', 265.0, 32.0, 91.0, 5, TRUE, 'Tidal backflow plus rainfall flooded coastal belt villages.', 220000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Thatta'),   '2022-09-05', 150.8, 31.8, 88.0, 4, TRUE, 'Sustained flooding in delta region.', 110000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Badin'),    '2022-08-25', 240.3, 31.5, 92.0, 4, TRUE, 'Heavy rainfall overwhelmed drainage; saline water intrusion in fields.', 195000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Badin'),    '2022-09-03', 168.9, 31.2, 90.0, 4, TRUE, 'Continued waterlogging in low-lying union councils.', 140000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Jacobabad'),'2022-08-20', 310.7, 34.0, 85.0, 5, TRUE, 'Record rainfall; entire city and surrounding villages submerged.', 360000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Jacobabad'),'2022-07-12', 155.4, 36.5, 78.0, 4, TRUE, 'Pre-monsoon flash flooding from hill torrents.', 70000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Shikarpur'),'2022-08-23', 220.1, 33.4, 87.0, 4, TRUE, 'Breaches in irrigation channels flooded farmland.', 150000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Sukkur'),   '2022-08-26', 190.5, 33.1, 86.0, 4, TRUE, 'Urban flooding; Indus at high flood level near Sukkur Barrage.', 120000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Hyderabad'),'2022-08-27', 205.8, 32.4, 89.0, 4, TRUE, 'Urban drainage overflow; several colonies inundated.', 135000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Hyderabad'),'2022-09-04', 120.6, 31.9, 85.0, 3, TRUE, 'Localized flooding in low-lying neighbourhoods.', 45000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Rajanpur'),'2022-08-15', 260.2, 33.8, 84.0, 5, TRUE, 'Hill torrents from Sulaiman Range devastated settlements.', 310000, 'PDMA Punjab report'),
((SELECT id FROM geographic_data WHERE district_name='Rajanpur'),'2022-07-20', 145.7, 35.2, 76.0, 4, TRUE, 'Early monsoon torrent flooding in tribal areas.', 85000, 'PDMA Punjab report'),
((SELECT id FROM geographic_data WHERE district_name='Dera Ghazi Khan'),'2022-08-16', 245.9, 34.1, 83.0, 5, TRUE, 'Major hill-torrent flooding; bridges and roads damaged.', 290000, 'PDMA Punjab report'),
((SELECT id FROM geographic_data WHERE district_name='Dera Ghazi Khan'),'2022-07-22', 138.3, 35.8, 75.0, 4, TRUE, 'Flash flooding in western tehsils.', 78000, 'PDMA Punjab report'),
((SELECT id FROM geographic_data WHERE district_name='Ghotki'),    '2022-08-18', 165.2, 34.8, 80.0, 3, TRUE, 'Flooding along riverine belt; kacha areas affected.', 62000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Karachi'),  '2022-07-10', 142.5, 31.5, 87.0, 3, TRUE, 'Monsoon urban flooding; underpasses and low areas submerged.', 55000, 'NDMA monsoon update');

-- 2010 super floods
INSERT INTO flood_events (geographic_id, event_date, rainfall_mm, temperature_c, humidity_pct, severity, flood_status, damage_description, affected_population, source) VALUES
((SELECT id FROM geographic_data WHERE district_name='Ghotki'),    '2010-08-05', 280.0, 34.2, 85.0, 5, TRUE, 'Indus super flood; mass evacuation from riverine areas.', 520000, 'NDMA 2010 flood report'),
((SELECT id FROM geographic_data WHERE district_name='Sukkur'),   '2010-08-07', 265.5, 34.0, 86.0, 5, TRUE, 'Record Indus discharge at Sukkur Barrage; protective bunds breached.', 480000, 'NDMA 2010 flood report'),
((SELECT id FROM geographic_data WHERE district_name='Jacobabad'),'2010-08-09', 250.8, 33.8, 87.0, 5, TRUE, 'Catastrophic flooding; city cut off for weeks.', 390000, 'NDMA 2010 flood report'),
((SELECT id FROM geographic_data WHERE district_name='Shikarpur'),'2010-08-10', 235.4, 33.6, 86.0, 5, TRUE, 'Widespread inundation of agricultural land.', 340000, 'NDMA 2010 flood report'),
((SELECT id FROM geographic_data WHERE district_name='Rajanpur'),'2010-07-28', 290.6, 34.5, 84.0, 5, TRUE, 'Combined river and hill-torrent flooding.', 370000, 'PDMA Punjab 2010 report'),
((SELECT id FROM geographic_data WHERE district_name='Dera Ghazi Khan'),'2010-07-30', 275.3, 34.8, 83.0, 5, TRUE, 'Indus and hill torrents devastated western Punjab.', 350000, 'PDMA Punjab 2010 report'),
((SELECT id FROM geographic_data WHERE district_name='Dadu'),     '2010-08-12', 210.9, 33.2, 88.0, 4, TRUE, 'Flooding along the western bank of the Indus.', 160000, 'NDMA 2010 flood report'),
((SELECT id FROM geographic_data WHERE district_name='Larkana'),  '2010-08-14', 195.7, 33.0, 87.0, 4, TRUE, 'Prolonged flooding in rural talukas.', 140000, 'NDMA 2010 flood report'),
((SELECT id FROM geographic_data WHERE district_name='Karachi'),  '2010-07-27',  98.2, 32.0, 82.0, 2, TRUE, 'Moderate monsoon rains; minor urban disruption.', 12000, 'NDMA 2010 flood report');

-- 2011 Sindh floods
INSERT INTO flood_events (geographic_id, event_date, rainfall_mm, temperature_c, humidity_pct, severity, flood_status, damage_description, affected_population, source) VALUES
((SELECT id FROM geographic_data WHERE district_name='Badin'),    '2011-08-22', 310.2, 31.8, 93.0, 5, TRUE, 'Exceptional monsoon rains; worst-hit district of 2011 floods.', 430000, 'NDMA 2011 flood assessment'),
((SELECT id FROM geographic_data WHERE district_name='Thatta'),   '2011-08-25', 285.6, 31.5, 92.0, 5, TRUE, 'Severe flooding in coastal and riverine areas.', 360000, 'NDMA 2011 flood assessment'),
((SELECT id FROM geographic_data WHERE district_name='Hyderabad'),'2011-09-01', 230.4, 31.2, 90.0, 4, TRUE, 'Heavy rains flooded urban and rural areas.', 210000, 'NDMA 2011 flood assessment'),
((SELECT id FROM geographic_data WHERE district_name='Dadu'),     '2011-09-05', 205.8, 32.0, 89.0, 4, TRUE, 'Flooding in low-lying union councils.', 170000, 'PDMA Sindh 2011 report'),
((SELECT id FROM geographic_data WHERE district_name='Larkana'),  '2011-09-08', 190.3, 31.8, 88.0, 4, TRUE, 'Waterlogging destroyed cotton and rice crops.', 150000, 'PDMA Sindh 2011 report'),
((SELECT id FROM geographic_data WHERE district_name='Sukkur'),   '2011-08-28', 160.7, 32.5, 87.0, 3, TRUE, 'Moderate flooding; drainage channels overflowed.', 70000, 'PDMA Sindh 2011 report');

-- 2020 Karachi urban flooding
INSERT INTO flood_events (geographic_id, event_date, rainfall_mm, temperature_c, humidity_pct, severity, flood_status, damage_description, affected_population, source) VALUES
((SELECT id FROM geographic_data WHERE district_name='Karachi'),  '2020-08-25', 230.0, 30.5, 92.0, 4, TRUE, 'Record monsoon spell; storm drains overflowed across the city.', 180000, 'NDMA 2020 monsoon report'),
((SELECT id FROM geographic_data WHERE district_name='Karachi'),  '2020-08-27', 185.5, 30.2, 91.0, 4, TRUE, 'Second spell; Malir and Lyari river corridors flooded.', 120000, 'NDMA 2020 monsoon report'),
((SELECT id FROM geographic_data WHERE district_name='Karachi'),  '2020-07-19', 110.4, 31.8, 86.0, 3, TRUE, 'Early monsoon urban flooding.', 38000, 'NDMA 2020 monsoon report');

-- Other monsoon seasons (2015, 2019, 2021, 2023, 2024)
INSERT INTO flood_events (geographic_id, event_date, rainfall_mm, temperature_c, humidity_pct, severity, flood_status, damage_description, affected_population, source) VALUES
((SELECT id FROM geographic_data WHERE district_name='Karachi'),  '2015-07-30', 135.2, 32.5, 84.0, 3, TRUE, 'Monsoon urban flooding; traffic disrupted.', 42000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Thatta'),   '2015-08-10', 128.6, 31.5, 88.0, 3, TRUE, 'Seasonal flooding in delta villages.', 35000, 'PDMA Sindh report'),
((SELECT id FROM geographic_data WHERE district_name='Rajanpur'),'2015-07-25', 172.4, 34.2, 80.0, 4, TRUE, 'Hill-torrent flooding damaged homes and crops.', 92000, 'PDMA Punjab report'),
((SELECT id FROM geographic_data WHERE district_name='Karachi'),  '2019-08-10', 145.8, 31.2, 89.0, 3, TRUE, 'Monsoon spell; nullahs overflowed in several towns.', 48000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Badin'),    '2019-08-15', 152.3, 31.0, 90.0, 3, TRUE, 'Heavy rains caused localized flooding.', 52000, 'PDMA Sindh report'),
((SELECT id FROM geographic_data WHERE district_name='Dera Ghazi Khan'),'2019-07-28', 168.1, 34.8, 78.0, 3, TRUE, 'Flash flooding from western hill torrents.', 60000, 'PDMA Punjab report'),
((SELECT id FROM geographic_data WHERE district_name='Thatta'),   '2021-08-20',  95.4, 32.2, 85.0, 2, TRUE, 'Moderate seasonal rains; minor field flooding.', 15000, 'PDMA Sindh report'),
((SELECT id FROM geographic_data WHERE district_name='Hyderabad'),'2021-08-22',  88.7, 32.8, 83.0, 2, TRUE, 'Moderate monsoon rains; brief waterlogging.', 12000, 'PDMA Sindh report'),
((SELECT id FROM geographic_data WHERE district_name='Larkana'),  '2023-08-12', 158.9, 33.5, 86.0, 3, TRUE, 'Monsoon flooding in rural talukas.', 68000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Sukkur'),   '2023-08-14', 102.5, 34.0, 82.0, 2, TRUE, 'Moderate rains; Indus within banks.', 18000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Karachi'),  '2023-08-05',  96.3, 31.5, 87.0, 2, TRUE, 'Monsoon urban waterlogging in low areas.', 22000, 'NDMA monsoon update'),
((SELECT id FROM geographic_data WHERE district_name='Badin'),    '2024-08-18', 148.2, 31.4, 89.0, 3, TRUE, 'Monsoon flooding; drainage relief operations launched.', 58000, 'PDMA Sindh situation report'),
((SELECT id FROM geographic_data WHERE district_name='Dadu'),     '2024-08-20', 105.6, 33.0, 85.0, 2, TRUE, 'Seasonal rains; minor flooding near Manchar Lake.', 20000, 'PDMA Sindh situation report');

-- ----------------------------------------------------------------------------
-- 4. SHELTERS (6)
-- ----------------------------------------------------------------------------
INSERT INTO shelters (name, geographic_id, geom, capacity, facilities, contact_phone) VALUES
('Dadu District Relief Camp - Model School',        (SELECT id FROM geographic_data WHERE district_name='Dadu'),     ST_SetSRID(ST_MakePoint(67.79, 26.74), 4326), 1500, ARRAY['Drinking water','Medical tent','Food kitchen','Sanitation'], '+92-259-9200123'),
('Mehar Taluka Shelter Hall',                       (SELECT id FROM geographic_data WHERE district_name='Dadu'),     ST_SetSRID(ST_MakePoint(67.72, 26.82), 4326),  800, ARRAY['Drinking water','Food kitchen','Sanitation'], '+92-259-9200456'),
('Larkana Emergency Shelter - Public School No. 4', (SELECT id FROM geographic_data WHERE district_name='Larkana'),  ST_SetSRID(ST_MakePoint(68.22, 27.55), 4326), 1200, ARRAY['Drinking water','Medical tent','Food kitchen'], '+92-74-9410789'),
('Thatta Coastal Evacuation Centre',                (SELECT id FROM geographic_data WHERE district_name='Thatta'),   ST_SetSRID(ST_MakePoint(67.93, 24.76), 4326),  900, ARRAY['Drinking water','Medical tent','Sanitation'], '+92-298-9200334'),
('Karachi Relief Centre - Expo Site Hall',          (SELECT id FROM geographic_data WHERE district_name='Karachi'),  ST_SetSRID(ST_MakePoint(67.06, 24.90), 4326), 2500, ARRAY['Drinking water','Medical tent','Food kitchen','Sanitation','Power backup'], '+92-21-9920-5566'),
('Rajanpur Flood Relief Camp',                      (SELECT id FROM geographic_data WHERE district_name='Rajanpur'), ST_SetSRID(ST_MakePoint(70.33, 29.11), 4326), 1000, ARRAY['Drinking water','Food kitchen','Sanitation'], '+92-604-7800123');

-- ----------------------------------------------------------------------------
-- 5. EMERGENCY CONTACTS (8)
-- ----------------------------------------------------------------------------
INSERT INTO emergency_contacts (name, organization, phone, district_name) VALUES
('NDMA Emergency Operations Centre', 'National Disaster Management Authority', '111-157-157', NULL),
('PDMA Sindh Control Room',          'Provincial Disaster Management Authority Sindh', '021-9933-2747', NULL),
('PDMA Punjab Control Room',          'Provincial Disaster Management Authority Punjab', '042-9920-4444', NULL),
('Rescue 1122 Sindh',                 'Rescue 1122', '1122', NULL),
('Pakistan Red Crescent Society',     'Pakistan Red Crescent Society', '051-925-0404', NULL),
('District Emergency Office Dadu',    'District Administration Dadu', '025-9200-111', 'Dadu'),
('District Emergency Office Larkana', 'District Administration Larkana', '074-9410-222', 'Larkana'),
('Karachi Commissioner Control Room', 'Commissioner Office Karachi', '021-9920-3333', 'Karachi');

-- ----------------------------------------------------------------------------
-- 6. SAMPLE PREDICTIONS (4) — machine learning-based risk outputs
-- ----------------------------------------------------------------------------
INSERT INTO predictions (geographic_id, model_version, probability, risk_level, input_features, main_factors, recommendations, created_by) VALUES
((SELECT id FROM geographic_data WHERE district_name='Dadu'),
 'rf-v1.2', 0.82, 'HIGH',
 '{"rainfall_mm": 310.0, "temperature_c": 33.5, "humidity_pct": 89.0, "elevation_m": 62.0, "river_distance_km": 14.0, "slope_deg": 1.2, "population_density_per_km2": 268.0, "vulnerability_index": 0.82, "prev_flood_events_10y": 7}'::JSONB,
 ARRAY['Heavy rainfall', 'Low elevation', 'River proximity', 'High social vulnerability'],
 ARRAY['Prepare evacuation plans', 'Monitor water levels', 'Contact emergency services', 'Pre-position relief supplies at designated shelters'],
 (SELECT id FROM users WHERE email='authority.demo@flooddss.pk')),
((SELECT id FROM geographic_data WHERE district_name='Larkana'),
 'xgb-v1.2', 0.45, 'MEDIUM',
 '{"rainfall_mm": 165.0, "temperature_c": 33.0, "humidity_pct": 84.0, "elevation_m": 51.0, "river_distance_km": 26.0, "slope_deg": 1.0, "population_density_per_km2": 420.0, "vulnerability_index": 0.79, "prev_flood_events_10y": 6}'::JSONB,
 ARRAY['Moderate rainfall', 'Flat terrain', 'High social vulnerability'],
 ARRAY['Monitor weather forecasts', 'Check drainage channels', 'Keep emergency kits ready'],
 (SELECT id FROM users WHERE email='authority.demo@flooddss.pk')),
((SELECT id FROM geographic_data WHERE district_name='Karachi'),
 'ann-v1.0', 0.12, 'LOW',
 '{"rainfall_mm": 60.0, "temperature_c": 31.0, "humidity_pct": 75.0, "elevation_m": 8.0, "river_distance_km": 62.0, "slope_deg": 0.7, "population_density_per_km2": 3650.0, "vulnerability_index": 0.69, "prev_flood_events_10y": 5}'::JSONB,
 ARRAY['Low forecast rainfall', 'Distance from Indus river'],
 ARRAY['No immediate action required', 'Continue routine monitoring'],
 (SELECT id FROM users WHERE email='authority.demo@flooddss.pk')),
((SELECT id FROM geographic_data WHERE district_name='Rajanpur'),
 'rf-v1.2', 0.77, 'HIGH',
 '{"rainfall_mm": 255.0, "temperature_c": 34.0, "humidity_pct": 83.0, "elevation_m": 122.0, "river_distance_km": 9.0, "slope_deg": 1.4, "population_density_per_km2": 160.0, "vulnerability_index": 0.76, "prev_flood_events_10y": 6}'::JSONB,
 ARRAY['Heavy rainfall', 'Hill-torrent exposure', 'River proximity'],
 ARRAY['Prepare evacuation plans', 'Monitor hill-torrent streams', 'Contact emergency services', 'Alert downstream communities'],
 (SELECT id FROM users WHERE email='authority.demo@flooddss.pk'));

-- ----------------------------------------------------------------------------
-- 7. ACTIVE ALERTS (3)
-- ----------------------------------------------------------------------------
INSERT INTO alerts (geographic_id, title, message, severity, is_active, issued_at, expires_at) VALUES
((SELECT id FROM geographic_data WHERE district_name='Dadu'),
 'Flood Emergency: Dadu District',
 'Heavy rainfall detected. Flood risk increased in your area. Water levels in Manchar Lake are rising. Residents in low-lying union councils should prepare for possible evacuation.',
 'emergency', TRUE, '2026-09-20 06:00:00+05', '2026-10-05 06:00:00+05'),
((SELECT id FROM geographic_data WHERE district_name='Larkana'),
 'Flood Warning: Larkana District',
 'Moderate to heavy rainfall forecast over the next 48 hours. Monitor local weather updates and keep emergency kits ready.',
 'warning', TRUE, '2026-09-24 09:30:00+05', '2026-10-05 09:30:00+05'),
((SELECT id FROM geographic_data WHERE district_name='Karachi'),
 'Rain Watch: Karachi',
 'Scattered monsoon showers expected. Minor urban waterlogging possible in low-lying areas during peak rainfall.',
 'watch', TRUE, '2026-09-25 12:00:00+05', '2026-09-30 12:00:00+05');
