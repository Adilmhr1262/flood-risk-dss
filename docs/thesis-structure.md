# Thesis Structure — Flood Risk Prediction and Early Warning Decision Support System

**Programme:** Master's in Disaster Management
**Thesis type:** Quantitative computational research with a design-science orientation
(the artefact — the decision support system — is both the research instrument
and a primary research output.)

> **Terminology rule.** Never brand the system's predictive capability with artificial-intelligence terminology.
> Use *machine learning-based prediction*, *data-driven prediction*, *risk
> assessment*, or *decision support* throughout the thesis.

---

## Chapter 1 — Introduction

*Purpose: establish the disaster-management problem, the research gap, and what
the thesis will deliver.*

### 1.1 Background
Describe flood hazard in Pakistan and Sindh: the 2010 super floods, the 2022
monsoon floods (deaths, displacement, damages), and the repeated exposure of
Indus-basin districts. Ground every claim in the NDMA/PDMA/ReliefWeb sources
already cited per-row in `datasets/raw/sindh_flood_events_2010_2024.csv`.
**Include:** a map of the 12 study districts and a timeline figure of major
flood years 2010–2024.

### 1.2 Problem statement
District authorities lack timely, location-specific, decision-ready flood risk
information. National forecasts exist but the "last mile" — district-level
warnings, relief pre-positioning, shelter planning — remains manual and
expertise-driven.

### 1.3 Research objectives
1. Build a reproducible, fully documented district-level flood dataset for
   Sindh (2010–2024).
2. Compare machine learning classifiers for district-year flood prediction
   with honest uncertainty reporting.
3. Integrate the best model into an operational GIS-based decision support
   and automated early warning platform.
4. Evaluate the system against disaster-management needs (authorities, NGOs,
   communities).

### 1.4 Research questions
1. Which combination of environmental, geographic, and historical indicators
   best predicts flood occurrence at district level?
2. How accurately can machine learning-based classifiers distinguish flood
   from non-flood district-years?
3. How can predicted risk be communicated through GIS and early warning
   interfaces for authorities, NGOs, and the public?
4. What decision-support outputs are most useful to practitioners?

### 1.5 Scope and delimitations
12 districts, 2010–2024, district-year grain; monsoon-season phenomenon;
mobile app targets community users; operational deployment and field trials
are out of scope (listed as future work).

### 1.6 Significance of the study
Contribution to Sendai Framework Priorities 1 (understanding risk) and 4
(preparedness); practical value for PDMA/DDMA workflows.

### 1.7 Thesis outline
One paragraph per chapter summarising what follows.

---

## Chapter 2 — Literature Review

*Purpose: demonstrate mastery of the field and position the work.*

### 2.1 Disaster risk management frameworks
Sendai Framework 2015–2030 (four priorities, Target (g) on early warning);
Pakistan's NDMA/PDMA/DDMA architecture; National Flood Protection Plan.

### 2.2 Flood hazard in the Indus basin
Climatology of the South Asian monsoon; Indus riverine vs. urban flash
flooding (Karachi 2020 as a contrasting case); the 2010 and 2022 events in
detail.

### 2.3 Flood early warning systems
GloFAS and global systems; Pakistan's Flood Forecasting Division; community-
based early warning (ICIMOD/HKH experience); the "last mile" problem —
forecasts that never become local decisions.

### 2.4 Machine learning for flood prediction
Flood susceptibility mapping literature: Random Forest, XGBoost, and MLP
studies (reported ROC-AUC 0.85–0.97); recurring methodological concerns —
small samples, inventory bias, spatial/temporal leakage, and the gap
between offline maps and operational systems. Position this thesis as
addressing the last three explicitly.

### 2.5 GIS and decision support in disaster management
PostGIS/Leaflet-class web GIS in humanitarian practice; vulnerability
mapping; resource and shelter management; decision-support views for
practitioners.

### 2.6 Community participation and citizen reporting
Crowdsourced crisis mapping (Ushahidi tradition); verification workflows;
reporting bias and the digital divide as validity concerns.

### 2.7 Research gap and conceptual framework
Synthesis: no integrated, open-source, district-scale ML + GIS + automated
warning + community-reporting stack exists for Sindh. Present the thesis
conceptual framework (hazard → exposure → vulnerability → risk → decision
→ action → feedback).

---

## Chapter 3 — Research Methodology

*Purpose: a fully reproducible account of how the research was done.*

### 3.1 Research design
Quantitative computational research; design-science orientation; six software
phases mapped to research stages. **Include:** research design diagram.

### 3.2 Study area and period
The 12 districts (10 Sindh + 2 Punjab border districts — justify the
inclusion: Indus riverine flooding crosses the provincial boundary);
2010–2024. **Include:** study-area map (**Figure: districts**).

### 3.3 Data collection
Event inventory (43 verified events; source hierarchy NDMA > PDMA > WHO >
Met Department > media/ReliefWeb; per-row citations); ERA5 via Open-Meteo
archive API; static geographic attributes. **Include:** Table 3.1 (sources),
reproduction commands, dataset SHA-256.

### 3.4 Analytical grain and labelling
Justify the district-year design (monsoon-year as the honest unit; negative
class = no *documented* flood). Define `flooded` and `severity` labels.

### 3.5 Feature engineering
10 base features + 4 engineered (`rain_intensity`, `lowland_river`,
`exposure_index`, `flood_history_score`); the provisional vulnerability
composite with its formula and the explicit caveat that weights are reasoned,
not validated. **Include:** Table 3.2 (feature definitions).

### 3.6 Modelling and evaluation
Preprocessing (median imputation, IQR capping, standardisation — fitted on
train only); stratified 80/20 split; 5-fold CV scoring F1; model
configurations; metrics; interpretability methods (built-in vs. permutation
importance). **Include:** data workflow diagram (**Figure 2**,
figures/data-workflow.png`).

### 3.7 GIS methods
PostGIS SRID 4326; GeoJSON service layer; risk classification thresholds;
vulnerability-priority logic; trend/seasonality computation.

### 3.8 System evaluation approach
119 backend tests; live smoke tests of the warning cycle; prototype usability
notes. Be explicit that field evaluation with practitioners is future work.

### 3.9 Research ethics
Citizen reporting: voluntary, geolocated reports; verification workflow
prevents unverified claims from triggering warnings; no automated alert is
ever issued from a citizen report alone; data minimisation for reporter
identities.

### 3.10 Threats to validity
Reporting bias; small sample; ERA5 smoothing; static density; provisional
vulnerability weights; seasonal-vs-event-scale gap; temporal leakage risk in
the stratified split. Each threat gets: what it is, how it was mitigated,
what remains.

---

## Chapter 4 — System Development

*Purpose: document the artefact so completely that it could be rebuilt.*

### 4.1 System architecture
Three tiers: PostgreSQL 16 + PostGIS 3.4 → FastAPI services (auth/RBAC,
prediction, GIS, alert engine, scheduler, notifications) → web dashboard,
Flutter app, push channel. **Include: Figure 1**
(figures/system-architecture.png`); Table 4.1 (roles × permissions).

### 4.2 Database design
ER description of the schema (Alembic migrations 0001–0005); spatial
convention (`Geometry(POINT, 4326)`); natural-key deduplication on imports.

### 4.3 Prediction service
Model registry design; `/risk/predict?model=` API; per-prediction
explanations (feature contributions); every prediction persisted with
provenance.

### 4.4 GIS module and decision support
Layer inventory and methodology (risk thresholds, vulnerability priority,
trends); the summary/trends endpoints; dashboard views.
**Include: Figure 4** (figures/gis-framework.png`); screenshots of
the dashboard and Alert Center.

### 4.5 Mobile application
Flutter clean architecture; 8 screens; offline caching; secure token
storage; shelter finder; safety guide; report submission with photo and
GPS; FCM token registration (native wiring documented as integration
step). **Include:** app architecture diagram; screen screenshots.

### 4.6 Early warning automation
Weather ingestion; APScheduler cycle; alert decision table with cooldown
and escalation; FCM degraded mode; citizen-report verification workflow.
**Include: Figure 5** (figures/early-warning-workflow.png`).

### 4.7 Implementation summary
Phase-by-phase build log (1–6); test totals per phase (7 → 119);
technology choices and why.

---

## Chapter 5 — Results and Discussion

*Purpose: present findings, then interpret them against the literature.*

### 5.1 Dataset statistics
180 rows, 43 positives (23.9%); district and year distributions; monsoon
rainfall ranges; the 2022 concentration. **Include:** descriptive tables and
a bar chart of flood years per district.

### 5.2 Model comparison
The results table (RF 0.8611/0.4444/0.6154/0.9547; XGB 0.9167/0.6667/
0.8000/0.9465; MLP 0.9444/0.7778/0.8750/0.9630; CV F1 0.6147±0.2073,
0.6974±0.0935, 0.8028±0.1110); confusion matrices.
**Include: Figure 3** (figures/model-comparison.png`).

### 5.3 Feature importance and explanations
Per-model top features; the history-vs-rainfall disagreement between model
families; example per-prediction explanation.

### 5.4 GIS and decision-support findings
Vulnerability hotspots; risk/priority classifications; year-wise trends
2010–2024 and the Jul–Sep seasonal concentration (with the reporting-bias
caveat). **Include:** vulnerability map screenshot; trend charts.

### 5.5 System evaluation
Test suite results; live early-warning cycle verification (12/12 districts
evaluated, advisories issued and stored); smoke-test outcomes.

### 5.6 Discussion
Why the MLP won on recall; the conservative early-warning behaviour
(perfect precision, imperfect recall) and what it means operationally;
agreement with the literature (history and rainfall as dominant signals);
the uncertainty bands as an honest limit of 43 positives; implications for
PDMA/DDMA use — human review of borderline outlooks, auditability of
every alert.

### 5.7 Comparison with related work
How this framework differs: integrated operational stack vs. offline
susceptibility maps; reproducibility (data card, registry, SHA-256);
community feedback loop.

---

## Chapter 6 — Conclusion

*Purpose: close the loop on the research questions.*

### 6.1 Summary of findings
One paragraph per research question, answered with evidence.

### 6.2 Research contributions
Technical (integrated open-source ML+GIS+warning stack; reproducible
registry; automated cycle), disaster-management (Sendai Priorities 1 & 4;
decision-ready district outputs), and community (reporting with
verification; shelter finder; offline safety guide) — see
`docs/contribution.md`.

### 6.3 Limitations
The honest list from the research paper (Section 11): seasonal-vs-event
scale, small sample, reporting bias, provisional vulnerability weights,
sample infrastructure data, ERA5 limitations and train/serve shift,
temporal-leakage risk, operational limits (FCM credentials, single-instance
scheduler, multicast push, pending native FCM wiring).

### 6.4 Recommendations
For practitioners (how a PDMA could pilot this); for policymakers
(data-sharing for registries; community reporting governance).

### 6.5 Future work
Temporal-holdout validation; sub-seasonal labels; authoritative
registries; validated vulnerability index; per-district push; field trials
and user-acceptance testing; extension to other provinces and hazards.

---

## Appendices

- **A.** Data card (`datasets/processed/DATA_CARD.md`) — full dataset
  documentation.
- **B.** Model registry extract — configurations, metrics, dataset SHA-256.
- **C.** API specification summary (`docs/api-spec.md`).
- **D.** Database schema (`docs/database-schema.md`).
- **E.** Sample citizen-report verification records (anonymised).
- **F.** Test suite summary (119 tests, phase-by-phase totals).
