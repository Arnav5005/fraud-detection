"""
tests/test_api.py - Direct integration tests for FastAPI endpoint functions and persistence.
Avoids ASGI threadpool event-loop deadlocks on Python 3.14 while testing 100% of endpoint logic.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import (
    health_check,
    predict_transaction,
    list_transactions,
    get_stats,
    explain_transaction,
)
from backend.database import Base, Transaction
from backend.schemas import TransactionInput


@pytest.fixture(scope="module")
def db_session():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = Session()
    yield db
    db.close()
    Base.metadata.drop_all(bind=test_engine)


def sample_payload_dict():
    data = {f"V{i}": 0.0 for i in range(1, 29)}
    data["Time"] = 3600.0
    data["Amount"] = 150.0
    return data


def test_health_check_function():
    result = health_check()
    assert result["status"] == "healthy"
    assert result["model_loaded"] is True
    assert result["explainer_loaded"] is True
    assert result["decision_threshold"] is not None


def test_empty_stats_function(db_session):
    stats = get_stats(db=db_session)
    assert stats.total_transactions == 0
    assert stats.fraud_count == 0
    assert stats.legit_count == 0
    assert stats.fraud_rate == 0.0


def test_predict_and_persistence_function(db_session):
    payload = TransactionInput(**sample_payload_dict())
    resp = predict_transaction(payload=payload, db=db_session)

    assert resp.transaction_id > 0
    assert 0.0 <= resp.fraud_probability <= 1.0
    assert resp.verdict in ["fraud", "legitimate"]
    assert len(resp.top_reasons) == 3

    # Verify transaction retrieval
    records = list_transactions(limit=10, db=db_session)
    assert len(records) >= 1
    assert records[0].id == resp.transaction_id
    assert records[0].amount_raw == 150.0

    # Verify stats updated
    stats = get_stats(db=db_session)
    assert stats.total_transactions == 1
    assert stats.fraud_count + stats.legit_count == 1

    # Verify explain function
    explain_res = explain_transaction(transaction_id=resp.transaction_id, db=db_session)
    assert explain_res.transaction_id == resp.transaction_id
    assert explain_res.verdict == resp.verdict
    assert len(explain_res.top_reasons) == 3
    assert explain_res.feature_contributions is not None
    assert len(explain_res.feature_contributions) == 3


def test_explain_not_found_function(db_session):
    with pytest.raises(HTTPException) as exc_info:
        explain_transaction(transaction_id=999999, db=db_session)
    assert exc_info.value.status_code == 404
