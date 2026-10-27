"""
backend/database.py - Database connection, SQLAlchemy models, and CRUD operations.
Supports SQLite by default, database-agnostic through SQLAlchemy.
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, desc
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Anchor DB path to workspace root
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "fraud_detection.db"
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

engine = create_engine(
    DB_URL,
    echo=False,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Transaction(Base):
    """Persisted transaction record with prediction results and audit details."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time_raw = Column(Float, nullable=False)
    amount_raw = Column(Float, nullable=False)
    hour = Column(Float, nullable=False)
    log_amount = Column(Float, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    verdict = Column(String, nullable=False)
    top_reasons = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction model to dictionary representation."""
        reasons_list = [r.strip() for r in self.top_reasons.split(",") if r.strip()] if self.top_reasons else []
        return {
            "id": self.id,
            "time_raw": self.time_raw,
            "amount_raw": self.amount_raw,
            "hour": self.hour,
            "log_amount": self.log_amount,
            "fraud_probability": round(self.fraud_probability, 4),
            "verdict": self.verdict,
            "top_reasons": reasons_list,
            "timestamp": self.timestamp.isoformat() if self.timestamp else datetime.now(timezone.utc).isoformat(),
        }


def init_db():
    """Create all tables in the database if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_transaction(
    db: Session,
    time_raw: float,
    amount_raw: float,
    hour: float,
    log_amount: float,
    fraud_probability: float,
    verdict: str,
    top_reasons: List[str]
) -> int:
    """Save a scored transaction to the database."""
    reasons_str = ", ".join(top_reasons) if isinstance(top_reasons, list) else str(top_reasons)
    transaction = Transaction(
        time_raw=time_raw,
        amount_raw=amount_raw,
        hour=hour,
        log_amount=log_amount,
        fraud_probability=fraud_probability,
        verdict=verdict,
        top_reasons=reasons_str,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction.id


def get_transaction_by_id(db: Session, transaction_id: int) -> Optional[Transaction]:
    """Retrieve a transaction by primary key."""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_recent_transactions(db: Session, limit: int = 50) -> List[Transaction]:
    """Retrieve recent transactions ordered by newest first."""
    return db.query(Transaction).order_by(desc(Transaction.id)).limit(limit).all()


def get_statistics(db: Session) -> Dict[str, Any]:
    """
    Calculate aggregate transaction statistics.
    Handles empty database case with 0 fraud rate.
    """
    total = db.query(Transaction).count()
    if total == 0:
        return {
            "total_transactions": 0,
            "fraud_count": 0,
            "legit_count": 0,
            "fraud_rate": 0.0
        }

    fraud_count = db.query(Transaction).filter(Transaction.verdict == "fraud").count()
    legit_count = total - fraud_count
    fraud_rate = round(fraud_count / total, 4)

    return {
        "total_transactions": total,
        "fraud_count": fraud_count,
        "legit_count": legit_count,
        "fraud_rate": fraud_rate
    }
