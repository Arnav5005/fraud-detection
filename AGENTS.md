# Agent Instructions — Credit Card Fraud Detection

## Project objective

Build a clean, understandable, end-to-end credit card fraud detection MVP from an empty project directory.

The product requirements are defined in `PRD.md`. Read it before implementation.

The project includes data exploration, ML training and evaluation, FastAPI, SQLite, SHAP explainability, and a React dashboard.

The primary ML objective is to reduce false negatives while maintaining a reasonable false-positive rate.

## 1. Working principles

- Inspect the current directory before creating files.
- Read `PRD.md` before implementation.
- Make a concise implementation plan, then execute it.
- Build the smallest correct implementation that satisfies the requirements.
- Prefer readable, conventional Python and JavaScript.
- Avoid unnecessary abstractions, dependencies, infrastructure, and boilerplate.
- Do not create placeholder functionality that appears complete but does not work.
- Do not fabricate metrics, predictions, explanations, or test results.
- Ask before performing paid operations or destructive actions.

## 2. Three-layer architecture

Use the three-layer approach only where it improves reliability.

### Directives

Use `directives/` for genuinely reusable procedures that need to be maintained independently.

Do not create directives merely to document every coding task.

Do not create or overwrite directives without authorization unless explicitly instructed.

### Orchestration

The agent is responsible for reading requirements, choosing the appropriate workflow, coordinating implementation, investigating failures, and verifying outcomes.

Use existing instructions and tools where available.

Do not build a custom agent framework or task orchestration engine for this project.

### Execution

Use ordinary Python modules and scripts for repeatable operations such as:

- Dataset validation.
- Feature preprocessing.
- Model training.
- Threshold evaluation.
- Artifact generation.
- Automated testing.

Keep the scripts deterministic where practical. Fix random seeds, validate inputs, and record important outputs.

Create a new script only when it provides a useful, distinct responsibility.

## 3. Mandatory ML correctness rules

- Use the Kaggle credit card fraud dataset.
- Treat `Class` as the target, never as an inference feature.
- Use stratified training, validation, and test partitions.
- Fit preprocessing only on training data.
- Apply SMOTE only to training data.
- Keep validation and test distributions untouched.
- Tune thresholds using validation data only.
- Do not use the final test set to select models or thresholds.
- Compare Logistic Regression, Random Forest, and XGBoost.
- Evaluate precision, recall, F1, F0.5, ROC-AUC, Average Precision, confusion matrices, false positives, and false negatives.
- Prioritize missed-fraud reduction while measuring false-positive costs.
- Save the selected model, preprocessing configuration, feature order, and threshold.
- Ensure training and inference use identical transformations.
- Never invent model results or claim that an unexecuted test passed.

Use the `fraud-ml-pipeline-auditor` skill when available and relevant.

## 4. Implementation standards

Write straightforward, maintainable code.

- Use descriptive names and focused functions.
- Add comments only where they explain meaningful reasoning.
- Use type hints where they improve clarity.
- Handle errors at appropriate boundaries.
- Remove unused code and dependencies.
- Keep the frontend simple and professional.
- Avoid unnecessary microservices, Redis, Kafka, Kubernetes, Celery, or distributed infrastructure.
- Do not add features outside the PRD without a clear reason.

## 5. Self-annealing

When something fails:

1. Read the error and relevant stack trace.
2. Identify the root cause.
3. Make the smallest justified fix.
4. Rerun the failing operation.
5. Run relevant regression tests.
6. Update reusable instructions only when authorized.

Do not apply repeated speculative fixes without checking the evidence.

## 6. Data and artifacts

Keep the dataset, model artifacts, and generated evaluation results organized.

Exclude credentials, `.env` files, virtual environments, caches, and other local secrets from version control.

Do not commit Kaggle credentials.

Do not overwrite valuable outputs without checking whether they are needed.

## 7. Verification

Verify the complete workflow:

Dataset → preprocessing → training → threshold selection → model inference → SHAP → database → API → React dashboard.

Run relevant tests and record actual outcomes.

Clearly identify anything that could not be tested because of missing credentials, dependencies, or services.

## 8. Completion report

At the end, summarize:

- What was implemented.
- Important engineering decisions.
- Commands required to run the project.
- Tests actually executed and their results.
- Remaining limitations.

The goal is a correct, understandable local MVP that can be maintained and explained by its developer.
