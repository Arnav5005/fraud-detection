# Fraud Detection Mini System — Project Blueprint

## Project Summary

A real-time financial transaction fraud detection system that ingests transaction data, scores it using a trained ML model, serves predictions via a REST API, and visualises results on a live dashboard. Covers the full ML system lifecycle: data → features → model → serving → monitoring.

---

## Tech Stack

### Frontend
- **React.js** — Dashboard UI
- **TailwindCSS** — Styling
- **Recharts** — Transaction charts, fraud rate graphs
- **Axios** — API calls from the frontend

### Backend
- **FastAPI (Python)** — REST API server for model serving
- **Uvicorn** — ASGI server to run FastAPI
- **Pydantic** — Request/response validation

### ML & Data
- **scikit-learn** — Model training (XGBoost, Random Forest, Logistic Regression)
- **imbalanced-learn (imblearn)** — Handle class imbalance via SMOTE
- **pandas** — Data manipulation and feature engineering
- **numpy** — Numerical operations
- **shap** — Model explainability (why was a transaction flagged?)
- **joblib** — Save and load trained models

### Database
- **SQLite** (development) / **PostgreSQL** (production-ready) — Store transactions and predictions
- **SQLAlchemy** — ORM for database interaction

### Dev Tools
- **Jupyter Notebook** — Exploratory data analysis and model training
- **Postman** — API testing
- **Git + GitHub** — Version control

---

## Free APIs & Datasets

| Resource | Purpose | Link |
|---|---|---|
| **Kaggle Credit Card Fraud Dataset** | Primary training dataset (284K transactions, 492 frauds) | kaggle.com/datasets/mlg-ulb/creditcardfraud |
| **Faker (Python library)** | Generate synthetic transaction data for testing | `pip install faker` |
| **Open Exchange Rates (free tier)** | Currency conversion for multi-currency transactions | openexchangerates.org |
| **Kaggle API** | Download datasets programmatically | `pip install kaggle` |

> No paid API is required. The Kaggle dataset is the industry-standard benchmark for fraud detection.

---

## System Design

```
[React Dashboard]
       |
       | HTTP (Axios)
       v
[FastAPI Server]  <-- /predict, /transactions, /stats endpoints
       |
   [Pydantic]  — validates incoming transaction JSON
       |
   [Feature Engineering Module]  — computes velocity, time features, etc.
       |
   [Trained ML Model (joblib)]  — returns fraud probability score
       |
   [SQLAlchemy ORM]
       |
   [SQLite / PostgreSQL]  — stores transaction + prediction log
       |
   [SHAP Explainer]  — returns top features that caused the flag
```

### Key Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/predict` | POST | Score a single transaction |
| `/transactions` | GET | List recent transactions with fraud scores |
| `/stats` | GET | Fraud rate, model confidence distribution |
| `/explain/{id}` | GET | SHAP explanation for a specific prediction |

---

## Roadmap (Sequential — 6 Weeks)

### Week 1 — Data & Exploration
- [ ] Download Kaggle Credit Card Fraud dataset
- [ ] Open Jupyter Notebook, load data with pandas
- [ ] Explore class imbalance (fraud is ~0.17% of data — this is the core problem)
- [ ] Visualise distributions: transaction amount, time, PCA features
- [ ] Learn: what is precision vs recall? Why accuracy is useless for imbalanced data?

**Deliverable:** EDA notebook with 5–7 visualisations and a written summary of findings.

---

### Week 2 — Feature Engineering
- [ ] Understand existing features (V1–V28 are PCA-transformed, Amount and Time are raw)
- [ ] Normalise `Amount` and `Time` using `StandardScaler`
- [ ] Create new features: `hour_of_day`, `log_amount`, `amount_zscore`
- [ ] Apply SMOTE using `imblearn` to balance the training set
- [ ] Split data: 80% train, 20% test (stratified split)

**Deliverable:** A clean `features.py` module with reusable preprocessing functions.

---

### Week 3 — Model Training
- [ ] Train Logistic Regression first (you already know this — use as baseline)
- [ ] Train Random Forest (`RandomForestClassifier`) — learn how it works while training
- [ ] Train XGBoost (`XGBClassifier`) — most powerful for tabular fraud data
- [ ] Evaluate with: Precision, Recall, F1-Score, ROC-AUC, Confusion Matrix
- [ ] Compare all 3 models in a results table
- [ ] Save the best model using `joblib.dump(model, 'model.pkl')`

**Deliverable:** `train.py` script + `model_comparison.csv` results table.

---

### Week 4 — Backend API
- [ ] Set up FastAPI project structure
- [ ] Create `/predict` endpoint: accepts transaction JSON, loads model, returns score
- [ ] Add Pydantic schemas for input validation
- [ ] Set up SQLite + SQLAlchemy: log every prediction to DB
- [ ] Create `/transactions` and `/stats` endpoints
- [ ] Add SHAP explainability: return top 3 features that drove the prediction
- [ ] Test all endpoints with Postman

**Deliverable:** Working FastAPI server that scores transactions and stores results.

---

### Week 5 — Frontend Dashboard
- [ ] Bootstrap React app with Vite
- [ ] Build Transaction Feed: table of recent transactions with fraud probability badge
- [ ] Build Stats Cards: total transactions, fraud count, avg confidence
- [ ] Build Fraud Rate Chart using Recharts (line chart over time)
- [ ] Build Explain Modal: when user clicks a flagged transaction, show SHAP values
- [ ] Connect all components to FastAPI via Axios

**Deliverable:** Fully functional React dashboard connected to the live API.

---

### Week 6 — Polish & Portfolio Prep
- [ ] Add a "Live Demo" mode: button that fires 10 random test transactions through the system
- [ ] Write README with architecture diagram, setup instructions, and results
- [ ] Record a 2-minute demo video showing the system end-to-end
- [ ] Deploy backend on Render.com (free tier) and frontend on Vercel (free tier)
- [ ] Push to GitHub with clean commit history

**Deliverable:** Deployed, live project with GitHub link and demo video.

---

## ML Learning Path (Parallel to Building)

Since you're learning ML while building, follow this reading order alongside the roadmap:

| Week | Learn This |
|---|---|
| 1 | Confusion matrix, Precision, Recall, F1-Score — why accuracy fails on imbalanced data |
| 2 | What is SMOTE? Overfitting vs underfitting, train/test split |
| 3 | Decision Trees → Random Forests (bagging). Then XGBoost (boosting). ROC-AUC intuition |
| 4 | How to serve ML models as APIs. Stateless prediction endpoints |
| 5–6 | SHAP values: what is feature importance and how to explain model decisions |

**Best free resource:** StatQuest with Josh Starmer on YouTube — covers all of the above with clear visuals.

---

## Folder Structure

```
fraud-detection/
├── data/
│   └── creditcard.csv
├── notebooks/
│   └── eda.ipynb
├── ml/
│   ├── features.py
│   ├── train.py
│   └── model.pkl
├── backend/
│   ├── main.py          # FastAPI app
│   ├── schemas.py       # Pydantic models
│   ├── database.py      # SQLAlchemy setup
│   └── explainer.py     # SHAP integration
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── App.jsx
│   └── package.json
├── README.md
└── requirements.txt
```

---

## What to Highlight to Interviewers

1. **Handled class imbalance** — SMOTE + precision-recall tradeoff (most candidates miss this)
2. **Model comparison** — you evaluated 3 models and chose the best one with justification
3. **Production-ready serving** — FastAPI with Pydantic validation, not just a Jupyter notebook
4. **Explainability** — SHAP values show you understand ML beyond accuracy scores
5. **Full-stack** — end-to-end from raw CSV to live dashboard
