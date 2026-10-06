# A Machine Learning-Based Flood Risk Prediction and GIS Decision Support Framework for Disaster Risk Reduction: A Case Study of Sindh, Pakistan

---

**Complete Project Report**

**Author:** Aadil Ali Mahar
BS Computer Science, The Islamia University of Bahawalpur, 2022–2026

*Prepared in support of the Master's in Disaster Management application*

**Date:** September 2026

---

> **Terminology note.** Throughout this report, the predictive capabilities
> of the system are described only as *machine learning-based prediction*,
> *data-driven prediction*, *risk assessment*, and *decision support* — per
> a standing project rule on system naming.

---

## Table of Contents

1. [Abstract](#abstract)
2. [Introduction](#introduction)
3. [Problem Statement](#problem-statement)
4. [Research Objectives](#research-objectives)
5. [Literature Review](#literature-review)
6. [Research Gap](#research-gap)
7. [Methodology](#methodology)
8. [System Architecture](#system-architecture)
9. [Dataset Description](#dataset-description)
10. [Feature Engineering](#feature-engineering)
11. [Prediction Models](#prediction-models)
12. [GIS Framework](#gis-framework)
13. [Early Warning Workflow](#early-warning-workflow)
14. [Mobile Application](#mobile-application)
15. [Results](#results)
16. [Discussion](#discussion)
17. [Limitations](#limitations)
18. [Future Work](#future-work)
19. [Conclusion](#conclusion)
20. [References](#references)
21. [Appendices](#appendices)

---

## Abstract

Floods are the most frequent and destructive natural hazard in Pakistan.
The 2010 super floods and the 2022 monsoon floods each displaced millions,
and Sindh has repeatedly borne the heaviest losses. Disaster management
authorities in the Indus basin still rely heavily on rainfall thresholds
and qualitative assessments when deciding where to pre-position relief,
issue advisories, and plan evacuations.

This report documents a complete, open-source Flood Risk Prediction and
Early Warning Decision Support System: machine learning-based flood risk
prediction, GIS visualisation, an automated early warning cycle, and
verified community reporting in a single operational platform, evaluated
on a purpose-built dataset covering 12 districts of Sindh and adjacent
Punjab border districts over the monsoon years 2010–2024.

A district-year research dataset of 180 rows (43 labelled flood years)
was constructed from 43 verified flood events with per-row source
citations, ERA5 reanalysis weather aggregates via the Open-Meteo archive
API, static geographic attributes, and a documented composite
vulnerability index. Three classifiers were compared on a stratified
80/20 held-out test set (n = 36) with 5-fold cross-validation: Random
Forest (F1 0.615, ROC-AUC 0.955), XGBoost (F1 0.800, ROC-AUC 0.947), and
a multilayer perceptron (F1 0.875, ROC-AUC 0.963). All three achieved
perfect precision with imperfect recall — a conservative early-warning
behaviour: a raised flag is trustworthy, while the absence of a flag is
not a guarantee of safety.

The best model is deployed behind a FastAPI prediction service with a
versioned model registry, a PostgreSQL 16 / PostGIS 3.4 spatial database,
a Leaflet web dashboard with decision-support summaries and trend
analysis, a Flutter community mobile application, and an automated early
warning loop (forecast ingestion → prediction → alert decision with
cooldown and escalation → push notification). Every prediction and every
automated alert is persisted with model version, probability, and
contributing factors, making all outputs fully auditable.

Limitations are documented explicitly: reporting bias in the flood
inventory, a small positive sample (43 flood years), provisional
vulnerability weights, sample infrastructure data, train/serve shift
between ERA5 reanalysis and forecast-API weather, and the gap between
seasonal (district-year) models and event-scale API inputs. The framework
shows how machine learning, GIS, and community participation can be
integrated to advance the disaster-risk understanding and preparedness
for effective response called for by the Sendai Framework (Priorities 1
and 4).

**Keywords:** flood risk prediction; machine learning; GIS; early warning
systems; decision support; disaster risk reduction; Sindh; Pakistan; Sendai
Framework.

---

## Introduction

### 1.1 Background

Pakistan is among the countries most exposed to flood hazard. The 2010
super floods affected more than 20 million people, submerging roughly a
fifth of the country's land area; the 2022 monsoon floods killed 1,700+,
displaced about 8 million, and caused damages exceeding USD 30 billion,
with Sindh and Balochistan worst affected. Between them lie recurrent
monsoon disasters — 2011, 2015, 2020, and others — striking substantially
the same districts again and again.

Three flood mechanisms operate in Sindh. **Riverine flooding** — the Indus
overtopping banks or breaching embankments — inundates the low-lying
floodplain districts of Dadu, Larkana, Shikarpur, Jacobabad, Sukkur, and
Ghotki. **Urban and flash flooding** — intense, short-duration downpours
overwhelming drainage — is the Karachi August 2020 canonical case:
disaster-scale impacts with no riverine overflow. **Coastal and tidal
flooding**, compounded by sea intrusion, affects deltaic Badin and Thatta.
District-level risk assessment in the province remains largely
qualitative, fragmented across agencies, and difficult for at-risk
communities to access.

### 1.2 The decision problem

Flood forecasting in Pakistan is not absent: the Flood Forecasting Division
issues Indus river-flow forecasts, the NDMA/PDMA/DDMA system coordinates
preparedness and response, and global systems such as GloFAS provide
ensemble flood outlooks. The difficulty is translation — converting
forecasts into *district-level, decision-ready risk information*: which
districts to warn, where to pre-position relief, which shelters to open.
That conversion is performed manually, under monsoon-season time pressure,
with no standardised, explainable, auditable district-level risk product
in routine use. This is the "last mile" problem of early warning: warnings
exist but never become local decisions, or arrive too late or in
unactionable form. A system that produces maps but no alerts, probabilities
but no explanations, models but no audit trail does not solve the problem
it was built for — which is why this project treats the last mile as the
primary design constraint.

### 1.3 Project overview

This report documents the Flood Risk Prediction and Early Warning Decision
Support System, developed in seven phases: schema and FastAPI backend; a
live database-backed prediction pipeline; a purpose-built 2010–2024
research dataset with three-model comparison; GIS intelligence and
decision support; a community mobile application; real-time early warning
automation; and research validation and publication.

The artefact is a three-tier operational platform: a data layer
(PostgreSQL 16 + PostGIS 3.4), a service layer (FastAPI with JWT
authentication and role-based access control for the roles authority, NGO,
public, and volunteer), and a client layer (a Leaflet web dashboard, a
Flutter community mobile application, and automated push notifications).
Machine learning models are versioned in a file-based registry outside the
application package so that retraining, deployment, and the API evolve
independently. Every prediction is persisted with its model version,
probability, contributing factors, and recommendations; every automated
alert stores its model provenance — requirements for any predictive tool
that informs public-safety decisions.

### 1.4 Scope and intended use

The study area is 12 districts (ten in Sindh plus two Punjab border
districts, included because Indus riverine flooding crosses the provincial
boundary) over the 15 monsoon years 2010–2024, at district-year grain. The
system is a decision *support* tool: it produces risk assessments,
explanations, and alerts for human officers to act on. It does not predict
exact flood timing, depth, or inundation extent, and operational deployment
and field trials are out of scope for this phase (see Section 18).

---

## Problem Statement

District authorities in Sindh lack timely, location-specific,
decision-ready flood risk information — not for absence of data (NDMA
situation reports, PDMA flood impact reports, meteorological records, and
media archives document decades of flood events), but because of the form
in which information reaches the people who must act. The problem has five
interlocking dimensions, each addressed by a component of this system.

**First, forecasts are not decisions.** National and global forecasting
products speak in river discharges, ensemble percentiles, and coarse grids
(GloFAS: ~0.1° resolution). A district officer needs to know whether to
open shelters in Dadu or warn villages along the Indus in Shikarpur — and
that conversion is performed manually, under monsoon-season time pressure,
with no standardised, explainable, auditable district-level risk product
in routine use.

**Second, institutional memory is personal, not systematic.** The strongest
predictor of where floods strike in Sindh is where they struck before — a
finding this project's own modelling reproduces — yet that knowledge lives
in officers' heads and scattered PDF reports, not in a queryable system.
A verified, citable flood event inventory with per-row source citations
converts personal memory into institutional memory.

**Third, vulnerability is discussed qualitatively and acted on unevenly.**
District planning often reduces to rainfall watch and past-experience
heuristics; no widely used quantitative vulnerability product at district
scale for Sindh combines exposure, historical susceptibility, and physical
proximity to hazard — which is why this project builds a documented
(provisional) composite vulnerability index and combines it with live risk
into decision priorities.

**Fourth, communities are warning recipients, not participants.** Ground
observations — rising water in a nullah, a breached embankment — travel
upward slowly, by phone and word of mouth. Verified community reporting
addresses this asymmetry, while the verification step guards against
rumours becoming official situational awareness.

**Fifth, predictive research stops at the map.** The literature reports
ROC-AUC values of 0.85–0.97 for flood susceptibility mapping, but studies
overwhelmingly end with offline maps: no API, no alerting loop, no audit
trail, no community channel. A susceptibility map, however accurate, has
never opened a single shelter.

Formally, the problem is: **how to convert verified flood histories,
reanalysis weather, and geographic data into district-level, explainable,
auditable flood risk information that flows automatically into warnings,
resource decisions, and community awareness in Sindh, Pakistan.**

---

## Research Objectives

The research objectives translate the problem statement into verifiable
deliverables:

1. **Build a reproducible, fully documented district-level flood dataset
   for Sindh (2010–2024)** — per-event source citations, a published data
   card, build scripts, and a recorded SHA-256 hash, so every result is
   traceable to the exact bytes it was learned from.
2. **Compare machine learning classifiers with honest uncertainty
   reporting** — at least three model families on a held-out test set
   with cross-validation; confidence bands, confusion matrices, and
   feature importances reported, not hidden.
3. **Integrate the best model into an operational GIS-based decision
   support and automated early warning platform** — versioned-registry
   prediction API, spatial risk visualisation, a scheduled warning cycle
   with cooldown and escalation, full provenance persisted for audit.
4. **Provide verified community participation channels** — geolocated,
   categorised, photo-evidenced flood reports via a mobile app, with an
   authority verification workflow ensuring unverified claims never become
   official situational awareness.
5. **Evaluate against disaster-management needs** — beyond model metrics:
   the test suite, live verification of the warning cycle, and documented
   limitations bounding every operational claim.

### Research questions

1. Which combination of environmental, geographic, and historical
   indicators best predicts flood occurrence at the district level in
   Sindh?
2. How accurately can machine learning-based classifiers distinguish flood
   from non-flood district-years, and with what uncertainty?
3. How can predicted risk be communicated through GIS and early warning
   interfaces for three distinct user groups — authorities, NGOs, and the
   public?
4. What decision-support outputs (risk factors, recommendations, resource
   views, trend analysis) are most useful to disaster management
   practitioners?

---

## Literature Review

### 2.1 Disaster risk management frameworks

The normative anchor of this work is the **Sendai Framework for Disaster
Risk Reduction 2015–2030**: Priorities 1 (understanding disaster risk)
and 4 (enhancing preparedness for effective response), and Global Target
(g) — substantially increasing access to multi-hazard early warning
systems. This project contributes to both: a quantitative, explainable
model of district flood risk embedded in an automated warning and
response-support loop.

Pakistan's institutional architecture is anchored by the **National
Disaster Management Authority (NDMA)**, with **Provincial Disaster
Management Authorities (PDMAs)** — including PDMA Sindh — responsible for
provincial preparedness and response, and **District Disaster Management
Authorities (DDMAs)** at district level. The National Flood Protection
Plan and post-2010/post-2022 policy reviews repeatedly identify the same
weaknesses: late or spatially coarse warnings, weak district-level
capacity, poor integration of community observations. The 2022 floods
showed that even where national forecasts existed, district authorities
lacked localised, decision-ready risk information.

### 2.2 Flood hazard in the Indus basin

The South Asian summer monsoon drives the Indus flood cycle: intense
June–September rainfall over the Himalayan and Sulaiman catchments swells
the Indus while direct monsoon rain adds local flooding. The 2010 super
floods and the 2022 monsoon floods define the national experience — over
20 million affected in 2010; 1,700+ killed, ~8 million displaced, damages
above USD 30 billion in 2022, Sindh worst hit in both. In both events the
districts that suffered most were substantially the same set — a pattern
of repeated exposure this project's modelling quantifies, and that
practitioners have long encoded as "past floods predict future floods."

### 2.3 Flood early warning systems

**GloFAS** (Global Flood Awareness System) provides ensemble flood
forecasts up to 30 days ahead, but at ~0.1° resolution with limited skill
for flash and urban flooding in South Asia — continental awareness, not
district operations. Regionally, the **Flood Forecasting Division of the
Pakistan Meteorological Department** issues Indus river-flow forecasts,
the backbone of official outlooks. At community scale, **ICIMOD's
community-based flood early warning systems** in the Hindu Kush Himalaya
show the value of local observation networks. The persistent pattern is
the **last-mile problem**: forecasts exist, but translation into local
decisions and community action is weak. The recommended remedy —
integrating official forecasts with community reporting and decision
support — is this project's design.

### 2.4 Machine learning for flood prediction

Machine learning is now standard in flood susceptibility mapping.
**Random Forest** dominates the applied literature for its robustness on
tabular environmental data and native feature importance; **XGBoost** is
typically the strongest tabular performer in head-to-head comparisons; and
**multilayer perceptrons (MLPs)** perform competitively where continuous
rainfall interactions are informative. Comparative studies across Iran,
Bangladesh, and China report ROC-AUC values of 0.85–0.97 — the benchmark
range for the results in Section 11.

Four recurring methodological concerns shape this project's design:
**small positive samples** (flood inventories are short; confidence bands
are wide and often under-reported); **reporting bias** (inventories record
*documented* floods, so the negative class is really "no documented
flood"); **spatial and temporal leakage** (random splits over space-time
data can leak future or neighbouring information into training); and the
**offline-map gap** (studies end at susceptibility maps and never reach
operational use). This project answers with a fully documented,
reproducible dataset with per-event citations, explicit treatment of
these validity threats, and deployment inside an operational early
warning and decision support platform.

### 2.5 GIS in disaster management

GIS is the operational backbone of modern disaster management: hazard
mapping, exposure and vulnerability analysis, shelter and resource
management, and evacuation planning all depend on spatial integration of
heterogeneous data. PostGIS-backed web GIS with Leaflet-class clients is a
mature, low-cost stack widely used by humanitarian agencies. Beyond
visualisation, disaster-management GIS centres on **decision layers**:
vulnerability-weighted priority maps, resource maps, and trend views for
pre-monsoon planning. This project's GIS module adds exactly these
decision-oriented views, designed around the questions a DDMA officer
asks before the monsoon.

### 2.6 Community participation and citizen reporting

Crowdsourced crisis mapping, in the tradition of Ushahidi's deployment
after the 2010 Haiti earthquake, has shown that affected communities are
the fastest sensors of ground truth — but brings validity concerns:
reporting bias (reports cluster where phones are), the digital divide, and
misinformation risk. The design response is a **verification workflow**:
reports enter as *pending*, pass through authority triage (verified /
rejected / resolved), and only verified reports enter official situational
awareness. No automated public warning is ever triggered by a citizen
report alone.

### 2.7 Conceptual framework

The project's logic is a chain: **hazard** (monsoon rainfall, river
proximity, terrain) → **exposure** (population in harm's way) →
**vulnerability** (composite susceptibility) → **risk** (modelled
probability × level) → **decision** (alerts, priorities, resource
allocation) → **action** (warnings issued, shelters opened, relief
pre-positioned) → **feedback** (verified community reports, new events
entering the inventory). Machine learning operates on the first three
links; GIS and decision support on the fourth and fifth; the early
warning cycle and mobile app on the sixth; the verification workflow
closes the seventh, feeding ground truth back into institutional memory.

---

## Research Gap

The literature is rich in components and poor in integration. The
research gap has four parts.

**Gap 1 — No integrated, open-source, district-scale stack for Sindh.**
Susceptibility studies produce offline maps; forecasting agencies produce
river-flow outlooks; humanitarian teams produce shelter maps. No
published, open-source system combines machine learning-based district
risk prediction, GIS decision support, automated alerting, and community
reporting in one reproducible codebase for Sindh. The pieces exist in
different institutions; the integration — where the last-mile problem
lives — has not been done.

**Gap 2 — Reproducibility is asserted, not demonstrated.** Studies describe
data sources in prose ("NDMA reports") without per-event citations, data
cards, or dataset hashes. When the inventory cannot be audited, a model
built on it cannot be trusted for public-safety decisions. This project's
per-row citations, data card, build scripts, and registry-recorded
SHA-256 set a provenance standard the regional literature does not meet.

**Gap 3 — Uncertainty is hidden, not reported.** Small-sample studies
report point metrics without confidence bands or confusion matrices,
implying a precision the data cannot support. This project reports CV F1
standard deviations of 0.09–0.21 prominently and documents every threat
to validity — because a Master's-level contribution must not overstate
what 43 positive samples can support.

**Gap 4 — The seasonal-to-operational bridge is missing.** District-year
classifiers answer "will this district flood this monsoon?"; operations
need event-scale answers. The literature rarely confronts this mismatch —
most studies simply do not deploy. This project deploys, documents the
mismatch honestly, and pairs the trained models with a transparent
deterministic rule-based engine for the automated cycle.

A fifth, softer gap concerns **community participation**: crowdsourced
reporting exists in crisis-mapping literature but is seldom integrated
with official warning workflows in a single verified system. This
project's citizen-report module fills that integration gap for Sindh.

---

## Methodology

This project follows a quantitative computational research design with a
design-science orientation: the artefact — the decision support system — is
both the research instrument and a primary research output. Seven build
phases map onto research stages: schema and API (infrastructure), live
prediction pipeline (instrumentation), research dataset and model
comparison (the core empirical study), GIS and decision support
(translation into practice), mobile application (community channel), early
warning automation (operational loop), and research validation and
publication.

### 3.1 Study area and period

Twelve districts — Badin, Dadu, Ghotki, Hyderabad, Jacobabad, Karachi,
Larkana, Shikarpur, Sukkur, Thatta (Sindh), plus Dera Ghazi Khan and
Rajanpur (Punjab border districts, included because Indus riverine
flooding crosses the provincial boundary; flagged as non-Sindh in
analysis) — over the 15 monsoon years 2010–2024, capturing the 2010 super
floods, the 2022 monsoon floods, and the recurrent disasters between them.

### 3.2 Analytical grain and labelling

Floods in Sindh are monsoon-season phenomena, so the honest analytical
unit is the **monsoon year**: one row per district per year (180 rows;
43 positive, 23.9%). The alternative — one row per district-event window —
would require exact event-day weather for every historical flood
(unavailable for most rows) and would leave no honest negative class. The
district-year design yields a real negative class (137 district-years,
76.1%) and matches operational use: a district's current monsoon outlook.
Labels: `flooded` = 1 if ≥1 verified event in the district-year, else 0;
`severity` = maximum verified severity (1–5), 0 if none.

### 3.3 Data collection

The inventory comprises 43 verified district-level flood records for
2010–2022 (`datasets/raw/sindh_flood_events_2010_2024.csv`), sourced under
an explicit hierarchy — NDMA situation reports, PDMA Sindh flood impact
reporting, WHO worst-affected district lists, Pakistan Met Department
records, Dawn/ReliefWeb/OCHA/IFRC situation reports — with **every row
carrying its own `source` citation and `source_url`**. Daily weather
(precipitation, temperature, humidity) for 2010-01-01–2024-12-31 comes
from ERA5 reanalysis via the Open-Meteo archive API (raw JSON cached per
district); static geographic attributes (elevation, river distance, slope,
population density) come from the `geographic_data` table.

### 3.4 Feature engineering

Ten base features from domain knowledge — monsoon rainfall sum,
temperature, humidity (hazard drivers); elevation, river distance, slope,
population density (static exposure); `prev_flood_events` and
`last_severity` on strictly earlier years plus a composite vulnerability
index (historical susceptibility) — with four interaction terms added at
training time: `rain_intensity` (rainfall × humidity), `lowland_river`
(elevation × river proximity), `exposure_index` (log-density × flood
history), and `flood_history_score`. The vulnerability composite is
provisional — a reasoned prior, documented and not fitted:

```
vulnerability_index = 0.5 · minmax(log1p(population_density))
                    + 0.3 · minmax(total verified events 2010–2024)
                    + 0.2 · minmax(1 / (1 + river_distance_km))
```

### 3.5 Modelling and evaluation

Preprocessing: median imputation, IQR outlier capping on rainfall and
elevation, standardisation — all parameters fitted on training data only
and persisted per model. Design: stratified 80/20 split (144/36,
`random_state=42`); 5-fold stratified cross-validation on the training
set scoring F1 (appropriate for the 23.9% minority class); imbalance
handled via `class_weight=balanced` (RF) and F1-based model selection.
Three classifiers: Random Forest (300 trees, `class_weight=balanced`),
XGBoost (300 rounds, max_depth 6, lr 0.05, subsample/colsample 0.9), MLP
((64, 32), max_iter 800) — strong literature-consistent defaults, not
aggressively tuned, to avoid overfitting 144 training rows. Metrics:
accuracy, precision, recall, F1, ROC-AUC on the held-out set; CV F1 mean
± std for uncertainty. Interpretability: built-in importances (trees),
permutation importance for the MLP (10 repeats, F1, held-out set);
per-prediction feature contributions from the API.

### 3.6 GIS and decision-support methods

SRID 4326 throughout, `Geometry(POINT, 4326)` by convention. Predicted
probabilities join district geography in PostGIS and are served as GeoJSON
risk layers (HIGH ≥ 0.66, MEDIUM 0.33–0.66, LOW < 0.33). A vulnerability
priority combines the composite index with live risk into
CRITICAL/HIGH/MEDIUM/LOW classes. Trends aggregate documented events by
district-year (2010–2024) and by month, exposing the July–September
seasonal concentration.

### 3.7 System evaluation

Multi-level: statistical validation (held-out metrics, CV, confusion
matrices); software testing (119 backend tests against a disposable test
database; 7 Flutter tests; clean `flutter analyze`); live smoke tests of
the warning cycle (12/12 districts evaluated, advisories stored); and
dashboard exercise against the live API with demo fallback. Field
evaluation with practitioners is future work.

### 3.8 Research ethics

All flood and weather data come from public institutional sources or
documented reanalysis products; no personal data are used in modelling.
Citizen reporting is voluntary; reports pass through authority
verification; no automated public warning is ever issued from a citizen
report alone; reporter identities are subject to data minimisation.

### 3.9 Threats to validity

Seven threats, each mitigated and each with residue: (1) reporting bias —
per-row citations, "no *documented* flood" labelling; (2) small sample —
honest uncertainty reporting instead of oversampling tricks; (3) ERA5
smoothing of extremes — documented; (4) static density — documented; (5)
provisional vulnerability weights — reasoned, not validated; (6)
seasonal-vs-event-scale gap — documented, with the rule-based engine as
the operational bridge; (7) temporal leakage — history features use
strictly earlier years, but the stratified split mixes years, so a
temporal holdout (train ≤2019, test 2020–2024) is recommended.

---

## System Architecture

The system is a three-tier platform: a **data layer** (PostgreSQL 16 +
PostGIS 3.4), a **service layer** (FastAPI), and **client applications**
(web dashboard, Flutter mobile app, automated scheduler). Machine learning
models are versioned in a file-based registry outside the application
package (`ml-models/registry.json` plus `ml-models/models/<name>-v1/`
artefacts) so that retraining, deployment, and the API can evolve
independently. The architecture diagram is provided as
`figures/system-architecture.png`.

### 4.1 Data layer

PostgreSQL 16 with PostGIS 3.4. All tables use UUID primary keys; every
spatial column uses `Geometry(POINT, 4326)` by project convention. The
schema (Alembic migrations 0001–0005) covers core tables (`users`,
`geographic_data`, `flood_events`, `risk_assessments`, `predictions`,
`alerts`, `emergency_contacts`, `shelters`), observations and boundaries
(`weather_observations`, `district_boundaries`), GIS and decision support
(`infrastructure`, `vulnerability_indicators`, `resource_allocations`),
and community/notification tables (`citizen_reports`, `device_tokens`).
Seed data provides the 12 districts, 52 historical flood events
(including the 2022 Pakistan floods), demo users, and sample
infrastructure rows explicitly flagged `is_sample_data`.

### 4.2 Service layer (FastAPI)

| Service | Module | Responsibility |
|---|---|---|
| Authentication & RBAC | `core/security.py`, `api/v1/auth.py` | JWT access/refresh; bcrypt; roles authority / ngo / public / volunteer |
| Prediction service | `services/prediction_service.py` | Versioned registry + rule-based fallback; persists every assessment |
| Risk engine | `services/risk_engine.py` | Deterministic v1 weighted scorer |
| GIS | `api/v1/gis.py` | GeoJSON layers: risk, historical, vulnerability, infrastructure, boundaries |
| Decision support | `api/v1/decision_support.py` | Summary, year-wise trends, resource allocation |
| Alert engine | `services/alert_engine.py` | LOW → none, MEDIUM → advisory, HIGH → emergency; 6h cooldown + escalation |
| Weather ingestion | `services/weather_ingestion.py` | Open-Meteo forecast → `weather_observations` (idempotent upserts) |
| Notifications | `services/notifications.py` | FCM; degraded log-only mode without credentials |
| CSV/GeoJSON import | `services/importers/` | Validated, authority-only bulk import with dry-run |
| Scheduler | `app/main.py` lifespan (APScheduler) | Warning cycle every `EW_CYCLE_MINUTES` (30) when enabled |

Security is enforced pervasively: role guards on every mutating endpoint,
authority-only import, alert, and verification workflows, and secure token
handling. Reproducibility is structural: the dataset SHA-256 is recorded in
the model registry, Alembic versions the schema, and the test suite (119
backend tests) runs against a disposable test database.

### 4.3 Machine learning subsystem

Training code lives in `backend/ml/` (modular pipeline; CLIs
`train.py` and `train_phase3.py`; dataset builder `build_dataset.py`;
weather fetcher `fetch_weather.py`). Artefacts live in `ml-models/`:
`registry.json` (configuration, features, preprocessing, metrics,
confusion matrix, dataset SHA-256) plus per-model directories with
`model.joblib`, `feature_names.json`, `preprocessing.json`,
`metrics.json`, `feature_importance.json`, and `confusion_matrix.png`.
Five servable entries: `rule-based-v1` (deterministic), `rf-v1` (legacy),
`randomforest-v1`, `xgboost-v1`, `mlp-v1` (best test F1 0.8750, ROC-AUC
0.9630), plus aliases (`randomforest`, `xgboost`, `mlp`). The service
resolves the registry via `MODEL_DIR` / `MODEL_REGISTRY_PATH`,
defaulting to repo-root `ml-models/`.

### 4.4 Clients and integrations

The web dashboard prototype (`frontend/prototype/`) provides a Leaflet
risk map with layer toggles, district search, decision-support charts, and
an Authority Alert Center, talking to the live API with a demo fallback.
The Flutter mobile app (`mobile/`, Flutter 3.47.5) provides community
access: risk assessment, GIS map, alerts, emergency resources, an offline
safety guide, and verified reporting. External integrations are Open-Meteo
(weather; free tier) and Firebase Cloud Messaging (push; service-account
JSON required for production). Deployment is via `docker-compose.yml`
(API + PostGIS); the scheduler is single-instance by design.

---

## Dataset Description

The training dataset (`datasets/processed/sindh_training_2010_2024.csv`,
version 1.0, built 2026-09-26) was constructed specifically for this study
by `backend/ml/build_dataset.py` and is fully documented in
`datasets/processed/DATA_CARD.md`. Its SHA-256 hash,
`4b478ea58d6af1f91dd65540bc32cb3e770badc428313c779d76b2700418fb62`, is
recorded in the model registry, so every trained model is traceable to the
exact bytes it learned from.

### 5.1 Study area, period, and grain

The dataset covers the 12 study districts over the 15 monsoon years
2010–2024 at district-year grain: **180 rows**, **43 (23.9%)** positive
(≥1 verified flood event in the district-year), 137 (76.1%) negative. The
district-year design is the only honest analytical unit available: exact
event-day weather is unavailable for most historical floods, and the
alternative (one row per district-event window) would leave no honest
negative class. The grain also matches operational use: the prediction API
assesses a district's current monsoon outlook.

### 5.2 Sources

| Data | Source | Access |
|---|---|---|
| 43 verified district-level flood records (2010–2022) | NDMA situation reports, PDMA Sindh Flood Impact Report 2022, WHO worst-affected district lists, Pakistan Met Department records, Dawn/ReliefWeb/OCHA/IFRC situation reports | `datasets/raw/sindh_flood_events_2010_2024.csv`; every row carries its own `source` citation and `source_url` |
| Daily weather, 2010-01-01–2024-12-31 (precipitation, temperature, humidity) | ERA5 reanalysis via the Open-Meteo archive API | Raw JSON cached in `datasets/raw/weather/<district>.json` |
| Elevation, river distance, slope, population density | Project `geographic_data` table | Static snapshot in `datasets/raw/district_static.csv` |

The source hierarchy (NDMA > PDMA > WHO > Met Department > media/ReliefWeb)
is applied consistently, and per-row citations make the inventory auditable
— the provenance standard identified as missing in the regional literature
(Research Gap 2).

### 5.3 Features

The ten base features are defined precisely in the data card:

| Feature | Definition |
|---|---|
| `rainfall_mm` | Monsoon-season (Jun–Sep) precipitation sum, mm (ERA5 `precipitation_sum`) |
| `temperature_c` | Monsoon-season mean of daily mean temperature, °C (ERA5) |
| `humidity_pct` | Monsoon-season mean of daily mean relative humidity, % (ERA5) |
| `elevation_m` | District mean elevation above sea level, m (static) |
| `river_distance_km` | Distance to nearest major river (Indus), km (static) |
| `slope_deg` | Mean terrain slope, degrees (static) |
| `population_density` | Persons per km² (static; time-invariant proxy) |
| `prev_flood_events` | Count of verified flood events in the same district in strictly earlier years |
| `last_severity` | Maximum severity (1–5) of verified events in strictly earlier years; 0 if none |
| `vulnerability_index` | Composite, static per district (provisional formula, Section 3.4) |

Contextual columns carried for provenance (not model inputs) include
`district_name`, `year`, `rainfall_annual_mm`, `rainfall_max_daily_mm`, and
`n_events_in_year`. Labels are `flooded` (binary) and `severity` (0–5
ordinal maximum).

### 5.4 Known limitations and biases

The data card documents seven limitations explicitly: **reporting
bias** (negative = "no *documented* flood"; positives skew catastrophic);
**no pre-2010 history** (`prev_flood_events` for 2010 rows is 0 by
construction); **static population density** across 15 years, ignoring
urbanisation; **ERA5 reanalysis, not station data** (smoothed extremes;
bilinear centroid estimates); **ordinal, source-dependent severity**
(1–5 from narrative reports, not a calibrated scale); **small sample**
(180 rows / 43 positives, wide confidence bands); and a **provisional
vulnerability composite** (reasoned weights, not fitted or validated).

### 5.5 Reproducibility

The dataset is rebuildable with two commands — `fetch_weather.py`
then `build_dataset.py` — followed by `sha256sum` verification against
the registry hash: the practical answer to Research Gap 2.

---

## Feature Engineering

Features were designed from disaster-management domain knowledge rather
than selected by automated search, so that every model input has a
physical or institutional interpretation an officer can understand.

### 6.1 Base features

The ten base features (Section 5.3) fall into three groups. **Hazard
drivers**: monsoon rainfall sum, mean temperature, mean humidity — the
physical forcing. **Static exposure**: elevation, river distance, slope,
population density. **Historical susceptibility**: `prev_flood_events`
and `last_severity` on strictly earlier years (no future leakage into a
row's history features), plus the composite vulnerability index.

### 6.2 Engineered interaction features

Four interaction terms are added at training time to capture compounding
effects that linear features miss:

- **`rain_intensity`** — rainfall × humidity: intense rain in saturated
  air, the compound driver of both riverine and urban flooding.
- **`lowland_river`** — elevation × river proximity: low-lying floodplain
  near the Indus, where overbank flow first reaches settlements.
- **`exposure_index`** — log-density × flood history: people exposed
  where floods have struck before, the human-impact potential.
- **`flood_history_score`** — a weighted summary of past events giving
  recent floods higher influence, encoding the institutional-memory
  insight that recent disasters predict near-term risk better than old
  ones.

### 6.3 The vulnerability composite

The composite vulnerability index combines three normalised components:

```
vulnerability_index = 0.5 · minmax(log1p(population_density))
                    + 0.3 · minmax(total verified events 2010–2024)
                    + 0.2 · minmax(1 / (1 + river_distance_km))
```

The components capture exposure (people in harm's way), historical
susceptibility (past floods predict future floods), and physical exposure
(Indus proximity). Density is log-transformed — it spans 160–3,650
persons/km², and without the transform Karachi alone saturates the
component. The weights are a reasoned prior (exposure dominant), not
fitted or externally validated: the index is presented throughout as a
documented provisional composite, never as a measured socioeconomic
index. It is nevertheless informative — in the MLP it carries a
permutation importance of 0.09 (Section 15).

### 6.4 Preprocessing

Median imputation, IQR outlier capping on rainfall and elevation, and
standardisation — all parameters fitted on training data only and
persisted per model (`preprocessing.json`), so serving-time inputs
undergo exactly the transformation the model was trained with.

---

## Prediction Models

### 7.1 Model set and registry

Five servable model entries are registered in `ml-models/registry.json`
(see Appendix C for the full extract):

- **`rule-based-v1`** (version `v1.0.0-rule-based`) — a deterministic
  weighted risk scoring engine over nine normalised features with fixed
  weights. Transparent, always available, and the default for the automated
  early warning cycle, where determinism is valued over marginal accuracy.
- **`rf-v1`** (legacy) — Random Forest (300 trees) trained on live
  database records: 52 documented flood events plus 36 synthetic non-flood
  observations across 12 districts (88 rows, trained 2026-09-26). Metrics
  of 1.0 across accuracy/precision/recall/F1/ROC-AUC (CV F1 0.9749 ±
  0.0308) are flagged in the registry as optimistic — the synthetic
  negative class inflates them. Preserved untouched for backward
  compatibility.
- **`randomforest-v1`**, **`xgboost-v1`**, **`mlp-v1`** — the three Phase 3
  research models trained on the Sindh 2010–2024 district-year dataset
  (180 rows), each recording the dataset SHA-256
  `4b478ea5…0418fb62` in its registry entry. Convenience aliases
  `randomforest`, `xgboost`, and `mlp` resolve to the versioned entries.
  The API serves all of them via `POST /api/v1/risk/predict?model=<name>`;
  unknown model names return HTTP 200 with an explanatory note and a
  rule-based fallback rather than an error.

**Training configuration.** All three research models were trained with
`backend/ml/train_phase3.py` on the stratified 80/20 split (144 train /
36 test, `random_state=42`):

- **randomforest-v1**: Random Forest, 300 trees, `class_weight=balanced`.
- **xgboost-v1**: XGBoost, 300 rounds, max_depth 6, lr 0.05,
  subsample/colsample 0.9.
- **mlp-v1**: MLP, hidden layers (64, 32), max_iter 800.

Hyperparameters are strong, literature-consistent defaults — deliberate
on 144 training rows, where tuning risks overfitting the validation
folds. Validation is 5-fold stratified CV scoring F1. Importance:
built-in (Gini/gain) for the trees; permutation importance (10 repeats,
F1, held-out set) for the MLP.

### 7.3 Per-prediction explanations

Every ML prediction carries `feature_contributions` (top 5) alongside
probability and risk level. The method is descriptive, not causal:
contribution = normalised feature importance × |z-score| of the
(preprocessed, engineered) input against the training distribution,
re-normalised to sum to 1 — answering "which features pushed *this*
prediction away from the average input?" Example (xgboost-v1,
high-rainfall input): `rainfall_mm` 0.30, `rain_intensity` 0.21,
`slope_deg` 0.10, `vulnerability_index` 0.06, `flood_history_score` 0.05.
The deterministic engine's `main_factors` labels are preserved alongside.
This per-prediction explainability makes outputs auditable: an authority
sees not only that a district is HIGH risk, but which measurable
conditions drove the assessment.

### 7.4 Model selection for operations

The automated early warning cycle defaults to `rule-based-v1` because it
is transparent and deterministic. The trained models, with `mlp-v1` as
best performer, serve analyst-driven assessment through the same API.
This two-tier arrangement is the pragmatic answer to the
seasonal-to-operational gap: the trained classifiers are district-year
(seasonal) models, so event-scale inputs yield indicative rather than
validated sub-seasonal outputs (Section 17).

---

## GIS Framework

The GIS module (Phase 4) turns predictions into spatial, decision-oriented
products. All geometry is stored in SRID 4326 (WGS 84); the API converts
PostGIS geometries to GeoJSON server-side, and the Leaflet 1.9.4 client
renders them without further transformation. Every GIS endpoint requires
JWT authentication; decision-support endpoints additionally enforce the
authority/NGO role matrix.

### 8.1 Spatial layers

| Layer | Endpoint | Source tables | Notes |
|---|---|---|---|
| Risk | `/api/v1/gis/risk-layer`, `/api/v1/gis/risk-layers` | `predictions` ⨝ `geographic_data` | Latest prediction per district; `NO_DATA` when none exists |
| Historical floods | `/api/v1/gis/historical-floods`, `/api/v1/gis/historical-layers` | `flood_events` ⨝ `geographic_data` | Documented events; severity 1–5 with labels |
| Vulnerability map | `/api/v1/gis/vulnerability-map` | `vulnerability_indicators` ⨝ `geographic_data` (+ latest prediction) | Phase 3 composite index combined with current risk |
| Infrastructure | `/api/v1/gis/infrastructure` | `infrastructure` ⨝ `geographic_data` | Hospitals, rescue centres, emergency facilities; seed rows flagged `is_sample_data` |
| Shelters | `/api/v1/gis/shelters` | `shelters` ⨝ `geographic_data` | Relief camps with capacity and facilities |
| District boundaries | `/api/v1/gis/boundaries` | `district_boundaries` | Polygons when the boundaries dataset is imported |
| Emergency contacts | `/api/v1/gis/emergency-contacts` | `emergency_contacts` | Directory (JSON, not GeoJSON) |
| Districts | `/api/v1/gis/districts` | `geographic_data` | District list for dropdowns and GPS matching |

Infrastructure seed rows are marked sample data (`is_sample_data = true`)
— plausible names/positions offset from district centroids — and must be
replaced with authoritative PDMA / Health Department registries before
operational use; the API surfaces the flag so the UI can warn users.

### 8.2 Risk classification and vulnerability priority

Districts are coloured from their latest stored prediction: **HIGH**
(probability ≥ 0.66, red), **MEDIUM** (0.33 ≤ p < 0.66, amber), **LOW**
(p < 0.33, green) — thresholds shared with the risk engine and the
trained classifiers' decision boundaries. The decision priority combines
the composite vulnerability index with current risk:

- **CRITICAL** — HIGH risk **and** vulnerability_index ≥ 0.33
- **HIGH** — HIGH risk, **or** vulnerability_index ≥ 0.40
- **MEDIUM** — MEDIUM risk, **or** vulnerability_index ≥ 0.25
- **LOW** — otherwise

The priority logic is implemented once and shared by the map and the
decision-support summary, so the two views can never disagree.

### 8.3 Decision support workflow

The workflow runs in six steps: (1) **data** — district attributes,
weather, documented flood history; (2) **prediction** —
`/risk/predict?model=…` returns probability + risk level, persisted;
(3) **explanation** — per-feature contributions (or stored main factors);
(4) **action** — rule-based recommendations per risk level; (5)
**resources** — shelters with capacity, infrastructure by type,
allocations by status, hotspots; (6) **review** — trends and seasonal
patterns for pre-monsoon planning. `GET /api/v1/decision-support/summary`
packages steps 2–5 into one operational view: high-risk districts with
explanations and actions, active alerts, latest predictions with model
versions, resource overview, and hotspots. Authority role additionally
gets the full allocation list and may record new allocations
(`POST /api/v1/decision-support/resources`).

### 8.4 Trend and seasonal analysis

`GET /api/v1/decision-support/trends` aggregates `flood_events` by
district and year (2010–2024). The trend indicator compares mean yearly
event counts for 2017–2024 against 2010–2016 (±25% bands); the seasonal
pattern counts events per calendar month, exposing the July–September
monsoon concentration. Counts reflect *documented* events only — the
reporting bias in the data card propagates into trends, and the endpoint
documentation says so.

### 8.5 Frontend map

`frontend/prototype/index.html` hosts the Decision Support view and the
GIS map page: independent layer toggles; district popups with risk
probability/level, contributing factors, recommended actions,
vulnerability priority, and shelter capacity; district search; and
dependency-free inline SVG time charts (year-wise totals, monthly
seasonal pattern). The dashboard consumes the live API with built-in
demo data when the API is unreachable.

---

## Early Warning Workflow

The automated early warning loop (Phase 6) converts weather forecasts
into district alerts without human intervention, keeping every automated
decision auditable.

### 9.1 The cycle

```
Open-Meteo forecast ──▶ weather_observations ──▶ PredictionService ──▶ risk level
                                                                              │
                                              ┌───────────────────────────────┴───────────────────────────────┐
                                              │ LOW → nothing                                                 │
                                              │ MEDIUM → advisory notification (watch)                        │
                                              │ HIGH → emergency warning (emergency)                          │
                                              └───────────────────────────────┬───────────────────────────────┘
                                                                              ▼
                                              alerts table ──▶ FCM push + inboxes
```

The components are: **weather ingestion**
(`app/services/weather_ingestion.py`, `scripts/ingest_weather.py`) —
Open-Meteo current + hourly forecast for all 12 districts, idempotent
upserts; the **APScheduler scheduler** in the `app/main.py` lifespan,
cycling every `EW_CYCLE_MINUTES` (default 30) when
`EW_SCHEDULER_ENABLED=true`; the **alert engine**
(`app/services/alert_engine.py`) — weather → prediction → decision per
district; **notifications** (`app/services/notifications.py`) — FCM with
degraded log-only mode without credentials; and **device tokens**
(`POST/DELETE /mobile/device-token`), multicast on alert.

### 9.2 Alert decision rules

| Prediction | Alert issued | `alerts.severity` |
|---|---|---|
| LOW | none | — |
| MEDIUM | advisory notification | `watch` |
| HIGH | emergency warning | `emergency` |

Two control mechanisms prevent alert fatigue and stale warnings.
**Cooldown**: no second alert at the same level within
`EW_ALERT_COOLDOWN_HOURS` (default 6); repeated HIGH readings inside the
window are suppressed and the existing active alert stands.
**Escalation**: MEDIUM → HIGH always issues immediately, even inside the
cooldown window, and the superseded advisory is deactivated
(`is_active=false`) so residents never see a stale advisory next to a live
emergency. Every automated alert stores `model_version`, `probability`,
and `factors`, so authorities can audit exactly why an alert fired.

### 9.3 Configuration

Environment variables (in `backend/.env`): `EW_SCHEDULER_ENABLED`
(default `false` — off in development/tests, on in production),
`EW_CYCLE_MINUTES` (30), `EW_ALERT_COOLDOWN_HOURS` (6),
`EW_DEFAULT_MODEL` (`rule-based-v1`), `EW_FORECAST_DAYS` (2). A cycle can
be driven manually via `alert_engine.run_early_warning_cycle()`, weather
ingestion alone via `scripts/ingest_weather.py`. The cycle was verified
live: all 12 study districts evaluated, advisories issued and stored.

### 9.4 Push notifications

In production mode, `FCM_SERVICE_ACCOUNT_PATH` points to a Firebase
service-account JSON with Cloud Messaging rights, and each alert
multicasts to every registered device token. Without credentials —
development, tests — notifications fall back to log-only: the payload is
logged, nothing is sent, and the cycle continues. The Flutter app has
token register/unregister ready; the remaining native Firebase wiring is
documented as a production integration step. Until then, the app inbox
(`GET /mobile/alerts`) remains the reliable alert channel.

### 9.5 Citizen-report verification workflow

Running in parallel with the automated loop is the community feedback
loop. Reports via `POST /mobile/report-event` carry a category
(`flood_water`, `road_blockage`, `rescue_request`, `medical_emergency`),
an optional photo (jpg/png/webp, ≤ 5 MB, stored under
`backend/uploads/reports/`), GPS coordinates, and a severity estimate.
Reports enter as **pending** and pass through authority triage —
**verified** (with `verified_by`, `verified_at`, `verification_note`),
**rejected** (invalid/duplicate, with a note), or **resolved** — via
`GET/PATCH /admin/reports`. The authority **Alert Center** in the web
prototype provides the triage queue with status filters, a manual
alert-creation form, and alert history with model provenance. No automated
public warning is ever triggered by a citizen report alone; reports enrich
human situational awareness while the alert engine alone fires warnings.

---

## Mobile Application

The Flutter community mobile application (Phase 5, Flutter 3.47.5) puts
risk information directly in citizens' and volunteers' hands — the safety
guide fully offline. Quality gates verified 2026-09-26: `flutter analyze`
clean, `flutter test` 7/7 passing (API client incl. 401-refresh rotation,
login, safety guide), `flutter build web --release` succeeding. (APK
packaging needs the Android SDK, not installed in this environment; the
passing web build proves the Dart compiles.)

### 10.1 Architecture

The app follows a pragmatic feature-first clean architecture:
`core/` (Dio API client with JWT attach and refresh-on-401, secure token
storage, offline cache via shared_preferences, typed errors) and
`features/` for auth, home, risk, map, alerts, emergency, and safety. JWT
access + refresh pairs are issued at login; the interceptor rotates the
pair on a single 401 and retries once. Registration supports `public`,
`volunteer`, and `ngo` roles; `authority` accounts are created by
administrators. The offline design serves the last cached payload on
network failure with an on-screen banner; the safety guide is bundled as
a Dart constant and always available.

### 10.2 Screens and workflows

Eight screens cover the community workflow: **Splash** (branding,
session restore); **Login/Register** (email + password, role picker);
**Home** (GPS → nearest district risk: level, probability, last update,
top factors, recommendations); **Risk assessment** (district dropdown or GPS plus weather inputs →
prediction with contributing factors, `POST /risk/predict?model=`
defaulting to `mlp-v1`); **GIS map**
(flutter_map with color-coded risk zones, shelters, hospitals/rescue
centres from live GeoJSON); **Alerts** (active warnings, newest first);
**Emergency** (nearby shelters sorted by distance with tap-to-call, rescue
contacts including Rescue 1122, and the flood-sighting report form); and
the offline **Safety guide** (before/during/after preparedness, emergency
kit, helplines). Every screen implements loading, error (with retry), and
empty states. A volunteer session adds the report flow: describe observed
flooding with severity 1–5 and GPS; the report is stored as `pending` for
authority triage.

### 10.3 Backend support

Alembic migration 0004 adds the `volunteer` role and the
`citizen_reports` table. The `/mobile/*` router exposes my-risk,
alerts, shelters/nearby, emergency-contacts, report-event, image upload,
device-token register/unregister, and reports/mine — all authenticated;
`POST /mobile/report-event` is restricted to volunteer/public/ngo
(authority → 403). Mobile API backend tests: 13 passing.

### 10.4 Limitations

Map tiles need network (OpenStreetMap); markers and cached data work
offline. GPS district matching uses centroids. Report submission needs
connectivity (offline queuing planned). `is_sample_data` infrastructure
points are illustrative until replaced by authoritative registries. App
alerts are pull-based; FCM integration is the documented next step.

---

## Results

### 11.1 Model comparison (held-out test set, n = 36)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | CV F1 (mean ± std) |
|---|---|---|---|---|---|---|
| randomforest-v1 | 0.8611 | 1.0000 | 0.4444 | 0.6154 | 0.9547 | 0.6147 ± 0.2073 |
| xgboost-v1 | 0.9167 | 1.0000 | 0.6667 | 0.8000 | 0.9465 | 0.6974 ± 0.0935 |
| **mlp-v1** | **0.9444** | 1.0000 | **0.7778** | **0.8750** | **0.9630** | **0.8028 ± 0.1110** |

Confusion matrices (rows = actual, columns = predicted `[no-flood,
flood]`): Random Forest `[[27, 0], [5, 4]]`; XGBoost `[[27, 0], [3, 6]]`;
MLP `[[27, 0], [2, 7]]` (visualised in `figures/model-comparison.png`).
Three readings follow.

**No false alarms, some missed events.** All three models achieve perfect
precision but miss 2–5 of the 9 flood years — consistent with the data's
limits: monsoon-season totals smooth over the short, intense downpours
behind urban flooding (e.g. Karachi 2020), and moderate events are
under-reported in the label sources.

**Ranking is stable across metrics.** mlp-v1 ≥ xgboost-v1 ≥
randomforest-v1 on F1, recall, accuracy, and CV F1. ROC-AUC exceeds 0.94
for all three — within the literature's 0.85–0.97 range — showing good
ranking ability even where the 0.5 threshold is conservative.

**Honest uncertainty.** CV F1 standard deviations (0.09–0.21) reflect the
small sample (144 training rows, 34 positives): fold composition changes
results materially. These are reported, not hidden.

### 11.2 Feature importance

Top features per model (normalised; method noted):

- **randomforest-v1** (built-in): `rainfall_mm` 0.20, `rain_intensity`
  0.17, `temperature_c` 0.14, `exposure_index` 0.09 — weather-driven.
- **xgboost-v1** (built-in): `flood_history_score` 0.20,
  `prev_flood_events` 0.13, `rainfall_mm` 0.11, `population_density`
  0.08 — history-driven, consistent with Indus-basin operational
  experience.
- **mlp-v1** (permutation): `rainfall_mm` 0.27, `rain_intensity` 0.17,
  `temperature_c` 0.13, `vulnerability_index` 0.09 — rainfall-dominated,
  with the vulnerability composite contributing measurably.

The disagreement between model families is itself informative: tree
ensembles split on history while the network leans on rainfall — which is
why the API serves all of them rather than a single model family.

### 11.3 GIS and decision-support findings

The vulnerability-priority logic combines the Phase 3 composite index
with live risk so map and dashboard always agree on where officers should
look first. Trend analysis over 2010–2024 exposes the July–September
seasonal concentration of documented events for pre-monsoon planning; the
±25% trend bands guard against over-reading noisy counts. Both products
carry the reporting-bias caveat: they summarise documented events, not
all floods.

### 11.4 System evaluation

Backend tests: 119/119 passing against a disposable test database;
Flutter: 7/7 with clean `flutter analyze`. The warning cycle was verified
live: all 12 districts evaluated, advisories stored with model provenance.
Dashboard decision-support views were exercised against the live API, with
the demo fallback confirming graceful degradation. Not yet evaluated:
field performance with PDMA/DDMA officers and community user-acceptance
testing (future work).

---

## Discussion

**Why the MLP won on recall.** The MLP's smooth decision surface appears
better suited to the continuous rainfall–humidity interactions separating
flood from non-flood monsoon years; the tree ensembles' axis-aligned
splits plus the conservative 0.5 threshold miss more marginal flood years.
All three rank well (ROC-AUC > 0.94) — the signal is present; the
threshold is what is conservative. Threshold tuning, done with authorities
in the loop, is therefore the cheapest lever for changing the operating
point.

**Conservative early warning.** Perfect precision with imperfect recall
makes the system a trustworthy flagger: a raised flag is reliable, but
absence of a flag is not absence of risk. This is the safer failure mode
for automated advisories — false alarms erode public trust — but it
mandates human review of borderline outlooks, communicated honestly to
authorities.

**Agreement with practitioner knowledge.** The models reproduce the two
signals disaster managers already use — monsoon rainfall intensity and
flood history, with history dominant in the best tree model. A model that
contradicted decades of Indus-basin experience would be suspect; one that
quantifies it, makes it queryable, and attaches uncertainty bands is
useful. The vulnerability composite's MLP contribution (0.09) suggests
exposure-weighted prioritisation adds signal — while remaining
provisional.

**Uncertainty is a result, not a footnote.** CV F1 standard deviations of
0.09–0.21 bound every operational claim: the system is a decision *aid*
requiring human review, not an oracle. The audit trail — every prediction
persisted with model version, probability, and contributing factors; every
alert with model provenance — lets reviewers interrogate the reasoning
rather than accept or reject it blindly.

**Deployment implication.** The API serves all three trained models plus
the rule-based engine; the automated cycle defaults to the rule-based
engine for determinism, with `mlp-v1` for analyst-driven assessment. The
single-instance scheduler, multicast push, and log-mode FCM are documented
limits a production deployment must resolve (Section 18).

**Comparison with related work.** This framework differs as an integrated
operational stack rather than an offline map; it is reproducible by
construction (data card, per-row citations, registry, SHA-256); and it
closes the loop with community reporting and automated alerting. Its
ROC-AUC values (0.9465–0.9630) sit at the top of the literature's
0.85–0.97 range — with the caveat that the small sample widens the
confidence bands.

---

## Limitations

1. **Seasonal vs. event scale.** The trained models are district-year
   (seasonal) classifiers, but the prediction API accepts event-scale
   inputs. This mismatch is documented, not hidden: event-scale outputs
   are indicative, not validated sub-seasonal claims. Reframing around
   district-season inputs or collecting sub-seasonal labels is priority
   future work.
2. **Small positive sample.** 43 flood years; confidence bands are wide
   (CV F1 std 0.09–0.21) and deep models must be interpreted cautiously.
3. **Reporting bias.** The negative class is "no *documented* flood";
   positives skew toward catastrophic events; trends and priorities
   inherit this bias.
4. **Provisional vulnerability weights** — reasoned, not fitted or
   externally validated; static district-level composites miss
   intra-district variation and real-time exposure.
5. **Sample infrastructure data** (`is_sample_data`) — must be replaced
   with authoritative PDMA / Health Department registries before
   operational use.
6. **ERA5 reanalysis** smooths extreme local downpours; training used
   the ERA5 archive while operations use the forecast API (distribution
   shift); the cycle reacts to the maximum 24-hour forecast precipitation,
   which can over-trigger ahead of uncertain monsoon cells.
7. **Temporal leakage risk managed but not eliminated** — history features
   use strictly earlier years, but the stratified split mixes years; a
   temporal holdout (train ≤2019, test 2020–2024) is recommended.
8. **Severity labels** are ordinal and source-dependent, not a calibrated
   scale.
9. **Operational limits:** FCM needs production credentials (degraded
   log-only mode otherwise); the scheduler is single-instance; push
   multicasts to all registered devices rather than per-district
   subscriptions; the mobile FCM token-registration API exists but native
   `firebase_messaging` wiring is a documented integration step; citizen
   reports need connectivity (no offline queue yet); map tiles need
   network.

---

## Future Work

**Modelling.** (1) Temporal-holdout validation (train ≤2019, test
2020–2024) to remove the stratified split's residual leakage risk; (2)
sub-seasonal labels to close the seasonal-vs-operational gap, or a
reframed district-season model; (3) a validated socioeconomic
vulnerability index to replace the provisional composite; (4)
threshold-sensitivity analysis with authorities to set the operating
point deliberately.

**Data.** Authoritative infrastructure registries (PDMA, Health
Department) replacing the `is_sample_data` seeds; district boundary
polygons for true choropleth rendering; station-observed weather to
complement ERA5; a living event inventory fed by the verification
workflow, so each monsoon grows the training set.

**Operations.** Production FCM credentials with per-district push
subscriptions; a distributed or leader-elected scheduler; native
`firebase_messaging` wiring in the app; offline report queuing;
Sindhi/Urdu content expansion.

**Evaluation.** Field trials with PDMA/DDMA officers, community
user-acceptance testing, and a one-to-two-district pilot over a full
monsoon season — the evaluation this phase defers. Then: extension to
additional provinces and hazard types.

---

## Conclusion

This report has documented an integrated, open-source framework that takes
flood risk prediction from dataset to deployed early warning for Sindh,
Pakistan: a reproducible district-year dataset (180 rows, 43 flood years,
2010–2024) with full provenance — per-row source citations, a published
data card, and a SHA-256 hash in the model registry; a rigorous
three-model comparison favouring a multilayer perceptron (test F1 0.875,
ROC-AUC 0.963) with honestly reported uncertainty (CV F1 0.8028 ±
0.1110); and an operational platform — a FastAPI prediction API with a
versioned registry, PostGIS GIS layers with vulnerability-weighted
decision priorities, an automated early warning cycle with cooldown and
escalation, push-notification infrastructure, and a Flutter community app
with verified citizen reporting.

The research questions are answered directly. (1) The best district-level
predictors are monsoon rainfall and its humidity interaction together
with flood history — weather-driven in the forest and network models,
history-driven in the gradient-boosted trees. (2) Classifiers distinguish
flood from non-flood district-years with ROC-AUC 0.9465–0.9630, perfect
precision and recall of 0.44–0.78 on the held-out set, with the wide
confidence bands of a 43-positive sample reported explicitly. (3)
Predicted risk is communicated through color-coded GIS layers,
per-prediction explanations, decision-support summaries with recommended
actions, trend analysis, automated advisories/emergency warnings, and a
mobile app — differentiated by role for authorities, NGOs, and the public.
(4) The most useful decision-support outputs are risk levels with
explanations and recommended actions, vulnerability-weighted priorities,
active-alert triage, resource overviews, and pre-monsoon trend analysis.

The work's significance lies less in any single metric than in the
integration: verified data with provenance, models with honest
uncertainty, predictions with explanations, alerts with audit trails, and
communities with a verified voice in the system. That integration is what
the last-mile problem demands — in direct support of Sendai Framework
Priorities 1 (understanding disaster risk) and 4 (preparedness for
effective response), and as a foundation for the author's Master's
research in Disaster Management.

---

## References

[1] National Disaster Management Authority (NDMA), Pakistan — Situation
reports and annual reviews on flood events, 2010–2024; per-row citations
in `datasets/raw/sindh_flood_events_2010_2024.csv`. [details to be
completed]

[2] Provincial Disaster Management Authority (PDMA) Sindh — Flood Impact
Report 2022, Government of Sindh. [details to be completed]

[3] UNISDR, *Sendai Framework for Disaster Risk Reduction 2015–2030*,
Geneva, Switzerland, 2015. [details to be completed]

[4] L. Alfieri et al., GloFAS — Global Flood Awareness System: global
ensemble flood forecasting (approx. 0.1° resolution, up to 30-day lead
time). [details to be completed]

[5] Flood Forecasting Division, Pakistan Meteorological Department —
Indus river system flood forecasts and flood situation reports. [details
to be completed]

[6] International Centre for Integrated Mountain Development (ICIMOD) —
Community-based flood early warning systems in the Hindu Kush Himalaya:
design and operational experience. [details to be completed]

[7] World Health Organization (WHO) — worst-affected district lists,
Pakistan monsoon floods 2022. [details to be completed]

[8] L. Breiman, "Random forests," *Machine Learning*, vol. 45, no. 1,
pp. 5–32, 2001.

[9] T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system,"
in *Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*,
2016, pp. 785–794.

[10] D. E. Rumelhart, G. E. Hinton, and R. J. Williams, "Learning
representations by back-propagating errors," *Nature*, vol. 323,
pp. 533–536, 1986.

[11] Flood susceptibility mapping literature — comparative studies using
Random Forest, XGBoost, and multilayer perceptron models across Iran,
Bangladesh, and China (reported ROC-AUC 0.85–0.97). [details to be
completed]

[12] Open-Meteo — ERA5 archive API and weather forecast API documentation.
[details to be completed]

[13] Ushahidi tradition — crowdsourced crisis mapping literature (Haiti
2010 deployments): community reporting, verification workflows, and
validity concerns. [details to be completed]

[14] OCHA / ReliefWeb / IFRC — Pakistan flood situation reports and
emergency appeals, 2010–2024. [details to be completed]

[15] Dawn (newspaper) — Pakistan flood event reporting, 2010–2024; cited
per-row in the project flood-event inventory. [details to be completed]

---

## Appendices

### Appendix A — Data card summary

*Source: `datasets/processed/DATA_CARD.md` (v1.0, built 2026-09-26) —
authoritative; this appendix summarises.*

- **File:** `datasets/processed/sindh_training_2010_2024.csv`, built by
  `backend/ml/build_dataset.py` (reproducible; re-run any time).
- **Coverage:** 12 districts (Badin, Dadu, Ghotki, Hyderabad, Jacobabad,
  Karachi, Larkana, Shikarpur, Sukkur, Thatta + Punjab border districts
  Dera Ghazi Khan and Rajanpur, flagged non-Sindh) × 15 monsoon years
  (2010–2024) → **180 district-year rows**, **43 (23.9%)** positive.
- **SHA-256:** `4b478ea58d6af1f91dd65540bc32cb3e770badc428313c779d76b2700418fb62`
  (recorded in the model registry).
- **Flood events:** 43 verified district-level records (2010–2022) from
  NDMA situation reports, PDMA Sindh Flood Impact Report 2022, WHO
  worst-affected district lists, Pakistan Met Department records, and
  Dawn/ReliefWeb/OCHA/IFRC situation reports — every row carries its own
  `source` citation and `source_url`.
- **Weather:** daily precipitation, temperature, humidity from ERA5
  reanalysis via the Open-Meteo archive API (raw JSON cached per district
  in `datasets/raw/weather/`).
- **Static attributes:** elevation, river distance, slope, population
  density from the `geographic_data` table.
- **Features:** 10 base (`rainfall_mm`, `temperature_c`, `humidity_pct`,
  `elevation_m`, `river_distance_km`, `slope_deg`, `population_density`,
  `prev_flood_events`, `last_severity`, `vulnerability_index`) + 4
  engineered at training time (`rain_intensity`, `lowland_river`,
  `exposure_index`, `flood_history_score`). Labels: `flooded` (binary),
  `severity` (0–5).
- **Vulnerability composite** (provisional — reasoned, not fitted):
  `0.5·minmax(log1p(population_density)) + 0.3·minmax(total verified
  events 2010–2024) + 0.2·minmax(1/(1+river_distance_km))`. Density spans
  160–3,650/km² (log-transformed so Karachi does not saturate it).
- **Known biases:** reporting bias (negative = "no *documented* flood");
  no pre-2010 history; static density; ERA5 smoothing; ordinal
  source-dependent severity; small sample; provisional vulnerability
  weights.
- **Reproduce:** `fetch_weather.py` → `build_dataset.py` → `sha256sum`
  against the registry hash.

### Appendix B — API endpoint list

*All paths are prefixed with `/api/v1`. Extracted from the router source
files in `backend/app/api/v1/` (prefixes from `__init__.py`). Auth: JWT
bearer unless noted.*

| Method | Path | Purpose | Access |
|---|---|---|---|
| POST | `/auth/register` | Register (roles: public / volunteer / ngo) | public |
| POST | `/auth/login` | Login → access + refresh JWT pair | public |
| POST | `/auth/refresh` | Rotate token pair | bearer |
| POST | `/auth/logout` | Stateless logout / local cleanup | bearer |
| GET | `/auth/me` | Current user profile | bearer |
| GET | `/users` | Paginated user list | authority |
| GET | `/users/{id}` | User detail | authority |
| PATCH | `/users/{id}` | Update user | authority |
| DELETE | `/users/{id}` | Delete user | authority |
| GET | `/dashboard/summary` | Dashboard summary statistics | auth |
| GET | `/dashboard/rainfall-trends` | Rainfall trend series | auth |
| GET | `/dashboard/flood-frequency` | Flood frequency aggregates | auth |
| GET | `/dashboard/risk-distribution` | Risk-level distribution | auth |
| POST | `/risk/predict?model=` | On-demand prediction (model alias; default `mlp-v1`) | auth |
| GET | `/risk/predictions` | Stored prediction history | auth |
| GET | `/risk/model-info` | Registry model metadata | auth |
| GET | `/gis/risk-layer`, `/gis/risk-layers` | Latest risk per district (GeoJSON) | auth |
| GET | `/gis/historical-floods`, `/gis/historical-layers` | Documented flood events (GeoJSON) | auth |
| GET | `/gis/vulnerability-map` | Vulnerability + risk priorities (GeoJSON) | auth |
| GET | `/gis/infrastructure` | Hospitals / rescue centres (GeoJSON; `is_sample_data` flagged) | auth |
| GET | `/gis/shelters` | Relief camps with capacity (GeoJSON) | auth |
| GET | `/gis/boundaries` | District boundary polygons (GeoJSON) | auth |
| GET | `/gis/emergency-contacts` | Rescue directory (JSON) | auth |
| GET | `/gis/districts` | District list | auth |
| GET | `/alerts` | Paginated alert list | auth |
| POST | `/alerts` | Create alert manually (201) | authority |
| PATCH | `/alerts/{id}/deactivate` | Deactivate an alert | authority |
| DELETE | `/alerts/{id}` | Delete an alert | authority |
| GET | `/decision-support/summary` | Operational view: high-risk districts, alerts, predictions, resources, hotspots | authority / ngo |
| GET | `/decision-support/trends` | Year-wise (2010–2024) and seasonal analysis | authority / ngo |
| GET | `/decision-support/resources` | Resource allocations | authority / ngo |
| POST | `/decision-support/resources` | Record a resource allocation | authority |
| GET | `/reports/risk-report` | Generated risk report | auth |
| GET | `/reports/historical-events` | Historical event listing | auth |
| GET | `/mobile/my-risk` | Latest assessment by district or lat/lon | bearer |
| GET | `/mobile/alerts` | Active warnings (app inbox) | bearer |
| GET | `/mobile/shelters/nearby` | Nearest shelters by geodesic distance | bearer |
| GET | `/mobile/emergency-contacts` | Rescue directory (+ district filter) | bearer |
| POST | `/mobile/report-event` | Submit citizen report → `pending` | volunteer / public / ngo (authority → 403) |
| POST | `/mobile/report-event/{report_id}/image` | Attach photo evidence (≤ 5 MB) | reporter or authority |
| GET | `/mobile/reports/mine` | User's own reports | bearer |
| POST | `/mobile/device-token` | Register FCM device token | bearer |
| DELETE | `/mobile/device-token` | Unregister FCM device token | bearer |
| POST | `/admin/import/{dataset}` | Validated CSV/GeoJSON bulk import (dry-run supported) | authority |
| GET | `/admin/import/templates/{dataset}` | Import file templates | authority |
| GET | `/admin/reports` | Citizen-report triage queue | authority |
| PATCH | `/admin/reports/{report_id}/verify` | Verify / reject / resolve a report | authority |

### Appendix C — Model registry extract

*Source: `ml-models/registry.json` — eight entries (five servable
models, three aliases), all trained 2026-09-26 (UTC).*

**`rule-based-v1`** — type `rule-based`, version `v1.0.0-rule-based`.
Deterministic weighted risk scoring over nine normalised features with
fixed weights. Transparent baseline, always available; default for the
automated early warning cycle. No learned metrics.

**`rf-v1`** — type `sklearn`, version `rf-v1`. Legacy Random Forest (300
trees) on live database records: 52 documented flood events + 36
synthetic non-flood observations (88 rows; 70 train / 18 test). Trained
2026-09-26T07:23:43Z. Metrics: accuracy/precision/recall/F1/ROC-AUC 1.0,
CV F1 0.9749 ± 0.0308, confusion matrix `[[7, 0], [0, 11]]` — flagged in
the registry as optimistic (synthetic negative class). Backward
compatibility only.

**`randomforest-v1`** — type `sklearn`. Random Forest (300 trees,
`class_weight=balanced`) on the 180-row research dataset (144/36). Trained
2026-09-26T07:47:41Z; dataset SHA-256 `4b478ea5…0418fb62`. Metrics:
accuracy 0.8611, precision 1.0, recall 0.4444, F1 0.6154, ROC-AUC 0.9547,
CV F1 0.6147 ± 0.2073, confusion matrix `[[27, 0], [5, 4]]`; built-in
importance. Caveat: "Negative class = no documented flood (reporting
bias); metrics are honest but the sample is modest."

**`xgboost-v1`** — type `sklearn`. XGBoost (300 rounds, max_depth 6,
lr 0.05) on the same 180 rows. Trained 2026-09-26T07:47:42Z; same dataset
SHA-256. Metrics: accuracy 0.9167, precision 1.0, recall 0.6667, F1
0.8000, ROC-AUC 0.9465, CV F1 0.6974 ± 0.0935, confusion matrix
`[[27, 0], [3, 6]]`; built-in importance. Same honest-sample caveat.

**`mlp-v1`** — type `sklearn`. Multilayer perceptron (64–32 hidden units,
max_iter 800) on the same 180 rows; permutation importance (10 repeats)
on the held-out test set. Trained 2026-09-26T07:47:47Z; same dataset
SHA-256. Metrics: accuracy 0.9444, precision 1.0, recall 0.7778, F1
0.8750, ROC-AUC 0.9630, CV F1 0.8028 ± 0.1110, confusion matrix
`[[27, 0], [2, 7]]`. Best test F1 and ROC-AUC of the three. Same
honest-sample caveat.

**Aliases** — `randomforest` → `randomforest-v1`, `xgboost` →
`xgboost-v1`, `mlp` → `mlp-v1` (each records `alias_of`; artefacts under
`ml-models/models/<name>-v1/`: `model.joblib`, `feature_names.json`,
`preprocessing.json`, `metrics.json`, `feature_importance.json`,
`confusion_matrix.png`).

### Appendix D — Glossary

- **Alert engine** — converts per-district predictions into alert decisions (none / advisory / emergency) with cooldown and escalation.
- **APScheduler** — in-process scheduler running the warning cycle every `EW_CYCLE_MINUTES` (default 30); single-instance by design.
- **Citizen report** — geolocated, categorised flood observation with optional photo; enters as `pending`, requires authority verification.
- **Cooldown** — 6-hour default window suppressing repeat same-level alerts per district.
- **Data card** — published dataset documentation (`datasets/processed/DATA_CARD.md`).
- **DDMA** — District Disaster Management Authority.
- **Decision support summary** — the single operational API view (`/decision-support/summary`): high-risk districts, explanations, actions, alerts, predictions, resources, hotspots.
- **District-year** — analytical grain: one row per district per monsoon year (180 rows = 12 districts x 15 years).
- **Early warning cycle** — forecast ingestion → prediction → alert decision → FCM push + app inboxes.
- **Escalation** — MEDIUM → HIGH always issues immediately, deactivating the superseded advisory.
- **FCM** — Firebase Cloud Messaging; degraded log-only mode without service-account credentials.
- **Feature contribution** — descriptive (non-causal) per-prediction score for which features pushed a prediction away from the average input.
- **GeoJSON** — the JSON geographic format of all map layers.
- **GloFAS** — Global Flood Awareness System (~0.1-degree resolution ensemble flood forecasts).
- **JWT / RBAC** — token authentication with role-based access control (authority, NGO, public, volunteer).
- **Last-mile problem** — the gap between forecasts and local, actionable decisions and community action.
- **Model registry** — versioned file registry (`ml-models/registry.json`) recording each model's configuration, metrics, dataset hash, and artefacts.
- **Monsoon year** — the June-September temporal unit; weather features are seasonal aggregates.
- **NDMA / PDMA** — National / Provincial Disaster Management Authority (Pakistan).
- **Permutation importance** — drop in a scoring metric when a feature's values are shuffled (used for the MLP: 10 repeats, F1 scoring).
- **PostGIS** — spatial extension to PostgreSQL; all spatial columns use `Geometry(POINT, 4326)` by convention.
- **Reporting bias** — under-documentation of minor/remote floods; the negative class is "no *documented* flood".
- **Risk level** — HIGH (p >= 0.66), MEDIUM (0.33-0.66), LOW (p < 0.33).
- **Rule-based engine** — the deterministic weighted-scoring baseline (`rule-based-v1`); default for the automated cycle.
- **Sendai Framework** — UN disaster risk reduction framework 2015-2030; this project addresses Priorities 1 and 4.
- **Severity (1-5)** — ordinal documented-event label from narrative reports; not calibrated.
- **SRID 4326** — WGS 84 coordinate reference system for all spatial data.
- **Stratified split** — 80/20 train/test preserving the 23.9% positive share (`random_state=42`).
- **Vulnerability index** — provisional 0-1 composite: log density (0.5), total verified events (0.3), Indus proximity (0.2); reasoned, not validated.
- **Vulnerability priority** — decision class from risk + vulnerability: CRITICAL / HIGH / MEDIUM / LOW.
