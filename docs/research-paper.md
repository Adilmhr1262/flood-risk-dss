# A Machine Learning-Based Flood Risk Prediction and GIS Decision Support Framework for Disaster Risk Reduction: A Case Study of Sindh, Pakistan

**Research paper draft — Flood Risk Prediction and Early Warning Decision Support System (Phase 7)**
**Study area:** Sindh Province, Pakistan · **Study period:** 2010–2024 · **Draft date:** 2026-09-26

> **Terminology note.** This project never brands its predictive capability with
> artificial-intelligence terminology. All predictive components are described as *machine learning-based* or
> *data-driven*, consistent with the project's standing terminology rule.

---

## Abstract

Floods are the most frequent and destructive natural hazard in Pakistan. The
2010 super floods and the 2022 monsoon floods each displaced millions of people,
and the province of Sindh has repeatedly borne the heaviest losses. Disaster
management authorities in the Indus basin still rely heavily on rainfall
thresholds and qualitative assessments when deciding where to pre-position
relief, issue advisories, and plan evacuations. This paper presents a complete,
open-source decision support framework that combines machine learning-based
flood risk prediction, geographic information system (GIS) visualization, an
automated early warning cycle, and community reporting into a single
operational platform, evaluated on a purpose-built dataset for 12 districts of
Sindh and the adjacent Punjab border districts (2010–2024).

We construct a district-year dataset of 180 rows (43 labelled flood years) from
43 verified flood events with per-row source citations, ERA5 reanalysis weather
aggregates via the Open-Meteo archive API, static geographic attributes, and a
documented composite vulnerability index. Three classifiers are compared on a
stratified 80/20 held-out test set with 5-fold cross-validation: Random Forest
(F1 0.615, ROC-AUC 0.955), XGBoost (F1 0.800, ROC-AUC 0.947), and a multilayer
perceptron (F1 0.875, ROC-AUC 0.963). All models achieve perfect precision but
imperfect recall — a conservative early-warning behaviour in which a flag is
trustworthy but its absence is not a guarantee of safety. The best model is
deployed behind a FastAPI prediction service with a versioned model registry,
PostgreSQL/PostGIS spatial layers, a Leaflet dashboard with decision-support
summaries and trend analysis, a Flutter community mobile application, and an
automated early warning loop (forecast ingestion → prediction → alert decision
with cooldown and escalation → push notification). Limitations — reporting
bias, a small positive sample, provisional vulnerability weights, sample
infrastructure data, and the seasonal-vs-event-scale modelling gap — are
documented explicitly. The framework demonstrates how machine learning,
GIS, and community participation can be integrated to support the
understanding of disaster risk and preparedness for effective response called
for by the Sendai Framework for Disaster Risk Reduction 2015–2030.

**Keywords:** flood risk prediction; machine learning; GIS; early warning
systems; disaster risk reduction; Sindh; Pakistan; Sendai Framework.

---

## 1. Introduction

### 1.1 Background

Pakistan is among the countries most exposed to flood hazard. The 2010
floods affected over 20 million people across the Indus basin; the 2022
monsoon floods killed more than 1,700 people, displaced 8 million, and caused
estimated damages above USD 30 billion, with Sindh and Balochistan the
worst-affected provinces. In Sindh, the districts along the Indus — Dadu,
Larkana, Shikarpur, Jacobabad, Sukkur, Badin, Thatta, and others — flood
repeatedly, yet district-level risk assessment remains largely
qualitative, fragmented across agencies, and difficult for communities to
access.

### 1.2 The early warning gap

Pakistan's flood forecasting infrastructure (notably the Flood Forecasting
Division and the provincial PDMAs) provides valuable river-flow and rainfall
forecasts, but translating forecasts into *district-level, actionable risk
information* — which districts to warn, where to pre-position relief, which
shelters to open — remains a manual, expertise-driven process. Global systems
such as GloFAS (Global Flood Awareness System) operate at coarse
resolutions unsuited to district operational decisions. Meanwhile,
machine-learning research on flood susceptibility mapping has grown rapidly
but rarely progresses beyond offline susceptibility maps to integrated,
operational decision support.

### 1.3 Contribution

This work closes that gap with an end-to-end, open-source framework:

1. A **research dataset** for Sindh (2010–2024) with full provenance (data
   card, per-row citations, dataset SHA-256 in a model registry).
2. A **comparative modelling study** (Random Forest, XGBoost, MLP) with
   honest reporting of uncertainty.
3. An **operational platform**: prediction API, GIS decision support,
   automated early warning cycle, push notifications, and a community
   mobile app with verified citizen reporting.

The remainder of this paper reviews the relevant literature (Section 2),
describes the dataset (Section 3) and methodology (Section 4), details the
system architecture (Section 5) and model development (Section 6), presents
results (Section 7), discusses their meaning for disaster management
(Section 8), describes the early warning and GIS workflows (Sections 9–10),
and concludes with limitations and future work (Sections 11–12).

---

## 2. Literature Review

### 2.1 Flood disaster management in Pakistan

Pakistan's disaster management architecture is anchored by the National
Disaster Management Authority (NDMA), with Provincial Disaster Management
Authorities (PDMAs) — including PDMA Sindh — responsible for provincial
preparedness and response, and District Disaster Management Authorities
(DDMAs) at the district level. The National Flood Protection Plan and the
post-2010 and post-2022 policy reviews repeatedly identify the same
weaknesses: late or spatially coarse warnings, weak district-level
capacity, and poor integration of community observations into official
situational awareness (NDMA situation reports; PDMA Sindh Flood Impact
Report 2022). The 2022 floods demonstrated that even when national
forecasts existed, district authorities lacked localized, decision-ready
risk information — precisely the gap this framework addresses.

### 2.2 The Sendai Framework and early warning

The Sendai Framework for Disaster Risk Reduction 2015–2030 sets four
priorities for action: (1) understanding disaster risk; (2) strengthening
disaster risk governance; (3) investing in disaster risk reduction for
resilience; and (4) enhancing disaster preparedness for effective response
and "Build Back Better". Its Global Target (g) calls for substantially
increasing the availability of and access to multi-hazard early warning
systems. This work contributes directly to Priorities 1 and 4: a
quantitative, explainable model of district flood risk (understanding
risk) embedded in an automated warning and response-support loop
(preparedness).

### 2.3 Existing flood early warning systems

Globally, GloFAS provides ensemble flood forecasts up to 30 days ahead but
at ~0.1° resolution with limited skill for flash and urban flooding in
South Asia. Regionally, the Flood Forecasting Division of the Pakistan
Meteorological Department issues river-flow forecasts for the Indus system,
and community-based systems (e.g. ICIMOD's community-based flood early
warning in the Hindu Kush Himalaya) show the value of local observation
networks. A persistent pattern across the literature is the "last mile"
problem: forecasts exist, but the translation into local decisions and
community action is weak. Integrating official forecasts with community
reporting and decision support — as done here — is the recommended remedy.

### 2.4 Machine learning for flood prediction

Machine learning is now standard in flood susceptibility mapping. Random
Forest and XGBoost dominate the literature for their robustness on
tabular environmental data (e.g. studies across Iran, Bangladesh, and China
report ROC-AUC values of 0.85–0.97 for flood susceptibility), while MLPs
and other neural models perform competitively where rainfall time series
are informative. Recurring methodological concerns in this literature —
which this study takes seriously — are small positive samples, reporting
bias in flood inventories, spatial and temporal leakage in validation
splits, and the gap between offline susceptibility maps and operational
use. Our contribution is distinguished by (i) a fully documented,
reproducible dataset with per-event citations, (ii) explicit treatment of
these validity threats, and (iii) deployment of the models inside an
operational early warning and decision support platform rather than a
static map.

### 2.5 GIS in disaster management

GIS is the operational backbone of modern disaster management: hazard
mapping, exposure and vulnerability analysis, resource and shelter
management, and evacuation planning all depend on spatial integration of
heterogeneous data. PostGIS-backed web GIS with Leaflet-class clients is a
mature, low-cost stack widely used by humanitarian agencies. Our GIS module
follows this pattern while adding decision-oriented views — risk-weighted
vulnerability priorities, resource allocation tracking, and trend analysis —
designed around the questions a DDMA officer asks before the monsoon.

---

## 3. Dataset Description

The training dataset (`datasets/processed/sindh_training_2010_2024.csv`) was
built specifically for this study by `backend/ml/build_dataset.py` and is
fully documented in `datasets/processed/DATA_CARD.md`.

### 3.1 Study area and period

TABLE II — Dataset summary (full data card: `datasets/processed/DATA_CARD.md`).

Twelve districts — Badin, Dadu, Ghotki, Hyderabad, Jacobabad, Karachi,
Larkana, Shikarpur, Sukkur, Thatta (Sindh), plus Dera Ghazi Khan and
Rajanpur (Punjab districts on the Sindh border, included because Indus
riverine flooding crosses the provincial boundary) — over the 15 monsoon
years 2010–2024.

### 3.2 Analytical grain: district-year

Floods in Sindh are monsoon-season phenomena, so the honest analytical unit
is the monsoon year: one row per district per year, yielding **180 rows**,
of which **43 (23.9%)** are positive (at least one verified flood event
that year). The alternative — one row per district-event window — would
require exact event-day weather for every historical flood (unavailable for
most rows) and would leave no honest negative class.

### 3.3 Sources

| Data | Source |
|---|---|
| 43 verified district-level flood events (2010–2022) | NDMA situation reports, PDMA Sindh Flood Impact Report 2022, WHO worst-affected district lists, Pakistan Met Department records, Dawn/ReliefWeb/OCHA/IFRC situation reports — each row carries its own `source` citation and `source_url` |
| Daily weather, 2010-01-01–2024-12-31 (precipitation, temperature, humidity) | ERA5 reanalysis via the Open-Meteo archive API; raw JSON cached per district |
| Elevation, river distance, slope, population density | Project `geographic_data` table (static snapshot) |

### 3.4 Features

Ten base features: monsoon-season (Jun–Sep) precipitation sum
(`rainfall_mm`), monsoon mean temperature (`temperature_c`), monsoon mean
relative humidity (`humidity_pct`), mean elevation (`elevation_m`),
distance to the Indus (`river_distance_km`), mean slope (`slope_deg`),
population density (`population_density`), count of verified floods in
strictly earlier years (`prev_flood_events`), maximum severity in strictly
earlier years (`last_severity`, 0–5), and a composite vulnerability index.

The **vulnerability index** is a documented provisional composite:

```
vulnerability_index = 0.5 · minmax(log1p(population_density))
                    + 0.3 · minmax(total verified events 2010–2024)
                    + 0.2 · minmax(1 / (1 + river_distance_km))
```

The weights are a reasoned prior (exposure dominant), not fitted or
externally validated — a limitation stated explicitly.

Four engineered features are added at training time: `rain_intensity`
(rainfall × humidity), `lowland_river` (elevation × river proximity),
`exposure_index` (log-density × flood history), and `flood_history_score`.
Labels: `flooded` (1 if ≥1 verified event in the district-year) and
`severity` (maximum verified severity, 0 if none).

### 3.5 Reproducibility

The dataset is rebuildable with two commands and its SHA-256
(`4b478ea5…0418fb62`) is recorded in the model registry, so every trained
model is traceable to the exact bytes it learned from.

**Figure 2** (see figures/data-workflow.png) summarises the pipeline.

---

## 4. Methodology

### 4.1 Feature engineering

Features were designed from disaster-management domain knowledge:
monsoon-season aggregates (the physical driver), static exposure
attributes (elevation, river proximity, slope, population density), and
historical susceptibility (`prev_flood_events`, `last_severity`,
`flood_history_score`). Interaction terms (`rain_intensity`,
`lowland_river`, `exposure_index`) capture compounding effects — intense
rain on low-lying floodplain near the river, and people exposed where
floods have struck before.

### 4.2 Preprocessing

Median imputation for missing numerics, IQR-based outlier capping on
rainfall and elevation, and standardisation — all parameters fitted on
training data only and persisted per model to prevent leakage at serving
time.

### 4.3 Experimental design

- **Split:** stratified 80/20 train/test (144/36 rows), `random_state=42`.
- **Validation:** 5-fold stratified cross-validation on the training set,
  scoring F1 (the positive class is the minority, 23.9%).
- **Models:** Random Forest (300 trees, `class_weight=balanced`),
  XGBoost (300 rounds, max_depth 6, lr 0.05, subsample/colsample 0.9),
  MLP (hidden layers (64, 32), max_iter 800).
- **Metrics:** accuracy, precision, recall, F1, ROC-AUC on the held-out
  test set; CV F1 mean ± std for uncertainty.
- **Interpretability:** built-in importances (RF, XGBoost); permutation
  importance for the MLP (10 repeats, F1 scoring). The API returns
  per-prediction feature contributions for every request.

### 4.4 Class imbalance

With 43 positives in 180 rows, the minority class was handled via
`class_weight=balanced` (RF), XGBoost's natural handling of imbalance, and
F1-based model selection rather than accuracy. The resulting models are
conservative (perfect precision, imperfect recall) — see Section 7.

---

## 5. System Architecture

The research artefact is a three-tier operational platform
(**Figure 1**, figures/system-architecture.png):

- **Data layer:** PostgreSQL 16 + PostGIS 3.4. Tables cover district
  geography, flood events, weather observations, predictions, alerts,
  shelters, infrastructure, vulnerability indicators, resource allocations,
  device tokens, and citizen reports. All spatial columns use
  `Geometry(POINT, 4326)` by project convention.
- **Application layer:** FastAPI with JWT authentication and role-based
  access control (roles: **authority**, **ngo**, **public**,
  **volunteer**). Services: prediction (versioned model registry),
  GIS (GeoJSON layers), alert engine, notifications (FCM), early-warning
  scheduler (APScheduler), and citizen-report verification.
- **Client layer:** a Leaflet web dashboard (risk map, decision support,
  Authority Alert Center), a Flutter community mobile app (risk
  assessment, alerts, shelter finder, offline safety guide, reporting),
  and automated push notifications.

Every prediction is persisted with its model version, probability,
contributing factors, and recommendations, making the system's outputs
auditable — a requirement for any tool that informs public-safety
decisions.

---

## 6. Model Development

The three candidate models were trained with `backend/ml/train_phase3.py`
under the registry names `randomforest-v1`, `xgboost-v1`, and `mlp-v1`
(plus a legacy `rf-v1` and a deterministic `rule-based-v1` fallback kept
for backward compatibility and operational transparency). Hyperparameters
were chosen as strong, literature-consistent defaults rather than via
extensive tuning — deliberate, given the small sample: aggressive tuning
on 144 training rows risks overfitting to the validation folds. The
registry records each model's configuration, feature list, preprocessing
parameters, metrics, confusion matrix, and the dataset SHA-256.

---

## 7. Results

### 7.1 Model comparison (held-out test set, n = 36)

TABLE I — Model performance on the held-out test set (n = 36) with 5-fold
cross-validation F1 on the training set.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | CV F1 (mean ± std) |
|---|---|---|---|---|---|---|
| randomforest-v1 | 0.8611 | 1.0000 | 0.4444 | 0.6154 | 0.9547 | 0.6147 ± 0.2073 |
| xgboost-v1 | 0.9167 | 1.0000 | 0.6667 | 0.8000 | 0.9465 | 0.6974 ± 0.0935 |
| **mlp-v1** | **0.9444** | 1.0000 | **0.7778** | **0.8750** | **0.9630** | **0.8028 ± 0.1110** |

Confusion matrices (rows actual, columns predicted `[no-flood, flood]`):
RF `[[27, 0], [5, 4]]`; XGBoost `[[27, 0], [3, 6]]`; MLP
`[[27, 0], [2, 7]]`. **Figure 3** (figures/model-comparison.png)
visualises the comparison.

### 7.2 Feature importance

- **Random Forest** (built-in): `rainfall_mm` 0.20, `rain_intensity` 0.17,
  `temperature_c` 0.14, `exposure_index` 0.09 — weather-driven.
- **XGBoost** (built-in): `flood_history_score` 0.20, `prev_flood_events`
  0.13, `rainfall_mm` 0.11, `population_density` 0.08 — history-driven:
  past floods are the strongest predictor of future floods, consistent
  with disaster-management experience in the Indus basin.
- **MLP** (permutation): `rainfall_mm` 0.27, `rain_intensity` 0.17,
  `temperature_c` 0.13, `vulnerability_index` 0.09 — rainfall-dominated,
  with the vulnerability composite contributing measurably.

The disagreement between model families is itself informative: tree
ensembles split on history while the network leans on rainfall. An
operational system should not rely on a single model family.

---

## 8. Discussion

**Why the MLP won on recall.** The MLP's smooth decision surface appears
better suited to the continuous rainfall–humidity interactions that
separate flood from non-flood monsoon years, whereas the tree ensembles'
axis-aligned splits, combined with the conservative 0.5 threshold, miss
more marginal flood years. All three models rank well (ROC-AUC > 0.94),
showing the signal is present; the threshold is what is conservative.

**Conservative early warning.** Perfect precision with imperfect recall
means the system as configured is a trustworthy flagger: when it flags a
district-year, the flag is reliable, but absence of a flag is not absence
of risk. For disaster management this is the safer failure mode for
automated advisories — false alarms erode public trust — but it mandates
human review of borderline monsoon outlooks and must be communicated
honestly to authorities.

**Uncertainty is reported, not hidden.** CV F1 standard deviations
(0.09–0.21) reflect the small sample; fold composition changes results
materially. We report this prominently because a Master's-level
contribution must not overstate what 43 positive samples can support.

**Deployment implication.** The API serves all three models plus the
transparent rule-based engine; the automated cycle defaults to the
rule-based engine for determinism, with `mlp-v1` available for
analyst-driven assessment. Per-prediction feature contributions give
authorities an auditable reason for every output.

---

## 9. Early Warning Workflow

The automated loop (**Figure 5**, figures/early-warning-workflow.png):

```
Open-Meteo forecast → weather_observations → scheduled cycle (30 min)
→ prediction engine → alert engine → alerts table → FCM push + inboxes
```

**Alert decision table:** LOW → no alert; MEDIUM → advisory notification
(`watch`); HIGH → emergency warning (`emergency`). A 6-hour cooldown
suppresses repeat alerts at the same level; escalation (MEDIUM → HIGH)
always fires immediately and deactivates the superseded advisory. Every
automated alert stores model version, probability, and triggering factors
for audit. Push notifications use Firebase Cloud Messaging with a graceful
degraded (log-only) mode when no service-account credentials are
configured — documented as a production deployment step.

A parallel **community feedback loop** lets citizens and volunteers submit
geolocated, categorised reports (flood water, road blockage, rescue
request, medical emergency) with photo evidence; authorities triage them
through a verification workflow (pending → verified/rejected → resolved)
in the Alert Center. This addresses the "last mile" problem identified in
Section 2.3: official forecasts fused with ground observations.

---

## 10. GIS Methodology

Spatial layers are stored in PostGIS (SRID 4326) and served as GeoJSON
(**Figure 4**, figures/gis-framework.png):

- **Risk layer** — latest prediction per district, coloured by
  probability thresholds (HIGH ≥ 0.66, MEDIUM 0.33–0.66, LOW < 0.33).
- **Historical floods** — documented events with 1–5 severity.
- **Vulnerability map** — the Phase 3 composite index combined with
  current risk into decision priorities (CRITICAL/HIGH/MEDIUM/LOW).
- **Infrastructure** — hospitals, rescue centres, emergency facilities
  (seed rows explicitly flagged `is_sample_data`, pending authoritative
  PDMA/Health Department registries).
- **Shelters and emergency contacts**, plus district boundaries when the
  polygon dataset is imported.

`/decision-support/summary` packages high-risk districts with explanations
and recommended actions, active alerts, predictions with model versions,
resource overviews, and vulnerability hotspots into a single operational
view; `/decision-support/trends` provides year-wise (2010–2024) and
seasonal (Jul–Sep concentration) analysis for pre-monsoon planning. Map
and dashboard share the same priority logic so they can never disagree.

---

## 11. Limitations

1. **Seasonal vs. event scale.** The models are district-year (seasonal)
   classifiers, but the prediction API accepts event-scale inputs. This
   mismatch is documented: event-scale outputs are indicative, not a
   validated sub-seasonal claim. Reframing around district-season inputs
   or collecting sub-seasonal labels is priority future work.
2. **Small positive sample.** 43 flood years; confidence bands are wide
   and deep models must be interpreted cautiously.
3. **Reporting bias.** The negative class is "no *documented* flood";
   positives skew toward catastrophic events; trends inherit this bias.
4. **Provisional vulnerability weights** — reasoned, not fitted or
   externally validated; static district-level composites miss
   intra-district variation.
5. **Sample infrastructure data** (`is_sample_data`) — must be replaced
   with authoritative registries before operational use.
6. **ERA5 reanalysis** smooths extreme local downpours; training used
   ERA5 archive while operations use the forecast API (distribution shift).
7. **Temporal leakage risk managed but not eliminated** — the stratified
   split mixes years; a temporal holdout (train ≤2019, test 2020–2024) is
   recommended.
8. **Operational limits:** FCM needs production credentials; the
   scheduler is single-instance; push currently multicasts to all devices
   rather than per-district subscriptions; the mobile FCM token
   registration API exists but the native `firebase_messaging` wiring is a
   documented integration step.

---

## 12. Conclusion and Future Work

This paper presented an integrated, open-source framework that takes flood
risk prediction from dataset to deployed early warning: a reproducible
Sindh 2010–2024 dataset, a rigorous three-model comparison favouring an
MLP (F1 0.875, ROC-AUC 0.963) with honestly reported uncertainty, and an
operational platform — prediction API, GIS decision support, automated
alerting, and community reporting — built to Master's research standards.

**Future work:** (1) temporal-holdout validation and sub-seasonal
(event-scale) labels; (2) authoritative infrastructure and boundary
datasets; (3) a validated socioeconomic vulnerability index;
(4) per-district push subscriptions and production FCM credentials;
(5) field evaluation with PDMA/DDMA officers and community user-acceptance
testing; (6) extension to additional provinces and hazard types.

---

## References

[1] National Disaster Management Authority (NDMA), Pakistan — situation
reports and annual reviews, flood events 2010–2024. Per-row citations in
`datasets/raw/sindh_flood_events_2010_2024.csv`. [details to be completed]

[2] Provincial Disaster Management Authority (PDMA) Sindh — Flood Impact
Report 2022. [details to be completed]

[3] UNISDR, *Sendai Framework for Disaster Risk Reduction 2015–2030*,
United Nations, Geneva, 2015.

[4] L. Alfieri *et al.*, "GloFAS — Global Flood Awareness System," Joint
Research Centre, European Commission. [details to be completed]

[5] Flood Forecasting Division, Pakistan Meteorological Department — Indus
river flood forecasts. [details to be completed]

[6] International Centre for Integrated Mountain Development (ICIMOD) —
community-based flood early warning systems, Hindu Kush Himalaya.
[details to be completed]

[7] Flood susceptibility mapping literature: comparative Random Forest /
XGBoost / MLP studies (Iran, Bangladesh, China; reported ROC-AUC
0.85–0.97). [details to be completed]

[8] Open-Meteo — ERA5 archive API and forecast API documentation,
https://open-meteo.com/. [details to be completed]

## Data Availability

The training dataset (`datasets/processed/sindh_training_2010_2024.csv`,
180 district-year rows) is rebuildable from the documented sources with
`backend/ml/fetch_weather.py` and `backend/ml/build_dataset.py`; its
SHA-256 (`4b478ea58d6af1f91dd65540bc32cb3e770badc428313c779d76b2700418fb62`)
is recorded in `ml-models/registry.json`. Raw per-event citations are in
`datasets/raw/sindh_flood_events_2010_2024.csv`; the full data card is
`datasets/processed/DATA_CARD.md`.

## DOI

A DOI will be minted for this paper and the accompanying dataset on
submission to a repository (e.g. Zenodo); no DOI has been assigned yet.

---

## Figure captions

| Figure | File | Caption |
|---|---|---|
| 1 | figures/system-architecture.png | Three-tier system architecture |
| 2 | figures/data-workflow.png | Data pipeline: sources → dataset → models → registry |
| 3 | figures/model-comparison.png | Test metrics + CV F1 for the three models |
| 4 | figures/gis-framework.png | GIS layers → decision support → clients |
| 5 | figures/early-warning-workflow.png | Automated warning cycle + citizen feedback loop |
