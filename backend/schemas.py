"""
backend/schemas.py - Pydantic models for API request and response validation.
Enforces non-negative Time and Amount, complete V1-V28 features, and exclusion of Class.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TransactionInput(BaseModel):
    """
    Inference input schema.
    Requires Time, V1 through V28, and Amount.
    Explicitly forbids Class to prevent target leakage at the API boundary.
    """
    model_config = ConfigDict(extra="forbid")

    Time: float = Field(..., description="Elapsed seconds from the first recorded transaction")
    V1: float = Field(...)
    V2: float = Field(...)
    V3: float = Field(...)
    V4: float = Field(...)
    V5: float = Field(...)
    V6: float = Field(...)
    V7: float = Field(...)
    V8: float = Field(...)
    V9: float = Field(...)
    V10: float = Field(...)
    V11: float = Field(...)
    V12: float = Field(...)
    V13: float = Field(...)
    V14: float = Field(...)
    V15: float = Field(...)
    V16: float = Field(...)
    V17: float = Field(...)
    V18: float = Field(...)
    V19: float = Field(...)
    V20: float = Field(...)
    V21: float = Field(...)
    V22: float = Field(...)
    V23: float = Field(...)
    V24: float = Field(...)
    V25: float = Field(...)
    V26: float = Field(...)
    V27: float = Field(...)
    V28: float = Field(...)
    Amount: float = Field(..., description="Transaction amount in currency units")

    @field_validator("Time")
    @classmethod
    def validate_time(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Time must be non-negative (>= 0)")
        return v

    @field_validator("Amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Amount must be non-negative (>= 0)")
        return v


class PredictedOutput(BaseModel):
    """Prediction endpoint response schema matching PRD Section 6.2."""
    transaction_id: int
    fraud_probability: float
    verdict: str
    top_reasons: List[str]


# Alias for naming consistency
PredictionResponse = PredictedOutput


class TransactionRecord(BaseModel):
    """Persisted transaction representation returned by /transactions."""
    id: int
    time_raw: float
    amount_raw: float
    hour: float
    log_amount: float
    fraud_probability: float
    verdict: str
    top_reasons: List[str]
    timestamp: str


class StatsResponse(BaseModel):
    """Aggregate statistics returned by /stats."""
    total_transactions: int
    fraud_count: int
    legit_count: int
    fraud_rate: float


class FeatureContribution(BaseModel):
    """Feature-level SHAP explanation item."""
    feature: str
    shap_value: float
    impact: str  # "increases_risk" or "decreases_risk"


class ExplanationResponse(BaseModel):
    """Detailed explanation response returned by /explain/{id}."""
    transaction_id: int
    fraud_probability: float
    verdict: str
    top_reasons: List[str]
    feature_contributions: Optional[List[FeatureContribution]] = None
