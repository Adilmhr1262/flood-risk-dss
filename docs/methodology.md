# Research Methodology

**Project:** Flood Risk Prediction and Early Warning Decision Support System
**Type:** Master's-level research and software project (Disaster Management)
**Approach:** Quantitative computational research

---

## 1. Research Title

*A Machine Learning-Based Flood Risk Prediction Framework Using Environmental and
Geospatial Data for Disaster Risk Reduction.*

## 2. Research Problem

Floods are among the most frequent and destructive natural hazards in Pakistan,
with the 2010 super floods and the 2022 monsoon floods each displacing millions
and causing severe economic loss. Disaster management authorities, NGOs, and
at-risk communities need timely, location-specific flood risk information to
support evacuation planning, relief logistics, and public safety communication.
This research develops a data-driven framework that converts environmental,
geographic, historical, and social data into actionable flood risk assessments.

## 3. Research Questions

1. Which combination of environmental, geographic, and historical indicators best
   predicts flood occurrence at the district level?
2. How accurately can machine learning-based classification models distinguish
   low, medium, and high flood-risk areas?
3. How can predicted risk be communicated effectively through GIS visualization
   and early warning interfaces for three distinct user groups (authorities,
   NGOs, public)?
4. What decision-support outputs (risk factors, recommendations, reports) are
   most useful to disaster management practitioners?

## 4. Research Design

Quantitative computational research with a design-science orientation: the
artefact (the decision support system) is both the instrument and a primary
research output. The study proceeds in six phases mirroring the software
development lifecycle.

## 5. Data Collection

| Category | Variables | Sources |
|---|---|---|
| Environmental | Rainfall (mm), temperature (°C), humidity (%) | Pakistan Meteorological Department records, NDMA situation reports |
| Geographic | Elevation (m), river distance (km), slope (°), coordinates | SRTM digital elevation data, Indus river network, PostGIS spatial store |
| Historical | Flood events, severity (1–5), damage, affected population | NDMA/PDMA reports (2010, 2011, 2015, 2020, 2022, 2023–2024) |
| Social | Population density, vulnerability index (0–1) | Census data, composite vulnerability indicators |

Inclusion criteria: district-level records with verified flood status and
complete environmental readings. The 2022 flood events form the primary
positive-class corpus (21 documented events in the seed dataset).

## 6. Data Preprocessing

1. **Cleaning** — missing-value imputation (median for numeric, mode for
   categorical), duplicate removal, outlier detection via IQR on rainfall and
   elevation.
2. **Normalization** — min–max scaling of continuous features to [0, 1] for
   distance-based models; inverse scaling for protective factors (elevation,
   river distance, slope).
3. **Encoding** — one-hot encoding of categorical fields (province, severity
   bands); ordinal encoding of risk levels.
4. **Class balancing** — stratified sampling / SMOTE review, since non-flood
   records outnumber flood events.
5. **Train/test split** — 80/20 stratified split with 5-fold cross-validation.

## 7. Feature Engineering

Derived features capturing domain knowledge:

- `rain_intensity` — rainfall normalized against district historical maximum.
- `lowland_river` — interaction term: (1 − normalized elevation) ×
  (1 − normalized river distance), capturing floodplain exposure.
- `exposure_index` — population density × vulnerability index, quantifying
  human impact potential.
- `flood_history_score` — exponentially weighted count of previous events,
  giving recent floods (e.g. 2022) higher influence.

Feature importance is extracted from tree-based models to rank the main risk
factors shown to end users.

## 8. Model Development

Three supervised classifiers are trained and compared:

1. **Random Forest** — ensemble of decision trees; robust to non-linear
   interactions and missing data; provides native feature importance.
2. **XGBoost** — gradient-boosted trees; typically the strongest tabular
   performer; tuned via grid search (depth, learning rate, estimators).
3. **Artificial Neural Network (multi-layer perceptron)** — captures complex
   non-linear relationships; trained with early stopping and dropout
   regularization.

A deterministic weighted-scoring baseline (v1 risk engine, documented weights
summing to 1.0) provides an interpretable reference and a fallback when
trained models are unavailable.

## 9. Model Evaluation

| Metric | Purpose |
|---|---|
| Accuracy | Overall correctness |
| Precision | Reliability of HIGH-risk predictions (avoid false alarms) |
| Recall | Capture of actual flood events (avoid missed warnings) |
| F1 Score | Balance of precision and recall |
| ROC-AUC | Discrimination across thresholds |

Models are compared on the held-out test set; confusion matrices and
threshold-sensitivity analysis inform the LOW (< 0.33) / MEDIUM (< 0.66) /
HIGH (≥ 0.66) classification boundaries. Recall is prioritized for the HIGH
class: a missed warning costs more than a false alarm in disaster contexts.

## 10. GIS Integration

Predicted probabilities are joined to district geometries in PostGIS and
served as GeoJSON risk layers (green = low, yellow = medium, red = high),
overlaid with historical flood event layers. The interactive map supports
location search, zoom, and layer toggling for situational awareness.

## 11. Decision Support System Development

The validated model is deployed behind a REST API (FastAPI) serving three
role-based interfaces: an authority dashboard (monitoring, reports, alerts),
an NGO view (affected areas, vulnerability, relief planning), and a public
mobile interface (location risk check, alerts, emergency information, safety
guidelines). Every prediction returns an explanation: probability, risk level,
main risk factors, and actionable recommendations.

## 12. Validation Strategy

- **Statistical validation** — cross-validated metrics on historical data.
- **Case validation** — back-testing against the 2022 flood events: the
  system must classify heavily affected districts (Dadu, Larkana, Thatta,
  Jacobabad) as HIGH risk.
- **Expert review** — structured feedback from disaster management
  practitioners on the usefulness of risk factors and recommendations.
- **Usability testing** — task-based evaluation of the dashboard and mobile
  interfaces with representative users from each role.

## 13. Expected Outcomes

1. A validated flood risk prediction framework with documented performance.
2. An operational decision support system (web dashboard + mobile application
   + GIS visualization).
3. A replicable methodology for data-driven flood risk assessment in
   data-scarce regions.
4. A research publication and the foundation for a Master's thesis in
   Disaster Management.

## 14. Limitations

- District-level granularity cannot capture street-level flash flooding.
- Historical records are incomplete for remote districts (reporting bias).
- The framework predicts risk probability, not exact flood timing or depth;
  it complements, rather than replaces, hydrological forecasting models.
- Real-time sensor and satellite integration are future work (Phase 6+).

## 15. Research Ethics

All data used are from public institutional sources or synthetic training
data. No personal data are collected. Location data are aggregated at
district level; individual user locations in the mobile application are
processed on-device where possible and never stored without consent.
