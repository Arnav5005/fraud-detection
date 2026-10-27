"""
tests/test_ml_pipeline.py - Unit tests for ML serving consistency, preprocessing, and SHAP.
"""

import pytest
import numpy as np
import pandas as pd
from backend.predictor import predictor, FEATURE_COLUMNS
from backend.explainer import explainer


@pytest.fixture(scope="module", autouse=True)
def setup_ml():
    predictor.ensure_loaded()
    explainer.ensure_loaded()


def test_artifacts_loaded():
    assert predictor.model is not None
    assert predictor.scaler is not None
    assert isinstance(predictor.threshold, float)
    assert 0.0 < predictor.threshold < 1.0


def test_feature_columns_order():
    expected_cols = [f"V{i}" for i in range(1, 29)] + ["Amount", "Hour"]
    assert FEATURE_COLUMNS == expected_cols


def test_preprocessing():
    payload = {f"V{i}": 0.0 for i in range(1, 29)}
    payload["Time"] = 7200.0  # 2 hours
    payload["Amount"] = 100.0

    df, hour, log_amount = predictor.preprocess(payload)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == FEATURE_COLUMNS
    assert df.shape == (1, 30)
    assert hour == 2.0
    assert np.isclose(log_amount, np.log1p(100.0))


def test_prediction_output():
    payload = {f"V{i}": 0.0 for i in range(1, 29)}
    payload["Time"] = 3600.0
    payload["Amount"] = 25.0

    result = predictor.predict(payload)
    assert "fraud_probability" in result
    assert "verdict" in result
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert result["verdict"] in ["fraud", "legitimate"]
    expected_verdict = "fraud" if result["fraud_probability"] >= predictor.threshold else "legitimate"
    assert result["verdict"] == expected_verdict


def test_shap_explainer():
    payload = {f"V{i}": 0.0 for i in range(1, 29)}
    payload["Time"] = 3600.0
    payload["Amount"] = 50.0

    df, _, _ = predictor.preprocess(payload)
    top_reasons, detailed = explainer.explain(df, top_k=3)

    assert len(top_reasons) == 3
    assert all(r in FEATURE_COLUMNS for r in top_reasons)
    assert len(detailed) == 3
    for item in detailed:
        assert "feature" in item
        assert "shap_value" in item
        assert item["impact"] in ["increases_risk", "decreases_risk"]
