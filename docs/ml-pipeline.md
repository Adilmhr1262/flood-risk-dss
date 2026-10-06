# Machine Learning Pipeline

Data-driven flood risk prediction: CSV or live-database training data →
cleaning → feature engineering → training → evaluation → model registry →
prediction service.

## Pipeline stages

```
ml/data_loader.py        load_training_data("db" | <csv path>)
        │  9 base features + flooded label (1 = flood, 0 = no flood)
        ▼
ml/preprocessing.py      clean(): dedupe, numeric coercion, median imputation,
                         IQR outlier capping, label clipping; validate_ranges()
        │  fit_preprocessing() stores medians + capping bounds for inference
        ▼
ml/feature_engineering.py engineer(): adds 4 derived features
        │  - rain_intensity   = rainfall_mm * (humidity_pct / 100)
        │  - lowland_river    = (1/(1+elevation_m)) * (1/(1+river_distance_km))
        │  - exposure_index   = log1p(population_density) * (1 + prev_flood_events)
        │  - flood_history_score = recency-weighted past-event count
        │    (exponential 5-year decay applied at load time in data_loader)
        ▼
ml/pipeline.py           run_training(): 80/20 stratified split, 5-fold CV,
                         StandardScaler + classifier pipeline
        ▼
ml/evaluate.py           evaluate(): accuracy, precision, recall, f1,
                         ROC-AUC, confusion matrix, classification report
        ▼
ml/predict.py            FloodPredictor: loads a model directory, applies the
                         identical preprocessing + engineering, predict_proba()
```

`ml/pipeline.py` also keeps the original import surface (`load_dataset`,
`clean`, `train_models`, `evaluate`, `save_model`, `load_model`) as thin
delegates for backwards compatibility.

## Training a model

```bash
cd backend
# from the live database (recommended)
DATABASE_URL="postgresql+psycopg2://flood_dss:flood_dss_dev@localhost:5432/flood_risk_dss" \
  .venv/bin/python -m ml.train --data db --model rf --out ml/models/rf-v1

# from a CSV file
.venv/bin/python -m ml.train --data ml/sample_training_data.csv --model mlp --out ml/models/mlp-v1
```

`--model` chooses `rf` (Random Forest), `xgb` (XGBoost — requires the
`xgboost` package, currently not installed) or `mlp` (multi-layer
perceptron).

Each run writes into the output directory:

| File | Contents |
|---|---|
| `model.joblib` | trained sklearn pipeline (StandardScaler + classifier) |
| `feature_names.json` | ordered feature list (9 base + 4 engineered) |
| `preprocessing.json` | imputation medians + IQR capping bounds |
| `metrics.json` | accuracy, precision, recall, f1, roc_auc, confusion matrix, 5-fold CV f1, row counts, timestamp |
| `feature_importance.json` | normalised per-feature importance (tree models only) |

## Training data from the live database

`data_loader.load_from_db()` joins `flood_events` to `geographic_data`:

- **Positives:** every documented flood event (`flood_status = true`).
  `prev_flood_events` is the exponentially decayed count of earlier events
  in the same district (5-year time constant); `last_severity` is the most
  recent prior event's severity (0 if none).
- **Negatives:** three synthetic non-flood observations per district with
  overlapping weather ranges (rainfall 2–130 mm, humidity 25–85%), so the
  model must learn the geographic distinction rather than a trivial
  rainfall threshold.

The historical record stores only floods, so the negative class is synthetic
by necessity — see the caveat below.

## Model registry (`ml/registry.json`)

```json
{
  "rule-based-v1": {
    "type": "rule-based",
    "version": "v1.0.0-rule-based",
    "description": "...",
    "always_available": true
  },
  "rf-v1": {
    "type": "sklearn",
    "version": "rf-v1",
    "model": "rf",
    "model_dir": "ml-models/models/rf-v1",
    "description": "...",
    "metrics": { "accuracy": 1.0, "precision": 1.0, ... },
    "trained_at": "2026-09-26T07:23:43Z",
    "data_source": "db"
  }
}
```

Register a newly trained model by adding an entry with `type: "sklearn"`,
`model_dir` relative to `backend/`, and its metrics. The prediction service
picks it up automatically; `GET /api/v1/risk/model-info` exposes the full
registry with metrics and feature importance.

## rf-v1 metrics (trained 2026-09-26)

Trained on 88 rows from the live database (52 documented flood events + 36
synthetic non-flood observations), 70 train / 18 test, Random Forest with
300 trees.

| Metric | Value |
|---|---|
| Accuracy | 1.0000 |
| Precision | 1.0000 |
| Recall | 1.0000 |
| F1 | 1.0000 |
| ROC-AUC | 1.0000 |
| 5-fold CV F1 | 0.9749 ± 0.0308 |
| Confusion matrix | [[7, 0], [0, 11]] |

Top features: humidity_pct (0.30), rain_intensity (0.28), rainfall_mm
(0.21), temperature_c (0.10), exposure_index (0.03).

**Caveat (report honestly):** the training set is small (88 rows) and the
negative class is synthetic, so these near-perfect scores are optimistic.
They demonstrate the pipeline works end to end, not that the model is
production-ready. Metrics will become meaningful as real non-flood
observations (dry-season district records) are added to the training set —
the loader, pipeline, and registry already support retraining without code
changes.

## How the prediction service uses models

`app/services/prediction_service.py` (`PredictionService`):

1. Runs the deterministic rule-based engine on every request — its
   normalised feature contributions produce the human-readable risk
   factors.
2. If the requested model (default `rf-v1`, selectable via
   `POST /api/v1/risk/predict?model=...`) exists in the registry and its
   artifacts are present, its probability becomes the reported probability;
   the risk level, factors, and recommendations follow the standard
   LOW/MEDIUM/HIGH contract.
3. If the model is missing, it falls back to the rule-based score and adds
   an explanatory `note` to the response.
4. Every assessment is persisted to the `predictions` table with
   `input_features` (JSONB), factors/recommendations arrays, and the
   requesting user's id.
