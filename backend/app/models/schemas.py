from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    account_id: str
    account_type: str = Field(..., description="Savings, Current, Loan, FD")
    creation_date: datetime
    status: str
    balance: float
    last_active_date: datetime
    last_txn_date: datetime


class CustomerBase(BaseModel):
    customer_id: str
    kyc_status: str
    income_bracket: int
    occupation: str
    risk_rating: str


class TransactionBase(BaseModel):
    txn_id: str
    sender_id: str
    receiver_id: str
    amount: float
    timestamp: datetime
    channel: str = Field(..., description="NEFT, IMPS, RTGS, UPI, SWIFT, ATM")
    account_type: str
    device_id: Optional[str] = None
    ip_address: Optional[str] = None


class AlertBase(BaseModel):
    alert_id: str
    timestamp: datetime
    subgraph_nodes: List[str]
    subgraph_edges: List[str]
    risk_score: float
    pattern_type: str = Field(
        ...,
        description=(
            "Cycle, Smurfing, HubAndSpoke, DormantActivation, PassThrough, TemporalLayering"
        ),
    )
    structural_score: float
    innocence_discount: float
    # Disposition resolved from score bands
    disposition: str = Field(
        default="Monitor",
        description="Immediate Review, Deferred Review, Auto-clear, Monitor",
    )
    channels: List[str] = Field(default_factory=list)
    # Per-signal breakdown so the UI can display a breakdown table
    scoring_signals: Dict[str, float] = Field(default_factory=dict)
    llm_explanation: Optional[str] = None
