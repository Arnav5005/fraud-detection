# Product Requirements Document

## Explainable Real-Time Fraud Detection System

**Status:** MVP definition and implementation handoff  
**Owner:** Fraud Detection Project  
**Date:** 2026-09-30  
**Target release:** Local MVP, followed by production-ready deployment

## 1. Product Summary

Build an explainable fraud-detection application that scores a credit-card transaction in real time, returns a fraud probability and human-readable reasons, records the decision, and gives fraud analysts a dashboard for reviewing recent activity and aggregate trends.

The product is an analyst decision-support tool. It does not automatically decline a transaction or replace human investigation. A prediction is a risk signal that can support review and downstream controls.

## 2. Problem Statement

The benchmark dataset contains 284,807 transactions and only 492 fraud cases, or approximately 0.17% of all transactions. Accuracy alone would therefore be misleading: a model could appear highly accurate while missing most fraud. The system must prioritize fraud-relevant measures such as precision, recall, F1, ROC-AUC, and the operational trade-off created by the decision threshold.

Analysts also need to understand why a transaction was flagged. A probability without an explanation is difficult to review, audit, or improve. Each scored transaction must therefore retain its prediction and its leading SHAP-based feature contributions.

## 3. Goals and Success Criteria

### Goals

- Score one transaction through a REST API with a target response time below 100 ms after model initialization.
- Validate every request before model inference.
- Return a probability, a threshold-based verdict, and the top contributing features.
- Persist every prediction for audit, review, and aggregate statistics.
- Provide a dashboard for recent transactions, fraud counts/rate, and prediction explanations.
- Keep the model-serving layer database-agnostic through SQLAlchemy so SQLite can later be replaced by PostgreSQL.

### Success criteria

- A valid transaction produces a stable prediction response and a persisted transaction record.
- Invalid or negative `Time`/`Amount` values are rejected with a clear validation error.
- A prediction can be retrieved later by its transaction ID, including its explanation.
- Dashboard totals and transaction rows match the persisted API data.
- Evaluation reports include precision, recall, F1, ROC-AUC, and a confusion matrix; accuracy is not the primary selection criterion.
- The deployed or local service can be demonstrated end to end: request, score, database record, explanation, and dashboard update.

## 4. Non-Goals for MVP

- Automatically approving, declining, freezing, or reversing financial transactions.
- Connecting to a bank, payment processor, or live card network.
- Identity resolution, customer profiles, merchant enrichment, or device fingerprinting.
- Multi-currency conversion or external exchange-rate integrations.
- Continuous online learning or automatic model retraining.
- Multi-user authentication and role-based permissions.
- Guaranteeing production regulatory compliance from the benchmark dataset alone.

## 5. Users and Primary Workflows

### Fraud analyst

1. Open the monitoring dashboard.
2. Review recent transactions sorted by timestamp.
3. Identify high-probability fraud using the verdict and probability badge.
4. Open a transaction explanation.
5. Review the top contributing features and use the result as an investigation signal.

### Developer or model owner

1. Train and evaluate candidate models from the benchmark CSV.
2. Select the model and threshold using fraud-relevant metrics.
3. Save the model, scaler, threshold, and SHAP explainer as versioned artifacts.
4. Start the FastAPI service and verify health, prediction, persistence, and statistics.
5. Inspect logged predictions and monitor basic service behavior.

## 6. Product Scope

### 6.1 Data and model pipeline

- Use the Kaggle credit-card fraud dataset stored as `creditcard.csv`.
- Treat `Class` as the training label: `0` legitimate and `1` fraud.
- Accept the input features `Time`, `V1` through `V28`, and `Amount`.
- Convert `Time` into an hour-of-day feature using the existing notebook approach.
- Apply `log1p` to `Amount` and standardize the configured numeric features using a persisted scaler.
- Perform an 80/20 stratified train/test split with a fixed random seed.
- Apply SMOTE only to the training partition to prevent test-set leakage.
- Compare Logistic Regression, Random Forest, and XGBoost during development.
- Serve the selected XGBoost model with its persisted scaler and tuned classification threshold.
- Generate per-transaction explanations with the persisted SHAP TreeExplainer.

### 6.2 Backend API

The backend is a FastAPI service using Pydantic validation, SQLAlchemy, and SQLite for the MVP.

| Endpoint        | Method | Purpose                                                                   |
| --------------- | -----: | ------------------------------------------------------------------------- |
| `/predict`      |   POST | Validate and score one transaction; persist the result.                   |
| `/transactions` |    GET | Return recent prediction records for the dashboard.                       |
| `/stats`        |    GET | Return total transactions, fraud count, legitimate count, and fraud rate. |
| `/explain/{id}` |    GET | Return the stored or reproducible explanation for one prediction.         |

#### Prediction request

A request contains numeric values for:

- `Time`
- `V1` through `V28`
- `Amount`

`Time` and `Amount` must be non-negative. The API must reject missing, non-numeric, or extra-invalid values with a documented 4xx response.

#### Prediction response

```json
{
  "transaction_id": 123,
  "fraud_probability": 0.94,
  "verdict": "fraud",
  "top_reasons": ["V14", "V10", "V12"]
}
```

The verdict must be derived from the persisted model threshold, not hard-coded to `0.5`. The response must identify the created database record.

### 6.3 Persistence

The MVP stores one record per prediction in the `transactions` table:

- Generated transaction ID
- Raw `Time` and `Amount`
- Derived hour and transformed amount
- Fraud probability
- Verdict
- Top explanation reasons
- UTC timestamp

The database layer must close sessions reliably and avoid losing a prediction when a request completes successfully. SQLite is the default local database; PostgreSQL migration is a later deployment concern.

### 6.4 Dashboard

The planned React dashboard must provide:

- Summary cards for total transactions, fraud count, legitimate count, and fraud rate.
- A recent transaction table with timestamp, amount, probability, and verdict.
- A fraud-rate or activity trend chart.
- A transaction explanation view showing the top SHAP feature contributions.
- A demo mode that can submit ten synthetic or sampled transactions for local demonstration.
- Loading, empty, API-error, and unavailable-backend states.

The dashboard must consume the API rather than read the SQLite file directly.

## 7. Functional Requirements

### FR-1: Transaction validation

The service shall validate the complete feature payload before inference. `Time` and `Amount` shall reject negative values. Validation errors shall identify the affected field and return a client error.

### FR-2: Model inference

The service shall load model artifacts at startup or through a controlled lazy-loading path and shall apply the same preprocessing used during training. The service shall return a probability in the inclusive range `[0, 1]` and a threshold-based verdict.

### FR-3: Explainability

For every successful prediction, the service shall provide up to three leading feature reasons ordered by contribution magnitude. Explanations shall be tied to the transaction ID and use the same feature representation supplied to the model.

### FR-4: Prediction audit log

Every successful prediction shall be written to the database with the model output, derived values, explanation reasons, and UTC creation time.

### FR-5: Transaction retrieval

The service shall return recent records in reverse chronological order. The endpoint shall support a bounded page size or limit to prevent unbounded responses.

### FR-6: Aggregate statistics

The service shall calculate totals from persisted records. Fraud rate shall be `fraud_count / total_transactions`, with a defined zero-record behavior of `0`.

### FR-7: API documentation and health

FastAPI's generated OpenAPI documentation shall describe request and response schemas. A lightweight health or readiness check should confirm that required model artifacts can be loaded before serving traffic.

### FR-8: Dashboard synchronization

After a successful prediction, the dashboard shall refresh or update the transaction feed and summary statistics without requiring a full page reload.

## 8. Non-Functional Requirements

- **Latency:** Target p95 prediction response below 100 ms on the local MVP after model warm-up, excluding cold-start loading.
- **Reliability:** A malformed request must not crash the service. Database sessions must be closed on success and failure paths.
- **Reproducibility:** Training uses documented preprocessing, a fixed random seed, and versioned artifacts.
- **Data integrity:** The test set must remain untouched by SMOTE and must not be used to fit scalers or other learned transforms.
- **Observability:** Log request failures, model-loading failures, prediction completion, and database errors without logging secrets.
- **Security baseline:** Do not expose raw credentials or unrestricted production endpoints. Configure CORS narrowly for the dashboard origin before deployment.
- **Accessibility:** Dashboard tables, status colors, and explanation content must remain understandable without relying on color alone.
- **Maintainability:** Keep feature transformation shared between training and inference to prevent training-serving skew.

## 9. Model Evaluation and Release Gate

The model comparison must report precision, recall, F1, ROC-AUC, and a confusion matrix for each candidate. The selected threshold must be tuned on a documented validation strategy rather than assumed to be 0.5.

A model is eligible for MVP serving only when:

- Its evaluation results are recorded and reproducible.
- The selected threshold and preprocessing artifacts are saved with the model.
- It demonstrates an acceptable precision/recall trade-off for the intended analyst workflow.
- Inference uses the same feature order and transformations as evaluation.
- A representative positive and negative request can be scored successfully.

The PRD intentionally does not prescribe a numeric precision or recall target until the product owner chooses the operational cost of false positives versus missed fraud. That decision is a release dependency.

## 10. Data Contract

The source CSV has 31 columns: `Time`, `V1`-`V28`, `Amount`, and `Class`. It contains 284,807 data rows and no missing values according to the EDA notebook. The label is required for training but must not be accepted as a prediction input.

The API feature order must be explicit and tested. Raw `Time` and `Amount` are retained for logging, while model input uses the documented derived/transformed representation. Feature names in SHAP output must map back to the same names shown in the dashboard.

## 11. Delivery Plan

### Phase 1: Model package

- Finalize reusable feature transformation code.
- Add a train script and recorded comparison results.
- Validate leakage controls and save model artifacts.

### Phase 2: Serving MVP

- Implement FastAPI startup, artifact loading, and `/predict`.
- Complete database initialization and prediction logging.
- Implement `/transactions`, `/stats`, `/explain/{id}`, and health/readiness behavior.
- Add API tests for valid, invalid, and boundary payloads.

### Phase 3: Analyst dashboard

- Create the React application and API client.
- Implement summary cards, transaction feed, trend chart, and explanation view.
- Add loading, empty, error, and demo states.

### Phase 4: Release hardening

- Fix dependency installation metadata and pin compatible versions.
- Add request, model, database, and dashboard integration tests.
- Document local setup and API usage.
- Evaluate deployment on a managed backend and frontend platform only after local acceptance passes.

## 12. Acceptance Criteria

- [ ] A complete valid payload returns HTTP 200 with `transaction_id`, probability, verdict, and reasons.
- [ ] Negative `Time` and `Amount` values return HTTP 422 or the documented validation status.
- [ ] The prediction probability is between 0 and 1 and the verdict agrees with the saved threshold.
- [ ] A successful prediction creates exactly one retrievable database record.
- [ ] `/transactions` returns records with the documented fields and bounded ordering.
- [ ] `/stats` counts persisted fraud and legitimate verdicts correctly, including the empty database case.
- [ ] `/explain/{id}` returns an explanation for an existing record and a documented 404 for an unknown ID.
- [ ] Model artifacts fail fast with a clear readiness error when missing or incompatible.
- [ ] API response latency is measured and reported under a repeatable local test.
- [ ] The dashboard displays live API data and handles backend failure without a blank or misleading state.
- [ ] Training and inference use identical feature order and preprocessing.
- [ ] Evaluation results and the selected threshold are checked into project documentation or generated result artifacts.

## 13. Risks and Mitigations

| Risk                          | Impact                                    | Mitigation                                                                                                 |
| ----------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Extreme class imbalance       | Missed fraud or excessive false positives | Use stratification, training-only SMOTE, threshold tuning, and precision/recall reporting.                 |
| Training-serving skew         | Unreliable production scores              | Centralize preprocessing and add feature-order contract tests.                                             |
| SHAP artifact incompatibility | Explanations fail at runtime              | Pin compatible versions and add an explanation smoke test.                                                 |
| SQLite concurrency limits     | Writes fail as usage grows                | Keep SQLAlchemy boundaries clean and plan PostgreSQL migration before scale-up.                            |
| Benchmark data limitations    | Poor real-world generalization            | Label the system as a benchmark/demo, avoid claiming bank-grade performance, and plan new validation data. |
| Dependency drift              | Setup or deployment failures              | Replace incorrect package names, pin versions, and verify installation in a clean environment.             |
| Threshold misuse              | Analyst overload or missed cases          | Show the probability and threshold-derived verdict, and make operating costs an explicit product decision. |

## 14. Open Decisions

- What probability threshold and false-positive budget are acceptable for the analyst workflow?
- Should explanations show only feature names, or feature names plus signed SHAP values and transformed values?
- What default transaction page size and maximum API limit should be used?
- Should the dashboard auto-refresh on a timer, use manual refresh, or use a streaming mechanism later?
- Which authentication and CORS policy are required before any public deployment?
- What model version, artifact checksum, and training timestamp must be stored with each prediction?

## 15. Current Implementation Notes

The repository already contains the benchmark CSV, EDA notebook, saved model/scaler/threshold/SHAP artifacts, a SQLAlchemy transaction model, and Pydantic schema definitions. The FastAPI entry point, predictor, and explainer modules are currently empty, and no frontend directory is present yet. This PRD therefore describes the target MVP and identifies the remaining implementation work; it should not be read as evidence that every listed endpoint or dashboard screen already exists.
