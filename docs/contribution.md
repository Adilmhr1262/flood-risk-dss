# Research Contribution Statement

**Project:** Flood Risk Prediction and Early Warning Decision Support System
**Case study:** Sindh, Pakistan (12 districts, 2010–2024)

> **Terminology rule.** This project never brands its predictive capability with
> artificial-intelligence terminology. Contributions are stated in terms of *machine learning-based
> prediction*, *data-driven* methods, and *decision support*.

---

## 1. Technical contribution

1. **The first integrated, open-source machine learning + GIS + automated
   early warning stack for district-scale flood risk in Sindh.** Prior work
   in the region stops at offline susceptibility maps or standalone
   forecasts; this framework carries the full path from raw sources to an
   operational warning loop in one reproducible codebase
   (PostgreSQL 16 + PostGIS 3.4, FastAPI, Leaflet dashboard, Flutter app).

2. **A reproducible research dataset with full provenance.** 180
   district-year rows (43 labelled flood years) built from 43 verified
   events with per-row source citations, ERA5 weather via Open-Meteo,
   static geographic attributes, and a documented composite vulnerability
   index — published with a data card, build scripts, and a dataset
   SHA-256 recorded in the model registry.

3. **A rigorous, honestly reported model comparison.** Random Forest, XGBoost,
   and MLP evaluated on a stratified held-out test set with 5-fold
   cross-validation; the MLP achieves F1 0.875 and ROC-AUC 0.963, and the
   wide confidence bands from the small positive sample are reported, not
   hidden.

4. **A versioned model registry with auditability.** Every model records its
   configuration, feature list, preprocessing parameters, metrics, and the
   exact dataset hash; every prediction served by the API persists its model
   version, probability, and contributing factors — a prerequisite for any
   predictive tool used in public-safety decisions.

5. **An automated early warning cycle.** Scheduled weather ingestion →
   prediction → alert decision (LOW/MEDIUM/HIGH with 6-hour cooldown
   deduplication and escalation) → push notification, verified live across
   all 12 study districts.

## 2. Disaster management contribution

1. **Directly supports Sendai Framework Priorities 1 and 4** —
   understanding disaster risk (quantified, explainable district risk) and
   enhancing preparedness for effective response (automated warnings,
   resource and shelter information, pre-monsoon trend analysis).

2. **Decision-ready outputs for PDMA/DDMA workflows.** Instead of raw
   probabilities, authorities receive risk levels with explanations,
   recommended actions, vulnerability-weighted priorities, active alerts,
   resource allocations, and an Alert Center for triage — designed around
   the questions a district officer asks before and during the monsoon.

3. **Closes the "last mile" with verified community reporting.**
   Categorised, geolocated citizen reports (flood water, road blockage,
   rescue request, medical emergency) with photo evidence pass through an
   authority verification workflow before entering situational awareness —
   fusing official forecasts with ground truth while guarding against
   unverified claims.

4. **Conservative-by-design warning behaviour.** The models' perfect
   precision / imperfect recall is characterised explicitly: flags are
   trustworthy, absence of a flag is not safety — the safer failure mode
   for automated advisories, paired with a requirement for human review of
   borderline cases.

## 3. Community impact

1. **A public mobile application** giving at-risk communities direct access
   to district risk assessments, flood alerts, nearby shelters with
   capacity, and emergency contacts — information that previously lived
   only inside government offices.

2. **An offline safety guide** bundled in the app, available without
   connectivity — critical when networks fail during floods.

3. **A volunteer reporting channel** that turns residents from passive
   warning recipients into active participants in the early warning
   system, with verification protecting the information commons.

4. **A foundation for local-language expansion.** The app's content
   architecture supports future Sindhi/Urdu localisation, which would
   extend reach to the communities most exposed and least served by
   English-language official channels.

5. **Capacity-building artefact.** The complete open codebase, documentation
   set, and research package serve as a teaching and replication resource
   for disaster-management students and practitioners in Pakistan and
   comparable flood-prone regions.

---

## Contribution summary (one paragraph)

This research delivers an end-to-end, open-source framework that converts
verified flood histories, reanalysis weather, and geographic data into
district-level flood risk predictions (best model F1 0.875, ROC-AUC 0.963),
serves them through GIS decision support and a community mobile app, and
closes the loop with an automated early warning cycle and verified citizen
reporting — advancing both the technical state of reproducible flood-risk
modelling for Sindh and the practical capacity of disaster managers and
communities to act on risk information, in line with the Sendai Framework.
