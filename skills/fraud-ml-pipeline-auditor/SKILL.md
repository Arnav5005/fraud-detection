---
name: fraud-ml-pipeline-auditor
description: Inspect, audit, debug, and validate imbalanced binary classification pipelines for credit card fraud detection. Use when implementing or modifying preprocessing, performing EDA, splitting data or applying SMOTE, training or comparing Logistic Regression, Random Forest, or XGBoost, tuning decision thresholds, investigating false negatives and false positives, evaluating precision/recall/F1/ROC-AUC/PR-AUC, saving or loading model artifacts, or checking consistency between training and API inference. Do not use for unrelated frontend styling or routine documentation changes.
---

# Fraud ML Pipeline Auditor

A specialized operational runbook for implementing, inspecting, debugging, and validating imbalanced binary classification pipelines for credit card fraud detection.

## Core Operational Principles

1. **Inspect Before Modifying**: Read existing scripts, preprocessing modules, notebooks, and serialized artifacts before proposing or executing changes. Reuse working implementations; do not rewrite code without empirical evidence of a defect.
2. **Never Fabricate Metrics**: Never invent evaluation numbers, assert unverified test passes, or report template examples as actual findings. All reported metrics must originate from verified execution.
3. **Verify Script Paths**: Never assume bundled scripts or workspace files exist without checking the actual directory structure first (e.g., using `Test-Path` or file inspection).
4. **Zero Data Leakage**: Transformations, scalers, and SMOTE must only be fitted on training partitions. Validation and test partitions must retain their natural class distribution.
5. **Kaggle Time Semantics**: Treat `Time` as continuous elapsed seconds from the start of recording, NOT wall-clock time. Do NOT derive cyclical hour-of-day features via modulo arithmetic without an empirical and defensible domain anchor.
6. **Fraud-First Optimization**: Prioritize missed-fraud reduction (False Negatives) while explicitly quantifying the business operational cost of false alarms (False Positives).
7. **Strict Serving Parity**: Training transformations, feature column ordering, and decision thresholds must match inference behavior exactly.

---

## When to Activate This Skill

Activate this skill immediately when performing or reviewing any of the following tasks:
- **Data Exploration & Validation**: Validating `creditcard.csv`, analyzing class imbalance (~0.17%), checking data cleanliness and column semantics.
- **Preprocessing & Feature Engineering**: Transforming `Amount` (e.g., `log1p`), handling elapsed `Time` (strictly as elapsed seconds, avoiding unfounded hour-of-day derivations), and scaling numeric features.
- **Partitioning & Resampling**: Splitting train/validation/test sets, verifying stratification, applying SMOTE.
- **Model Training & Comparison**: Running or comparing Logistic Regression, Random Forest, and XGBoost.
- **Threshold Tuning**: Evaluating decision boundaries, precision-recall trade-offs, and false negative/positive counts on validation data.
- **Artifact Management**: Serializing, versioning, or loading models, scalers, thresholds, and SHAP explainers.
- **Inference Verification**: Auditing FastAPI endpoints, Pydantic input schemas (rejecting `Class`), and SHAP reasoning against training transformations.

**Do NOT activate** for unrelated frontend styling, routine documentation edits, or general environment setup.

---

## 8-Step Pipeline Audit Workflow

```
[1. Inspect] ──> [2. Validate Dataset] ──> [3. Audit Leakage] ──> [4. Compare Models]
                                                                          │
[8. Report]  <── [7. Verify SHAP]     <── [6. Serving Parity] <── [5. Audit Threshold]
```

### Step 1: Inspect Before Modifying
Before editing any code or configuration:
1. Check the actual directory tree and verify existing training scripts, preprocessing modules, notebooks, and serialized artifacts.
2. Record existing hyperparameters, random seeds, and saved metric outputs.
3. Formulate minimal, surgical corrections only when a defect is verified with concrete evidence.

### Step 2: Validate the Dataset
For the Kaggle credit card fraud dataset (`creditcard.csv`):
1. **Schema Check**: Confirm 31 columns (`Time`, `V1` through `V28`, `Amount`, `Class`).
2. **Column Semantics**:
   - `Time`: Elapsed seconds from the first recorded transaction (spans ~172,792 seconds / 48 hours). Treat strictly as continuous elapsed time; do not assume wall-clock hour without a proven reference.
   - `Class`: Binary target `{0, 1}`. Positive class `1` must explicitly designate **Fraud**.
3. **Class Imbalance**: Calculate exact fraud prevalence (benchmark is ~492 fraud cases out of 284,807 transactions, ~0.172%).
4. **Cleanliness**: Check for nulls, infinities, duplicate rows, and confirm `Time >= 0` and `Amount >= 0`.
5. **Execution**: Verify that the dataset auditor script exists, then run:
   ```bash
   # Verify script exists first:
   python .agents/skills/fraud-ml-pipeline-auditor/scripts/audit_dataset.py --data-path creditcard.csv
   ```

### Step 3: Audit Data Leakage and Partitions
Verify strict separation across all stages. (See [Leakage and Splitting Guide](./references/leakage_and_splitting_guide.md)):
1. **Splitting Order**: Stratified split performed *before* any feature transformations or resampling.
2. **Preprocessing Fit Scope**: Scalers and transformers must be fitted strictly on the training partition (`X_train`). Only `transform()` may be called on validation and test sets.
3. **Resampling Isolation**: SMOTE/ADASYN must be applied **only to the training split**. Validation and test partitions must remain completely un-resampled.
4. **Evaluation Isolation**: Decision thresholds must be tuned strictly on the validation partition. The final test set must remain untouched until the release gate.
5. **Execution**: Verify script presence, then scan codebase for leakage:
   ```bash
   python .agents/skills/fraud-ml-pipeline-auditor/scripts/audit_leakage.py .
   ```

### Step 4: Compare Models Correctly
Compare the three mandatory architectures: **Logistic Regression**, **Random Forest**, and **XGBoost**.
1. **Metric Evaluation**: Evaluate each candidate using:
   - **Precision**: $\frac{TP}{TP + FP}$
   - **Recall**: $\frac{TP}{TP + FN}$
   - **F1 Score**: Harmonic balance of precision and recall
   - **F0.5 Score**: Weights precision twice as heavily as recall ($\beta = 0.5$)
   - **ROC-AUC**: Discrimination across all thresholds
   - **PR-AUC / Average Precision**: Primary ranking metric under extreme imbalance (~0.17% fraud)
   - **Confusion Matrix**: Explicit counts of $TP$, $FP$, $TN$, $FN$.
2. **Target Convention**: Explicitly set `pos_label=1` (Fraud) for all metric computations.
3. **Reproducibility**: Enforce fixed random seeds across all models and splitters.

### Step 5: Audit Threshold Selection
Never assume a default threshold of `0.5` is optimal under extreme class imbalance.
1. **Validation Sweep**: Sweep probability thresholds from `0.05` to `0.95` strictly on validation predictions.
2. **Trade-Off Analysis**:
   - Quantify how lowering the threshold increases Recall (fewer missed frauds) at the cost of higher False Positives (analyst review overhead).
   - Quantify operational cost: $\text{Cost} = (FN \times C_{FN}) + (FP \times C_{FP})$.
3. **Business Limitation**: If acceptable false-positive budget or $C_{FN}/C_{FP}$ costs are not formally defined, document this trade-off explicitly.
4. **Execution**: Verify script presence, then run:
   ```bash
   python .agents/skills/fraud-ml-pipeline-auditor/scripts/evaluate_thresholds.py --val-preds path/to/val_predictions.csv
   ```
   (See [Metrics and Trade-Offs Reference](./references/metrics_and_tradeoffs.md)).

### Step 6: Verify Inference Consistency and Serving Contract
Ensure complete parity between training pipeline and serving API:
1. **Artifact Alignment**: Confirm API loads the selected model, fitted scaler, saved threshold, and exact feature order.
2. **Feature Preprocessing & Ordering**:
   - Feature columns must be passed to the model in the **exact order** used during training.
   - Transformations (e.g., `log1p(Amount)`, elapsed `Time` scaling) must match training transformations identically.
3. **API Boundary Validation**:
   - Request schema must exclude `Class`. `Class` must never be accepted as an inference input.
   - Verify `Time >= 0` and `Amount >= 0` validations reject invalid input with HTTP 422.
   - Prediction probabilities must be finite and within `[0.0, 1.0]`.
   - Verdict (`fraud` vs `legitimate`) must match `probability >= saved_threshold`.
4. **Execution**: Verify script presence, then test inference contract:
   ```bash
   python .agents/skills/fraud-ml-pipeline-auditor/scripts/verify_inference_contract.py
   ```
   (See [Serving Consistency Checklist](./references/serving_consistency_checklist.md)).

### Step 7: Verify Explainability (SHAP)
1. **Explainer Compatibility**: Explainer class must match the model architecture (e.g., `shap.TreeExplainer` for XGBoost / Random Forest).
2. **Feature Representation**: Explanations must be computed on the transformed inference array using exact feature names shown to analysts.
3. **Attribution Ordering**: Top reasons must be ordered by contribution magnitude ($|\phi_i|$) and correctly indicate risk direction.
4. **Zero Fallbacks / Fabrication**: Never return hardcoded or random explanations. Raise a descriptive exception if SHAP computation fails.

### Step 8: Test Execution and Audit Reporting
After any pipeline modification or audit, run focused tests and produce a structured audit report.

---

## Audit Report Format

When delivering an audit report, use the following template. **All metric figures, counts, and thresholds inside brackets or labeled as placeholders are purely illustrative examples; replace them with actual verified test results.**

```markdown
# ML Pipeline Audit Report: [Component / Stage Name]

## 1. Executive Summary
- Overall Pipeline Status: [PASS / WARN / FAIL]
- Key Risk Identified: [Brief summary of verified risk or none]
- Primary Recommendation: [Immediate action needed based on evidence]

## 2. Findings & Defect Severity
| ID | Category | Finding Description | Severity (Critical/High/Med/Low) | Status |
|----|----------|---------------------|----------------------------------|--------|
| F1 | [Category] | [Description based on inspected code/data] | [Severity] | [Confirmed/Risk] |

## 3. Evidence & Root Cause Analysis
- **Finding F1**: [Exact file, line number, and code snippet demonstrating the defect]

## 4. Minimal Recommended Corrections
Provide exact code diffs:
\`\`\`python
# Minimal surgical fix
- [Faulty line]
+ [Corrected line]
\`\`\`

## 5. Verification Tests & Results
- Unit/Pipeline Tests Executed: [Exact command executed in workspace]
- Test Outcomes: [Passed / Failed count, actual test output summary]
- Actual Measured Metrics (Record real execution outputs only; do NOT copy placeholders):
  - Recall: [e.g. 0.84 - ILLUSTRATIVE PLACEHOLDER ONLY; replace with actual measured value]
  - Precision: [e.g. 0.81 - ILLUSTRATIVE PLACEHOLDER ONLY; replace with actual measured value]
  - F1: [e.g. 0.82 - ILLUSTRATIVE PLACEHOLDER ONLY; replace with actual measured value]
  - F0.5: [e.g. 0.81 - ILLUSTRATIVE PLACEHOLDER ONLY; replace with actual measured value]
  - PR-AUC: [e.g. 0.85 - ILLUSTRATIVE PLACEHOLDER ONLY; replace with actual measured value]
  - ROC-AUC: [e.g. 0.98 - ILLUSTRATIVE PLACEHOLDER ONLY; replace with actual measured value]
  - Selected Threshold: [e.g. 0.35 - ILLUSTRATIVE PLACEHOLDER ONLY; replace with validation-tuned threshold]

> [!CAUTION]
> The numbers above are strictly illustrative placeholders for format guidance. Never report them as actual results without real execution evidence.

## 6. Remaining Operational Risks & Limitations
- [Document unmitigated risks, unstated business cost budgets, or deployment dependencies]
```

---

## Verified Bundled Resources

Verify existence in `.agents/skills/fraud-ml-pipeline-auditor/` (or `skills/fraud-ml-pipeline-auditor/`) before execution:

- [Audit Checklist & Defect Catalog](./references/audit_checklist.md)
- [Leakage & Splitting Guide](./references/leakage_and_splitting_guide.md)
- [Metrics & Trade-Offs Reference](./references/metrics_and_tradeoffs.md)
- [Serving Consistency Checklist](./references/serving_consistency_checklist.md)
- [Dataset Auditor Script](./scripts/audit_dataset.py)
- [Leakage Checker Script](./scripts/audit_leakage.py)
- [Threshold Evaluator Script](./scripts/evaluate_thresholds.py)
- [Inference Contract Checker](./scripts/verify_inference_contract.py)
