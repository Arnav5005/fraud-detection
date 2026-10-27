"""
tests/test_schemas.py - Unit tests for Pydantic input/output schemas.
"""

import pytest
from pydantic import ValidationError
from backend.schemas import TransactionInput, PredictedOutput, StatsResponse


def sample_valid_data():
    data = {f"V{i}": 0.0 for i in range(1, 29)}
    data["Time"] = 3600.0
    data["Amount"] = 120.50
    return data


def test_valid_transaction_input():
    data = sample_valid_data()
    item = TransactionInput(**data)
    assert item.Time == 3600.0
    assert item.Amount == 120.50
    assert item.V1 == 0.0
    assert item.V28 == 0.0


def test_negative_amount_rejected():
    data = sample_valid_data()
    data["Amount"] = -1.0
    with pytest.raises(ValidationError) as exc:
        TransactionInput(**data)
    assert "Amount must be non-negative" in str(exc.value)


def test_negative_time_rejected():
    data = sample_valid_data()
    data["Time"] = -5.0
    with pytest.raises(ValidationError) as exc:
        TransactionInput(**data)
    assert "Time must be non-negative" in str(exc.value)


def test_class_leakage_rejected():
    data = sample_valid_data()
    data["Class"] = 1  # Target should never be accepted
    with pytest.raises(ValidationError):
        TransactionInput(**data)


def test_missing_feature_rejected():
    data = sample_valid_data()
    del data["V1"]
    with pytest.raises(ValidationError):
        TransactionInput(**data)


def test_stats_response_zero_division():
    stats = StatsResponse(
        total_transactions=0,
        fraud_count=0,
        legit_count=0,
        fraud_rate=0.0
    )
    assert stats.total_transactions == 0
    assert stats.fraud_rate == 0.0
