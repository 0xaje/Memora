"""
Incident Domain Models and Schemas.
Enforces strict input validation, domain types, and auditable responses.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationType(str, Enum):
    LOG_AND_PASS = "LOG_AND_PASS"
    MONITOR_AND_VERIFY = "MONITOR_AND_VERIFY"
    DISPATCH_PATROL = "DISPATCH_PATROL"
    ESCALATE_TO_SUPERVISOR = "ESCALATE_TO_SUPERVISOR"
    LOCKDOWN_AREA = "LOCKDOWN_AREA"


class IncidentCreate(BaseModel):
    """External request to report or analyze an operational incident."""
    raw_text: str = Field(..., min_length=5, max_length=2000, description="Raw observation or incident log")
    location: Optional[str] = Field(None, description="Explicit location if known, else extracted")
    incident_type: Optional[str] = Field(None, description="Category of incident e.g. suspicious_vehicle")
    reported_by: Optional[str] = Field("field_operator", description="Reporting entity or sensor")
    session_id: Optional[str] = Field(None, description="Client session identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant UUID for organization isolation")
    memory_enabled: bool = Field(True, description="Toggle for load-bearing memory retrieval vs baseline")

    @field_validator("raw_text")
    @classmethod
    def validate_raw_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("raw_text cannot be empty or whitespace only")
        return v.strip()


class IncidentFacts(BaseModel):
    """Normalized, extracted operational facts."""
    incident_id: str
    location: str
    incident_type: str
    summary: str
    indicators: List[str] = Field(default_factory=list)
    entities_involved: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OutcomeCreate(BaseModel):
    """External request to record the follow-up outcome of an incident."""
    incident_id: str = Field(..., min_length=3, description="Referenced incident ID e.g. INC-001")
    action_taken: str = Field(..., min_length=3, description="Action taken by security team")
    observed_result: str = Field(..., min_length=3, description="Result observed after action taken")
    is_resolved: bool = Field(..., description="Whether the incident was successfully resolved")
    unresolved_reason: Optional[str] = Field(None, description="Reason if unresolved")
    operational_lesson: Optional[str] = Field(None, description="Specific organizational lesson learned")
    tenant_id: Optional[str] = Field(None, description="Tenant UUID for isolation")


class SessionContext(BaseModel):
    id: str
    is_fresh: bool


class BaselineAssessment(BaseModel):
    risk: RiskLevel
    recommendation: RecommendationType
    confidence: float
    factors: List[str]


class MemoryAssessment(BaseModel):
    risk: RiskLevel
    recommendation: RecommendationType
    changed: bool
    confidence: float
    escalation_reason: Optional[str] = None


class MemoryInfluence(BaseModel):
    related_incidents: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_risks: List[Dict[str, Any]] = Field(default_factory=list)
    previous_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    previous_outcomes: List[Dict[str, Any]] = Field(default_factory=list)
    operational_lessons: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_count: int = 0


class DecisionExplanation(BaseModel):
    what_happened: str
    what_was_retrieved: str
    what_pattern_was_inferred: str
    why_decision_changed: str


class DecisionChangeDetails(BaseModel):
    """Explicit diff between baseline assessment and final memory-informed decision."""
    from_risk: RiskLevel
    to_risk: RiskLevel
    from_recommendation: RecommendationType
    to_recommendation: RecommendationType


class PatternInferenceSummary(BaseModel):
    """Explicit structural pattern inferred from Sibyl Memory."""
    is_recurrent: bool = False
    recurrence_count: int = 0
    unresolved_history: bool = False
    unresolved_incident_ids: List[str] = Field(default_factory=list)
    has_prior_failed_outcome: bool = False
    failed_prior_actions: List[str] = Field(default_factory=list)
    verified_mitigations: List[str] = Field(default_factory=list)
    applicable_lessons: List[str] = Field(default_factory=list)
    summary: str = ""


class ProvenanceSummary(BaseModel):
    """Audit provenance cleanly categorizing facts, retrieval, inference, and rationale."""
    facts: str
    retrieval: str
    inference: str
    decision_shift: str


class MemoryRecordUI(BaseModel):
    """UI-safe sanitized representation of a historical memory record."""
    category: str
    id: str
    location: str
    summary: str
    status: str
    timestamp: Optional[str] = None
    action_taken: Optional[str] = None
    is_resolved: Optional[bool] = None
    rule_or_insight: Optional[str] = None
    recurrence_count: Optional[int] = None
    successful_mitigation: Optional[str] = None


class MemorySummary(BaseModel):
    """UI-safe structured summary of retrieved historical memories."""
    found: bool
    count: int
    records: List[MemoryRecordUI] = Field(default_factory=list)


class IncidentAnalysisResult(BaseModel):
    """Full auditable response from Memora for frontend and operational consumers."""
    incident: IncidentFacts
    session: SessionContext
    baseline_assessment: BaselineAssessment
    memory_assessment: MemoryAssessment
    memory_influence: MemoryInfluence
    explanation: DecisionExplanation

    # Direct frontend convenience fields
    baseline: BaselineAssessment
    decision: MemoryAssessment
    decision_changed: bool
    decision_change: Optional[DecisionChangeDetails] = None
    memory: MemorySummary
    inference: PatternInferenceSummary
    why_decision_changed: str
    provenance: ProvenanceSummary


class OutcomeResponse(BaseModel):
    """UI-safe response returned upon recording an operational outcome."""
    status: str
    outcome_id: str
    incident_id: str
    is_resolved: bool
    action_taken: str
    observed_result: str
    unresolved_reason: Optional[str] = None
    lesson_id: Optional[str] = None
    lesson_rule: Optional[str] = None
    recurrence_count: Optional[int] = None
    successful_mitigation: Optional[str] = None
    message: str

    def __getitem__(self, item: str) -> Any:
        """Enables dictionary-style indexing for backwards compatibility with tests and callers."""
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        """Enables dict.get-style access for backwards compatibility."""
        return getattr(self, item, default)
