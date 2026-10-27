"""
backend/predictor.py - Preprocessing and model inference engine.
Ensures serving parity with training pipeline:
- Derives Hour = (Time / 3600) % 24
- Applies log1p to Amount
- Applies saved StandardScaler to [Amount, Hour]
- Orders features exactly as expected by model: V1..V28, Amount, Hour
- Applies serialized decision threshold to evaluate verdict
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

MODEL_PATH = MODELS_DIR / "model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
THRESHOLD_PATH = MODELS_DIR / "threshold.pkl"

# Feature order expected by the trained XGBoost model
FEATURE_COLUMNS = [
    "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
    "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20",
    "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28",
    "Amount", "Hour"
]


class FraudPredictor:
    """Manages model loading, feature transformation, and inference."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.threshold = 0.5
        self._loaded = False

    def load_artifacts(self):
        """Load trained model, scaler, and tuned threshold from disk."""
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH}")
        if not SCALER_PATH.exists():
            raise FileNotFoundError(f"Scaler artifact not found at {SCALER_PATH}")
        if not THRESHOLD_PATH.exists():
            raise FileNotFoundError(f"Threshold artifact not found at {THRESHOLD_PATH}")

        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        raw_threshold = joblib.load(THRESHOLD_PATH)
        self.threshold = float(raw_threshold)
        self._loaded = True

    def ensure_loaded(self):
        """Lazy load artifacts if not already loaded."""
        if not self._loaded:
            self.load_artifacts()

    def preprocess(self, payload: Dict[str, float]) -> Tuple[pd.DataFrame, float, float]:
        """
        Transform raw input dictionary into model-ready DataFrame.
        Returns:
            (feature_df, hour, log_amount)
        """
        raw_time = float(payload["Time"])
        raw_amount = float(payload["Amount"])

        hour = (raw_time / 3600.0) % 24.0
        log_amount = float(np.log1p(raw_amount))

        # Scale Amount and Hour using saved scaler
        scaled_features = self.scaler.transform(pd.DataFrame([[log_amount, hour]], columns=["Amount", "Hour"]))
        scaled_amount = float(scaled_features[0][0])
        scaled_hour = float(scaled_features[0][1])

        # Assemble feature row in exact column ordering
        row = {}
        for i in range(1, 29):
            col = f"V{i}"
            row[col] = float(payload[col])
        row["Amount"] = scaled_amount
        row["Hour"] = scaled_hour

        feature_df = pd.DataFrame([row], columns=FEATURE_COLUMNS)
        return feature_df, hour, log_amount

    def predict(self, payload: Dict[str, float]) -> Dict[str, Any]:
        """
        Execute prediction pipeline for one transaction payload.
        Returns prediction probability, verdict, threshold, and preprocessed DataFrame.
        """
        self.ensure_loaded()
        feature_df, hour, log_amount = self.preprocess(payload)

        # Compute probability for positive class (Class=1, Fraud)
        proba = float(self.model.predict_proba(feature_df)[0, 1])
        verdict = "fraud" if proba >= self.threshold else "legitimate"

        return {
            "fraud_probability": round(proba, 4),
            "verdict": verdict,
            "threshold": self.threshold,
            "hour": round(hour, 4),
            "log_amount": round(log_amount, 4),
            "feature_df": feature_df
        }

    def is_healthy(self) -> bool:
        """Readiness check confirming model and artifacts are operational."""
        try:
            self.ensure_loaded()
            return self.model is not None and self.scaler is not None
        except Exception:
            return False


# Singleton predictor instance for application-wide reuse
predictor = FraudPredictor()
