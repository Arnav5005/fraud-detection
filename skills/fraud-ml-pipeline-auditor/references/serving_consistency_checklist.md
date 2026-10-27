# Serving Consistency & Inference Contract Checklist

Training-serving skew occurs when the inference pipeline applies transformations or orders features differently from the training pipeline. This guide provides strict verification rules.

---

## 1. Feature Representation Contract

The raw dataset contains 30 input features + 1 label:
`Time`, `V1`..`V28`, `Amount`, `Class`.

### Preprocessing & Semantics:
1. **Time Representation**:
   - `Time` records the **elapsed seconds** from the initial transaction in the dataset (~172,792 seconds across ~48 hours).
   - It is continuous elapsed time, **not wall-clock time**.
   - **Do NOT derive cyclical hour-of-day features (e.g., modulo 24)** without an empirical, defensible basis or timezone anchor.
   - Treat `Time` as continuous elapsed seconds (scaled via the fitted training scaler if used as a model feature).
2. **Amount Transformation**:
   $$\text{Amount\_log} = \ln(1 + \text{Amount})$$
3. **Feature Scaling**:
   Standardize `Amount_log` (and `Time` if modeled) using the saved scaler parameters ($\mu, \sigma$) learned during training:
   $$z = \frac{x - \mu}{\sigma}$$
   *Never refit the scaler on inference payloads.*

### Feature Order Verification:
The feature columns passed to `model.predict_proba()` must follow the exact order used during `model.fit()`:
```python
# Standard Inference Feature Ordering (30 features):
EXPECTED_FEATURES = [
    "Time_scaled", # Or "Time" depending on the pipeline configuration
    "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
    "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20",
    "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28",
    "Amount_scaled"
]
```

---

## 2. API Input Schema Rules

The FastAPI Pydantic schema must enforce:
1. **Exclusion of `Class`**:
   The input schema must not include `Class`. If an incoming payload contains `Class`, the API must reject it or strip it.
2. **Range Validation**:
   - `Time >= 0`: Non-negative float.
   - `Amount >= 0`: Non-negative float.
   - Rejections must return HTTP 422 Unprocessable Entity.

```python
from pydantic import BaseModel, Field

class TransactionRequest(BaseModel):
    Time: float = Field(..., ge=0.0, description="Seconds elapsed since first transaction")
    Amount: float = Field(..., ge=0.0, description="Transaction amount in currency units")
    V1: float
    V2: float
    # ... V3 to V27
    V28: float

    # Note: Class is STRICTLY EXCLUDED
```

---

## 3. Output Contract & Verdict Mapping

1. **Probability**:
   - Must be computed via `model.predict_proba(X)[0, 1]`.
   - Must be a finite float in $[0.0, 1.0]$.
2. **Verdict**:
   - Must be computed against the serialized threshold, e.g.:
   ```python
   verdict = "fraud" if probability >= saved_threshold else "legitimate"
   ```
   - Must never hardcode `0.5`.
3. **Reasons / Explanations**:
   - Derived from `shap.TreeExplainer(model)` (or model-compatible explainer).
   - Output up to 3 leading feature names ordered by magnitude of positive contribution toward fraud.
   - If SHAP fails or artifacts are unavailable, return a clean error; never fabricate reasons.

---

## 4. Serving Verification Script

Verify that the script exists before running:
```bash
python .agents/skills/fraud-ml-pipeline-auditor/scripts/verify_inference_contract.py \
    --model-path models/xgboost_model.joblib \
    --scaler-path models/scaler.joblib \
    --threshold-path models/threshold.json
```
