from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

Action = Literal["validate", "false_positive", "escalate"]


class Alert(BaseModel):
    id: int
    ts: datetime
    agent: str
    rule_id: int
    rule_level: int
    severity: str
    technique: Optional[str] = None
    src_ip: Optional[str] = None
    description: str
    status: str
    created_at: datetime


class Ticket(BaseModel):
    id: int
    alert_id: int
    confiance_siem: str
    analyse_llm: str
    severity: str
    recommended_action: Optional[Action] = None
    created_at: datetime


class Decision(BaseModel):
    id: int
    alert_id: int
    analyst: str
    action: Action
    old_status: Optional[str] = None
    new_status: str
    comment: Optional[str] = None
    created_at: datetime


class AlertList(BaseModel):
    items: list[Alert]
    total: int
    page: int
    size: int


class AlertDetail(BaseModel):
    alert: Alert
    ticket: Optional[Ticket] = None
    decisions: list[Decision] = []


class DecisionCreate(BaseModel):
    action: Action
    analyst: str = "analyst"
    comment: Optional[str] = None


# ---- /stats ---------------------------------------------------------------
class SeverityBucket(BaseModel):
    day: str
    severity: str
    n: int


class CoveragePoint(BaseModel):
    manche: Optional[int] = None
    taux_couverture: Optional[float] = None


class Stats(BaseModel):
    by_severity_over_time: list[SeverityBucket]
    agreement_rate: float
    agreement_sample: int
    coverage: list[CoveragePoint] = []
