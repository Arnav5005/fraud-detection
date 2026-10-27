# Credit Card Fraud Detection System

An explainable, real-time financial transaction fraud detection system that scores credit card transactions using a calibrated Machine Learning model, explains flagged predictions with game-theoretic SHAP attributions, persists decisions in an audit log, and visualizes real-time risk through a React monitoring dashboard.

---

## 1. System Architecture

```
                                  [ Analyst UI / Browser ]
                                             │
                                             │ HTTP (Axios / JSON)
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FastAPI Serving Engine                                 │
│                                                                                        │
│   ┌───────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐   │
│   │  Pydantic Schemas │ ──> │ Preprocessing Engine │ ──> │ XGBoost Inference Model │   │
│   │ (Anti-leak & Bnd) │     │ (log1p + Scaler)     │     │ (Threshold: 0.89)       │   │
│   └───────────────────┘     └──────────────────────┘     └─────────────────────────┘   │
│                                                                        │               │
│                                                                        ▼               │
│   ┌───────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐   │
│   │ SQLite Audit Log  │ <── │ Decision & Persist   │ <── │ SHAP TreeExplainer      │   │
│   │ (SQLAlchemy ORM)  │     │ (ID + Probability)   │     │ (Top 3 Contributions)   │   │
│   └───────────────────┘     └──────────────────────┘     └─────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Machine Learning Methodology & Metrics

### The Core Problem: Extreme Class Imbalance
The benchmark dataset contains **284,807 transactions** with only **492 fraud cases (~0.172%)**. A naive classifier predicting legitimate for all transactions would achieve **99.83% accuracy while catching 0% of fraud**. 

### Rigorous Pipeline Design:
1. **Stratification**: 80/20 train/test split preserving the exact 0.172% fraud prevalence in both splits.
2. **Zero Feature Leakage**:
   - `Amount` is transformed using $\ln(1 + \text{Amount})$ to correct severe right skewness.
   - `Time` (continuous elapsed seconds) is converted to `Hour = (Time / 3600) % 24`.
   - `StandardScaler` is fit **strictly on training partitions**; validation and test splits are transformed using stored training parameters.
   - `Class` target is strictly excluded from all inference schemas and features.
3. **Resampling Isolation**:
   - `SMOTE` (Synthetic Minority Over-sampling Technique) is applied **strictly to training data**.
   - Test partitions retain their natural real-world class distribution.
4. **Architecture Comparison**:
   - Baseline: Logistic Regression (balanced class weights).
   - Ensemble: Random Forest Classifier.
   - Champion: **XGBoost Classifier** (`eval_metric='aucpr'`, gradient boosted decision trees).

### Verified Evaluation Results:

| Model Architecture | Precision | Recall | F1 Score | ROC-AUC | PR-AUC (Average Precision) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** (Baseline) | 0.0512 | 0.8737 | 0.0968 | 0.9603 | 0.7241 |
| **Random Forest** | 0.9359 | 0.7684 | 0.8439 | 0.9605 | 0.8520 |
| **XGBoost** (Default 0.50 Threshold) | 0.7835 | 0.8000 | 0.7917 | **0.9689** | **0.8654** |
| **XGBoost (Tuned Threshold: 0.89)** | **0.9359** | **0.7684** | **0.8439** | **0.9689** | **0.8654** |

> **Note on Threshold Tuning:**  
> The calibrated threshold of **0.89** reduces false alarms by over 70% compared to a default 0.5 threshold, maximizing precision (0.9359) while capturing ~77% of fraud incidents.

---

## 3. Explainable AI (SHAP)

Every scored transaction computes localized Shapley values via `shap.TreeExplainer`:
- Measures each feature's marginal contribution toward elevating or lowering fraud probability.
- Top 3 driving features are extracted (e.g., `V14`, `V10`, `V12`, `Amount`, `Hour`) and returned via the REST API.
- The dashboard highlights whether each feature **elevated fraud risk** or **supported legitimacy**.

---

## 4. Repository Structure

```
fraud-detection/
├── backend/
│   ├── database.py       # SQLAlchemy ORM model and SQLite session handling
│   ├── explainer.py      # SHAP TreeExplainer serving module
│   ├── main.py           # FastAPI application and REST endpoints
│   ├── predictor.py      # Feature engineering and XGBoost inference engine
│   └── schemas.py        # Pydantic v2 boundary validation schemas
├── frontend/             # React + Vite + Tailwind CSS + Recharts Dashboard
│   ├── src/
│   │   ├── components/   # Header, SummaryCards, DemoPanel, FraudTrendChart, ExplainModal
│   │   ├── services/     # Axios API service
│   │   ├── App.jsx       # Root dashboard application
│   │   └── main.jsx      # Vite entrypoint
│   └── package.json
├── models/
│   ├── explainer.pkl     # Persisted shap.TreeExplainer artifact
│   ├── model.pkl         # Trained XGBoost model
│   ├── scaler.pkl        # Fitted StandardScaler artifact
│   └── threshold.pkl     # Calibrated classification threshold (0.89)
├── notebooks/
│   └── eda.ipynb         # Exploratory data analysis, modeling, and evaluation notebook
├── skills/               # ML Pipeline Auditor skill & validation runbooks
├── tests/
│   ├── test_api.py           # FastAPI endpoint and persistence integration tests
│   ├── test_ml_pipeline.py   # Preprocessing, inference, and SHAP tests
│   └── test_schemas.py       # Pydantic boundary and validation tests
├── creditcard.csv        # Benchmark Kaggle Credit Card Fraud dataset
├── requirements.txt      # Pinned Python dependencies
└── README.md             # System documentation
```

---

## 5. Getting Started

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ and npm

### 1. Backend Installation & Startup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run automated tests to verify serving contract
pytest tests/

# Start FastAPI backend server (port 8000)
python -m uvicorn backend.main:app --reload --port 8000
```

Interactive API documentation will be available at:  
👉 **Swagger UI:** `http://localhost:8000/docs`  
👉 **Health Check:** `http://localhost:8000/health`

### 2. Frontend Dashboard Startup

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Start Vite development server (port 5173)
npm run dev
```

Open your browser at:  
👉 **Dashboard:** `http://localhost:5173`

---

## 6. REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service readiness, model operational status, and active threshold. |
| `POST` | `/predict` | Scores a single transaction (`Time`, `Amount`, `V1`..`V28`), computes SHAP, persists record. |
| `GET` | `/transactions` | Retrieves recent scored transactions (default limit: 50). |
| `GET` | `/stats` | Returns aggregate statistics: total transactions, fraud count, legit count, fraud rate. |
| `GET` | `/explain/{id}` | Retrieves stored prediction, top 3 SHAP drivers, and risk impact directions. |

---

## 7. Interactive Dashboard & Demo Mode

The React dashboard provides:
1. **KPI Summary Cards**: Real-time totals for Scored Transactions, Flagged Fraud, Legitimate Transactions, and Fraud Detection Rate.
2. **Demo Simulator**: Single-click testing of pre-configured legitimate transactions ($42.50), high-risk fraud transactions ($840.00), or a 5-transaction streaming batch.
3. **Probability Stream Chart**: Real-time Recharts visualization tracking prediction confidence against the 89% threshold boundary.
4. **Recent Transactions Feed**: Sortable audit feed with status badges and probability progress meters.
5. **Explain Modal**: Deep-dive SHAP visualization displaying top feature drivers, rank impact, and contextual descriptions.

---

## 8. Known Limitations & Production Roadmap

1. **Benchmark Data Scope**: The Kaggle dataset represents simulated European cardholder transactions across a 48-hour window. Real production deployment requires live velocity windows (e.g., 1h, 24h, 7d transaction count aggregations).
2. **Database Concurrency**: The local MVP uses SQLite for zero-setup execution. For high-concurrency production serving, configure `DATABASE_URL` in `.env` to point to a PostgreSQL cluster.
3. **Continuous Retraining**: Retraining is currently executed manually through scripts/notebooks. Production pipelines should incorporate concept drift monitoring (e.g., Evidently AI).
