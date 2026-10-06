# Master's Research Proposal

**A Machine Learning-Based Flood Risk Prediction and GIS Decision Support Framework for Disaster Risk Reduction: A Case Study of Sindh, Pakistan**

*Programme: Master's in Disaster Management · Candidate: Aadil Ali Mahar*
*Draft: 2026-09-26*

> **Terminology note.** This research never brands its predictive capability with
> artificial-intelligence terminology. All predictive components are described as *machine learning-based* or
> *data-driven*, consistent with the project's standing terminology rule.

---

## 1. Research title

**A Machine Learning-Based Flood Risk Prediction and GIS Decision Support
Framework for Disaster Risk Reduction: A Case Study of Sindh, Pakistan**

## 2. Background

Pakistan is among the countries most exposed to flood hazard. The 2010 super
floods affected over 20 million people across the Indus basin, and the 2022
monsoon floods killed more than 1,700 people, displaced 8 million, and caused
damages above USD 30 billion — with Sindh bearing the heaviest losses. In
Sindh, districts along the Indus — Dadu, Larkana, Shikarpur, Jacobabad,
Sukkur, Badin, Thatta — flood repeatedly, yet district-level risk assessment
remains largely qualitative, fragmented across agencies, and difficult for
communities to access.

Pakistan's flood forecasting infrastructure (the Flood Forecasting Division,
PDMA Sindh) produces valuable river-flow and rainfall forecasts, but
translating forecasts into *district-level, actionable risk information* —
which districts to warn, where to pre-position relief, which shelters to open
— remains a manual, expertise-driven process. Global systems such as GloFAS
operate at coarse resolutions unsuited to district operational decisions, and
the machine-learning literature on flood susceptibility mapping rarely
progresses beyond offline susceptibility maps to integrated, operational
decision support. The persistent "last mile" problem — forecasts exist, but
the translation into local decisions and community action is weak — motivates
this research.

A proof-of-concept implementation of this framework has been built: a
purpose-built dataset for 12 districts of Sindh and adjacent Punjab border
districts (2010–2024; 180 district-year rows, 43 labelled flood years, each
event carrying its own source citation), a three-model comparison (Random
Forest F1 0.615, XGBoost F1 0.800, MLP F1 0.875 with ROC-AUC 0.963) on a
stratified held-out test set with 5-fold cross-validation, and an operational
platform (FastAPI prediction service, PostgreSQL 16 + PostGIS 3.4 spatial
layers, Leaflet dashboard, Flutter community mobile app, and an automated
early-warning cycle). This proposal extends that foundation into a Master's
thesis that strengthens the methodology, validates the system with real
practitioners, and answers research questions the proof of concept raised but
could not settle.

## 3. Motivation

Three gaps justify the proposed research:

1. **The operational gap.** Most flood-risk modelling research ends at a
   trained model. Disaster managers need decision-ready outputs — risk levels
   with explanations, recommended actions, vulnerability-weighted priorities,
   and verified community observations — embedded in the workflows they
   already use. Research that carries models into an auditable, operational
   decision-support platform is scarce for Pakistan.

2. **The methodological gap.** The proof-of-concept's stratified train/test
   split mixes years, leaving temporal leakage risk managed but not
   eliminated; its models are district-year (seasonal) classifiers while
   operational use is event-scale; and its vulnerability composite uses
   reasoned but unvalidated weights. Each of these is a legitimate,
   publishable methodological contribution once addressed honestly.

3. **The validation gap.** The system has been smoke-tested technically but
   never evaluated by its intended users — PDMA/DDMA officers and at-risk
   communities. A Master's thesis that subjects the framework to structured
   expert review and community user-acceptance testing directly serves the
   Sendai Framework for Disaster Risk Reduction (Priorities 1 and 4) and
   produces transferable knowledge for comparable flood-prone regions.

## 4. Objectives

1. To design and build a reproducible, provenance-tracked dataset of
   district-level flood risk for Sindh (2010–2024) and extend it with
   sub-seasonal labels suitable for operational early warning.
2. To develop, compare, and rigorously validate machine learning-based
   flood risk models — including temporal-holdout evaluation, honest
   uncertainty reporting, and a validated vulnerability index — and deploy
   the best-performing model behind an auditable prediction service with a
   versioned model registry.
3. To integrate the models into a complete decision-support platform
   (GIS visualisation, automated early-warning cycle with cooldown and
   escalation logic, community reporting with authority verification) and
   evaluate it with disaster-management practitioners and community users
   for usability, usefulness, and trust.

## 5. Research questions

1. Can a district-year flood risk classifier trained on verified historical
   events, ERA5 reanalysis weather, and geographic attributes achieve
   reliable discrimination (ROC-AUC) on a strict temporal holdout
   (train ≤ 2019, test 2020–2024), and how does performance compare with a
   stratified split?
2. Which features drive flood-risk predictions across model families
   (Random Forest, XGBoost, MLP), and does the observed disagreement —
   tree ensembles splitting on flood history while the network leans on
   rainfall — persist under temporal validation?
3. What are the operational consequences of the models' conservative
   behaviour (perfect precision, imperfect recall on the current test set),
   and how should threshold choice be governed for automated advisories?
4. Can sub-seasonal (event-scale) flood labels be constructed for the study
   area with sufficient reliability to close the seasonal-vs-event-scale
   modelling gap, and does an event-scale model improve actionable lead
   time over the district-year classifier?
5. To what extent do PDMA/DDMA officers and community users find the
   integrated decision-support outputs (risk summaries, alert workflows,
   verified citizen reporting) trustworthy and usable in pre-monsoon
   planning and response, and what changes does their feedback require?

## 6. Methodology

**Study area and data.** 12 districts (10 Sindh + Dera Ghazi Khan and
Rajanpur, Punjab, on the Sindh border), 2010–2024, at district-year grain
(180 rows, 43 positive), extending to sub-seasonal event windows where
documentation permits. Sources: NDMA situation reports, PDMA Sindh Flood
Impact Report 2022, WHO/IFRC/OCHA/ReliefWeb reports (per-row citations),
ERA5 reanalysis via the Open-Meteo archive API, static geographic
attributes, and authoritative infrastructure registries to replace the
current sample data.

**Model development.** Feature engineering from domain knowledge
(monsoon-season weather aggregates, exposure attributes, historical
susceptibility, interaction terms); leakage-safe preprocessing (parameters
fit on training data only); three classifiers with literature-consistent
defaults; evaluation on a stratified 80/20 split *and* a temporal holdout;
5-fold cross-validation reporting F1 mean ± standard deviation; permutation
and built-in feature importance; per-prediction contributing factors for
auditability.

**System development.** PostgreSQL 16 + PostGIS 3.4 data layer; FastAPI
application layer with JWT authentication and role-based access control
(authority/ngo/public/volunteer); versioned model registry recording
configuration, features, metrics, and dataset SHA-256; automated early
warning cycle (Open-Meteo forecast ingestion → prediction → alert engine
with LOW/MEDIUM/HIGH levels, 6-hour cooldown deduplication, and
escalation) → push notification with graceful degraded mode; Leaflet
decision-support dashboard; Flutter community mobile app (Flutter 3.47.5).

**Evaluation.** (a) Quantitative: test-set and temporal-holdout metrics,
confusion matrices, calibration of the conservative precision/recall
trade-off. (b) Qualitative: structured walkthroughs and task-based
user-acceptance testing with PDMA/DDMA officers and community members,
analysed thematically; findings feed back into system iterations.

**Ethics and limitations.** No fabricated signatures or forged documents;
citizen reports enter situational awareness only through authority
verification; reporting bias, the small positive sample, and provisional
vulnerability weights are stated explicitly in all outputs.

## 7. Expected contribution

- **Technical:** the first integrated, open-source machine learning + GIS
  + automated early-warning stack for district-scale flood risk in Sindh
  carried from raw sources to an operational warning loop; a reproducible
  dataset with full provenance; a rigorous multi-model comparison with
  honestly reported uncertainty; a versioned, auditable model registry.
- **Disaster management:** decision-ready outputs designed around a
  district officer's pre-monsoon questions (risk levels with explanations,
  recommended actions, vulnerability-weighted priorities, alert triage);
  support for Sendai Framework Priorities 1 (understanding risk) and 4
  (preparedness); a verified community-reporting channel addressing the
  "last mile" problem.
- **Community and capacity-building:** a public mobile app giving at-risk
  communities direct access to risk information, shelters, and alerts plus
  an offline safety guide; an open codebase and documentation set as a
  teaching and replication resource for disaster-management students and
  practitioners in Pakistan and comparable regions.

## 8. Timeline

| Month | Milestone |
|---|---|
| 1 | Finalise proposal; literature review (flood susceptibility mapping, EWS, Sendai Framework); ethics clearance for practitioner/community evaluation |
| 2 | Extend dataset: authoritative infrastructure registries, sub-seasonal event-window labelling; data card v2 |
| 3 | Feature engineering v2; validated vulnerability index; temporal-holdout experimental design |
| 4 | Train and compare Random Forest, XGBoost, MLP (+ baselines) on stratified and temporal splits; uncertainty analysis |
| 5 | Threshold and calibration study; conservative-behaviour analysis; per-prediction explainability |
| 6 | Prediction service + model registry v2; event-scale inputs; integration tests |
| 7 | GIS decision-support extensions (vulnerability map, trends); early-warning cycle refinements (per-district push subscriptions) |
| 8 | Mobile app: production FCM wiring, Sindhi/Urdu localisation groundwork, field readiness |
| 9 | Practitioner evaluation: structured walkthroughs with PDMA/DDMA officers; iterate on findings |
| 10 | Community user-acceptance testing (alerts, shelters, reporting workflow); iterate on findings |
| 11 | Thesis writing: methodology, results, discussion, limitations; research paper revision |
| 12 | Final revisions, defence preparation; open-source release of dataset, models, and code |
