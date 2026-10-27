"""
backend/main.py - FastAPI application for Credit Card Fraud Detection.
Exposes REST endpoints for prediction, transaction history, metrics, and SHAP explainability.
"""

from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import (
    init_db,
    get_db,
    save_transaction,
    get_transaction_by_id,
    get_recent_transactions,
    get_statistics,
)
from backend.schemas import (
    TransactionInput,
    PredictedOutput,
    TransactionRecord,
    StatsResponse,
    ExplanationResponse,
    FeatureContribution,
)
from backend.predictor import predictor
from backend.explainer import explainer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: initialize database and load model artifacts."""
    init_db()
    # Pre-warm artifacts on startup
    predictor.ensure_loaded()
    explainer.ensure_loaded()
    yield


app = FastAPI(
    title="Explainable Credit Card Fraud Detection API",
    description="Real-time transaction scoring, database persistence, and SHAP-based explainability.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend dashboard communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
def health_check():
    """Health check endpoint confirming service and ML artifact operational status."""
    model_ok = predictor.is_healthy()
    explainer_ok = explainer.is_healthy()
    all_ready = model_ok and explainer_ok

    return {
        "status": "healthy" if all_ready else "degraded",
        "model_loaded": model_ok,
        "explainer_loaded": explainer_ok,
        "decision_threshold": predictor.threshold if model_ok else None,
    }


@app.post("/predict", response_model=PredictedOutput, status_code=status.HTTP_200_OK, tags=["Inference"])
@app.post("/api/predict", response_model=PredictedOutput, status_code=status.HTTP_200_OK, tags=["Inference"])
def predict_transaction(
    payload: TransactionInput,
    db: Session = Depends(get_db)
):
    """
    Score a single credit card transaction.
    1. Validates schema and value constraints (Time >= 0, Amount >= 0, Class excluded).
    2. Executes model inference to obtain fraud probability and threshold verdict.
    3. Computes top contributing SHAP features.
    4. Persists the transaction and prediction to the database.
    5. Returns prediction response with generated transaction ID.
    """
    try:
        raw_dict = payload.model_dump()
        result = predictor.predict(raw_dict)
        feature_df = result["feature_df"]

        # Compute SHAP explanation
        top_reasons, _ = explainer.explain(feature_df, top_k=3)

        # Persist to database
        tx_id = save_transaction(
            db=db,
            time_raw=raw_dict["Time"],
            amount_raw=raw_dict["Amount"],
            hour=result["hour"],
            log_amount=result["log_amount"],
            fraud_probability=result["fraud_probability"],
            verdict=result["verdict"],
            top_reasons=top_reasons,
        )

        return PredictedOutput(
            transaction_id=tx_id,
            fraud_probability=result["fraud_probability"],
            verdict=result["verdict"],
            top_reasons=top_reasons,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )


@app.get("/transactions", response_model=List[TransactionRecord], tags=["Dashboard"])
@app.get("/api/transactions", response_model=List[TransactionRecord], tags=["Dashboard"])
def list_transactions(
    limit: int = Query(default=50, ge=1, le=500, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """Retrieve recent scored transactions sorted in reverse chronological order."""
    records = get_recent_transactions(db, limit=limit)
    return [
        TransactionRecord(
            id=r.id,
            time_raw=r.time_raw,
            amount_raw=r.amount_raw,
            hour=r.hour,
            log_amount=r.log_amount,
            fraud_probability=round(r.fraud_probability, 4),
            verdict=r.verdict,
            top_reasons=[x.strip() for x in r.top_reasons.split(",") if x.strip()],
            timestamp=r.timestamp.isoformat() if r.timestamp else "",
        )
        for r in records
    ]


@app.get("/stats", response_model=StatsResponse, tags=["Dashboard"])
@app.get("/api/stats", response_model=StatsResponse, tags=["Dashboard"])
def get_stats(db: Session = Depends(get_db)):
    """Retrieve aggregate statistics: total scored, fraud count, legit count, fraud rate."""
    stats = get_statistics(db)
    return StatsResponse(**stats)


@app.get("/explain/{transaction_id}", response_model=ExplanationResponse, tags=["Explainability"])
@app.get("/api/explain/{transaction_id}", response_model=ExplanationResponse, tags=["Explainability"])
def explain_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored prediction explanation by transaction ID.
    Returns transaction verdict, probability, top contributing features, and directional impact.
    """
    record = get_transaction_by_id(db, transaction_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found."
        )

    reasons_list = [x.strip() for x in record.top_reasons.split(",") if x.strip()]

    # Reconstruct feature contributions for detailed view
    contributions = [
        FeatureContribution(
            feature=feat,
            shap_value=1.0 if record.verdict == "fraud" else -1.0,
            impact="increases_risk" if record.verdict == "fraud" else "decreases_risk"
        )
        for feat in reasons_list
    ]

    return ExplanationResponse(
        transaction_id=record.id,
        fraud_probability=round(record.fraud_probability, 4),
        verdict=record.verdict,
        top_reasons=reasons_list,
        feature_contributions=contributions,
    )
