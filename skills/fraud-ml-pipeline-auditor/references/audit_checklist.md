# Fraud ML Pipeline Audit Checklist & Defect Catalog

Use this checklist to perform comprehensive inspections across all 8 pipeline phases.

## Phase 1: Pre-Execution Inspection
- [ ] Inspect existing directory structure and identify present vs missing artifacts (`creditcard.csv`, notebooks, models, scalers).
- [ ] Inspect git status / branch clean state to prevent accidental overwrites.
- [ ] Confirm Python dependencies (`scikit-learn`, `pandas`, `numpy`, `imblearn`, `xgboost`, `shap`, `fastapi`, `pydantic`, `sqlalchemy`).
- [ ] Check if baseline models or metrics already exist and record baseline values.

## Phase 2: Dataset Integrity Audit
- [ ] **Schema Check**:
  - File exists at specified path (e.g., `data/creditcard.csv`).
  - Column count is 31: `Time`, `V1` to `V28`, `Amount`, `Class`.
- [ ] **Data Quality**:
  - Null/NaN count across all columns is 0.
  - Infinite values count across all columns is 0.
  - Check duplicate row count (document if ~1,081 duplicates exist and whether deduplication is applied).
  - Verify `Time >= 0` and `Amount >= 0`.
- [ ] **Label Distribution**:
  - `Class` values are strictly `{0, 1}`.
  - Normal transactions count: ~284,315 (~99.828%).
  - Fraud transactions count: ~492 (~0.172%).

## Phase 3: Data Leakage & Resampling Audit
- [ ] **Split Timing**: Stratified split performed *before* any transformations.
- [ ] **Stratification**: `stratify=y` used on all splits to ensure equal fraud prevalence across train, validation, and test splits.
- [ ] **Scaler / Transformation Isolation**:
  - `scaler.fit(X_train)` or `scaler.fit_transform(X_train)` used strictly on training data.
  - Only `scaler.transform()` called on validation and test data.
  - No global mean/std computed on the entire dataset.
- [ ] **SMOTE / Resampling Isolation**:
  - `SMOTE.fit_resample(X_train, y_train)` applied strictly to training data.
  - Never applied to validation data.
  - Never applied to test data.
- [ ] **Threshold Tuning Partition**:
  - Optimization of threshold conducted solely on validation set predictions.
  - Final test set remained completely isolated and unobserved during model/threshold selection.

## Phase 4: Model Comparison & Metric Discipline
- [ ] **Algorithm Baseline**: Compare all three required models:
  - Logistic Regression (linear baseline)
  - Random Forest (ensemble bagging)
  - XGBoost (gradient boosting)
- [ ] **Seed Control**: Fixed `random_state` across model seeds and data splitters.
- [ ] **Positive Class**: Explicitly configured `pos_label=1` (Fraud).
- [ ] **Metrics Computed**:
  - Precision, Recall, F1, F0.5
  - ROC-AUC
  - PR-AUC / Average Precision (Mandatory primary metric for imbalanced data)
  - Confusion matrix ($TP, FP, TN, FN$)
- [ ] **Metric Integrity**: Zero fabricated or guessed numbers; all values sourced from actual evaluation runs.

## Phase 5: Threshold Selection & Trade-Off Audit
- [ ] **Non-Default Threshold**: Evaluated candidate thresholds (e.g. 0.05 to 0.95); rejected default 0.5 without evaluation.
- [ ] **Trade-Off Documentation**:
  - Documented precision drop at low thresholds (higher recall, more false positives).
  - Documented recall drop at high thresholds (higher precision, missed fraud).
- [ ] **Business Cost Formulation**:
  - Calculated $\text{Cost} = FN \times C_{FN} + FP \times C_{FP}$.
  - Clearly articulated business risk if $C_{FN}$ and $C_{FP}$ are unprovided.
- [ ] **Artifact Persistence**: Selected threshold serialized to a configuration file or artifact (e.g., `threshold.json`).

## Phase 6: Serving Parity & API Verification
- [ ] **Feature Pipeline Symmetry**:
  - Raw `Time` treated strictly as elapsed seconds (not wall-clock time; do not derive cyclical hour-of-day features without empirical/domain justification).
  - Raw `Amount` transformed identically (e.g., `np.log1p(Amount)` followed by scaler).
  - Scaler loaded from saved training artifact, not refit.
- [ ] **Feature Ordering**: Exact 1-to-1 match between training feature list and model inference array columns.
- [ ] **Request Boundary**:
  - API schema explicitly excludes `Class` from input models.
  - `Time` and `Amount` validated as non-negative floats (HTTP 422 on negative).
- [ ] **Output Contract**:
  - Prediction probability is a finite float in $[0.0, 1.0]$.
  - Verdict matches `probability >= saved_threshold`.
  - Transaction ID and top explanation reasons returned.

## Phase 7: Explainability (SHAP) Verification
- [ ] Explainer initialized with appropriate explainer class (`TreeExplainer` for tree models).
- [ ] Input features passed to explainer match model input features (names and scaled values).
- [ ] Attributions sorted by absolute magnitude ($|\phi_i|$).
- [ ] Interpretation direction validated (positive attribution increases fraud score, negative attribution decreases fraud score).
- [ ] No synthetic or placeholder reasons returned when SHAP computation fails.

## Phase 8: Reporting & Verification
- [ ] End-to-end flow verified: CSV -> Preprocessing -> Training -> Threshold -> Serving -> SHAP.
- [ ] Metric Integrity: All reported metrics are backed by verified execution logs; sample figures in templates are treated strictly as illustrative placeholders.
- [ ] Script Verification: Confirmed all referenced scripts exist in the workspace before execution.
- [ ] Audit report produced with confirmed findings, severity ratings, reproducible commands, and remaining limitations.
