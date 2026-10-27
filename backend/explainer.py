"""
backend/explainer.py - SHAP explainability engine.
Loads persisted shap.TreeExplainer artifact to compute real feature attributions.
Extracts top 3 contributing features by absolute Shapley magnitude.
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
EXPLAINER_PATH = BASE_DIR / "models" / "explainer.pkl"


class FraudExplainer:
    """Manages SHAP explainer loading and transaction explanation generation."""

    def __init__(self):
        self.explainer = None
        self._loaded = False

    def load_explainer(self):
        """Load persisted SHAP TreeExplainer artifact from disk."""
        if not EXPLAINER_PATH.exists():
            raise FileNotFoundError(f"Explainer artifact not found at {EXPLAINER_PATH}")
        self.explainer = joblib.load(EXPLAINER_PATH)
        self._loaded = True

    def ensure_loaded(self):
        """Lazy load explainer if not already loaded."""
        if not self._loaded:
            self.load_explainer()

    def explain(self, feature_df: pd.DataFrame, top_k: int = 3) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Compute genuine SHAP values for a given preprocessed feature DataFrame.
        Returns:
            (top_reason_names, detailed_contributions)
        """
        self.ensure_loaded()

        # Compute SHAP values
        shap_result = self.explainer(feature_df)
        if hasattr(shap_result, "values"):
            shap_values = shap_result.values[0]
        else:
            shap_values = np.array(shap_result)[0]

        # In binary classification, if shap_values is 2D (samples, classes), take positive class
        if len(shap_values.shape) > 1 and shap_values.shape[-1] == 2:
            shap_values = shap_values[:, 1]

        feature_names = list(feature_df.columns)

        # Sort indices by absolute contribution magnitude descending
        magnitudes = np.abs(shap_values)
        top_indices = np.argsort(magnitudes)[::-1][:top_k]

        top_reasons = []
        detailed_contributions = []

        for idx in top_indices:
            feat = feature_names[idx]
            val = float(shap_values[idx])
            top_reasons.append(feat)
            detailed_contributions.append({
                "feature": feat,
                "shap_value": round(val, 4),
                "impact": "increases_risk" if val > 0 else "decreases_risk"
            })

        return top_reasons, detailed_contributions

    def is_healthy(self) -> bool:
        """Check if explainer artifact is loadable and ready."""
        try:
            self.ensure_loaded()
            return self.explainer is not None
        except Exception:
            return False


# Singleton explainer instance for application-wide reuse
explainer = FraudExplainer()
