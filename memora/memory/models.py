"""
Sibyl Memory Data Models.
Defines the 5 conceptual memory categories required by Memora:
1. IncidentMemory (What happened?)
2. DecisionMemory (What did the agent or team decide?)
3. OutcomeMemory (What happened after the decision?)
4. UnresolvedRiskMemory (What remains open or dangerous?)
5. OperationalLesson (What did the organization learn from previous events and outcomes?)
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class MemoryCategory(str, Enum):
    INCIDENTS = "incidents"
    DECISIONS = "decisions"
    OUTCOMES = "outcomes"
    UNRESOLVED_RISKS = "unresolved_risks"
    OPERATIONAL_LESSONS = "operational_lessons"


class IncidentMemory(BaseModel):
    """Category: INCIDENT MEMORY — What happened?"""
    incident_id: str = Field(..., description="Unique incident identifier e.g. INC-2026-001")
    title: str = Field(..., description="Brief summary of the incident")
    location: str = Field(..., description="Normalized location e.g. Gate 3")
    incident_type: str = Field(..., description="Type of incident e.g. suspicious_vehicle")
    summary: str = Field(..., description="Full text description of the event")
    indicators: List[str] = Field(default_factory=list, description="Key indicators or tags")
    entities_involved: List[str] = Field(default_factory=list, description="Assets/vehicles/persons involved")
    status: str = Field(default="unresolved", description="Incident status: unresolved, resolved, monitoring")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DecisionMemory(BaseModel):
    """Category: DECISION MEMORY — What did the agent or team decide?"""
    decision_id: str = Field(..., description="Unique decision ID")
    incident_id: str = Field(..., description="Referenced incident ID")
    baseline_risk: str = Field(..., description="Risk evaluated from current facts alone")
    final_risk: str = Field(..., description="Risk determined after memory retrieval")
    recommendation: str = Field(..., description="Recommended action")
    rationale: str = Field(..., description="Audit rationale")
    memory_informed: bool = Field(..., description="Whether retrieved memory altered the assessment")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OutcomeMemory(BaseModel):
    """Category: OUTCOME MEMORY — What happened after the decision?"""
    outcome_id: str = Field(..., description="Unique outcome ID")
    incident_id: str = Field(..., description="Referenced incident ID")
    action_taken: str = Field(..., description="Action executed by operations team")
    observed_result: str = Field(..., description="What was observed after taking action")
    is_resolved: bool = Field(..., description="Whether the root threat was eliminated")
    unresolved_reason: Optional[str] = Field(None, description="Reason if still unresolved")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UnresolvedRiskMemory(BaseModel):
    """Category: UNRESOLVED RISK MEMORY — What remains open or dangerous?"""
    risk_id: str = Field(..., description="Unique risk ID")
    incident_id: str = Field(..., description="Associated incident ID")
    location: str = Field(..., description="Location of the risk")
    hazard_description: str = Field(..., description="Detailed description of ongoing hazard")
    severity: str = Field(..., description="Severity level: MEDIUM, HIGH, CRITICAL")
    first_observed: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = Field(default="open", description="open, closed, mitigated")


class OperationalLesson(BaseModel):
    """Category: OPERATIONAL LEARNING — What did the organization learn from previous events and outcomes?"""
    lesson_id: str = Field(..., description="Unique lesson ID")
    incident_id: str = Field(..., description="Source incident ID")
    location: str = Field(..., description="Location context")
    rule_or_insight: str = Field(..., description="Synthesized operational insight")
    failed_prior_action: Optional[str] = Field(None, description="Prior recommendation that was insufficient")
    escalation_recommendation: Optional[str] = Field(None, description="Recommended escalation if pattern repeats")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
