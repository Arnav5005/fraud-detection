from sqlalchemy import create_engine , Column , Integer , Float , String , DateTime, true
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DB_URL = 'sqlite:///mydatabase.db'

engine = create_engine(
    DB_URL,
    echo = True,
    connect_args = {"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False,bind=engine)
Base = declarative_base()

# table definition
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time_raw = Column(Float)
    amount_raw = Column(Float)
    hour = Column(Float)
    log_amount = Column(Float)
    fraud_probability = Column(Float)
    verdict = Column(String)
    top_reasons = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

