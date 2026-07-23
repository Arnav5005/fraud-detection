# pydantic for validation

from attr import field
from pydantic import BaseModel, field_validator
from typing import List

# input
class TransactionInput(BaseModel):
    Time: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    Amount: float

# validation

@field_validator('Amount')
@classmethod
def validate_amt(cls,v:float)->float:
    if(v<0):
        raise ValueError("Amount can't be negative")
    return v

@field_validator('Time')
@classmethod
def validate_time(cls,v:float)->float:
    if(v<0):
        raise ValueError("Time can't be negative")
    return v

# output - respose which the API sends back

class PredictedOutput(BaseModel):
    transaction_id: int
    fraud_probability: float
    verdict: str
    top_reasons: List[str]

class TransactionRecord(BaseModel):
    id: int
    amount: float
    hour: float
    fraud_probability: float
    verdict: str
    timestamp: str

class StatsResponse(BaseModel):
    total_transactions: int
    fraud_count: int
    legit_count: int
    fraud_rate: float