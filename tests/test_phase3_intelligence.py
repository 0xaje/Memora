"""
Phase 3 Intelligence Layer & Operational Reasoning Tests.
Tests:
- Rich fact extraction (time, duration, entity attributes, reporter, explicit unknowns)
- Evidence taxonomy separation (CURRENT_FACT, HISTORICAL_FACT, INFERENCE, UNKNOWN, RECOMMENDATION)
- Failed mitigation intelligence (diagnosis & current operational implication)
- Actionable operational lesson translation
- Adversarial Test 1: Location relevance boundary (Gate 3 vehicle memory does NOT escalate Gate 7)
- Adversarial Test 2: Resolved vs Unresolved history (resolved prior incident does not trigger unresolved hazard escalation)
"""

import os
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from memora.api.app import create_app
from memora.memory.client import sibyl_manager, SibylClientManager
from memora.incidents.service import IncidentService
from memora.incidents.models import (
    IncidentCreate,
    OutcomeCreate,
    RiskLevel,
    RecommendationType,
    EvidenceType
)
from memora.intelligence.extractor import FactExtractor


@pytest.fixture
def isolated_client(tmp_path):
    """Provides a fresh isolated Sibyl SQLite environment for each test."""
    db_file = str(tmp_path / "test_p3.db")
    mgr = SibylClientManager(db_path=db_file)
    service = IncidentService(client_manager=mgr)
    return service, mgr


def test_rich_fact_extraction_complex_incident():
    """Verify rich deterministic extraction parses time, duration, entities, reporter, and unknowns."""
    extractor = FactExtractor()
    raw = (
        "At approximately 21:40, one of the guards reported seeing the same white delivery van "
        "again near Gate 3. The vehicle remained around the area for several minutes before leaving."
    )
    facts = extractor.extract(raw)

    assert facts.location == "Gate 3"
    assert facts.incident_type == "suspicious_vehicle"
    assert facts.approximate_time in ("21:40", "21:40,") or "21:40" in facts.approximate_time
    assert facts.duration is not None and "minutes" in facts.duration
    assert facts.reported_by == "one of the guards"
    assert facts.entity_attributes.get("color") == "white"
    assert facts.entity_attributes.get("vehicle_type") == "van"
    assert facts.entity_attributes.get("is_recurrent_mention") is True
    assert "repeat occurrence" in facts.indicators
    # Explicit unknowns should be declared
    assert any("License plate" in unk for unk in facts.unknowns)
    assert any("Driver" in unk for unk in facts.unknowns)


def test_adversarial_location_relevance_boundary(isolated_client):
    """
    Adversarial Test 1:
    Incident A occurs at Gate 3.
    Incident B occurs at Gate 7 (routine maintenance truck).
    Memora must NOT use Gate 3 history to escalate Gate 7.
    """
    service, mgr = isolated_client

    # 1. Ingest incident at Gate 3 and record unresolved outcome
    inc_a = service.analyze_incident(IncidentCreate(
        raw_text="Suspicious delivery vehicle observed near Gate 3.",
        location="Gate 3",
        incident_type="suspicious_vehicle"
    ))
    service.record_outcome(OutcomeCreate(
        incident_id=inc_a.incident.incident_id,
        action_taken="Monitored Gate 3 via camera",
        observed_result="Vehicle departed unverified",
        is_resolved=False,
        operational_lesson="Gate 3 camera monitoring insufficient"
    ))

    # 2. Ingest unrelated vehicle incident at Gate 7
    inc_b = service.analyze_incident(IncidentCreate(
        raw_text="Routine maintenance truck arrived at Gate 7 for scheduled delivery.",
        location="Gate 7",
        incident_type="suspicious_vehicle"
    ))

    # Gate 7 must NOT escalate due to Gate 3's unresolved memory!
    assert inc_b.incident.location == "Gate 7"
    assert inc_b.decision.risk == inc_b.baseline.risk
    assert inc_b.decision.recommendation == inc_b.baseline.recommendation
    assert inc_b.decision_changed is False
    assert inc_b.inference.is_recurrent is False
    assert inc_b.inference.unresolved_history is False


def test_adversarial_resolved_vs_unresolved_history(isolated_client):
    """
    Adversarial Test 2:
    Historical incident at Gate 3 was successfully RESOLVED.
    Current incident at Gate 3 occurs again.
    Memora must recognize recurrence but NOT escalate to unresolved hazard level.
    """
    service, mgr = isolated_client

    # 1. Ingest incident at Gate 3 and record RESOLVED outcome
    inc_prev = service.analyze_incident(IncidentCreate(
        raw_text="Suspicious delivery vehicle arrived at Gate 3.",
        location="Gate 3",
        incident_type="suspicious_vehicle"
    ))
    service.record_outcome(OutcomeCreate(
        incident_id=inc_prev.incident.incident_id,
        action_taken="Inspected driver credentials and bill of lading",
        observed_result="Driver identity verified and authorized delivery confirmed",
        is_resolved=True,
        operational_lesson="Physical credential check resolved delivery verification"
    ))

    # 2. Same vehicle arrives at Gate 3 again
    inc_new = service.analyze_incident(IncidentCreate(
        raw_text="Suspicious delivery vehicle observed again near Gate 3.",
        location="Gate 3",
        incident_type="suspicious_vehicle"
    ))

    # Recurrence should be recognized, but because previous incident was resolved,
    # it must not trigger the unresolved hazard escalation!
    assert inc_new.inference.is_recurrent is True
    assert inc_new.inference.unresolved_history is False
    assert inc_new.inference.is_resolved_precedent is True
    assert inc_new.decision.risk == inc_new.baseline.risk
    assert inc_new.decision_changed is False


def test_failed_mitigation_and_actionable_lesson_intelligence(isolated_client):
    """
    Verify that a failed historical mitigation produces explicit diagnosis
    and actionable operational implications.
    """
    service, mgr = isolated_client

    inc_1 = service.analyze_incident(IncidentCreate(
        raw_text="Unidentified delivery van loitering near Gate 3.",
        location="Gate 3",
        incident_type="suspicious_vehicle"
    ))
    service.record_outcome(OutcomeCreate(
        incident_id=inc_1.incident.incident_id,
        action_taken="Monitored delivery van via Gate 3 cameras",
        observed_result="Van departed before physical verification; driver unverified",
        is_resolved=False,
        operational_lesson="Camera monitoring alone failed to identify vehicle at Gate 3"
    ))

    # Recurrent incident
    inc_2 = service.analyze_incident(IncidentCreate(
        raw_text="Same delivery van returned to Gate 3.",
        location="Gate 3",
        incident_type="suspicious_vehicle"
    ))

    assert inc_2.decision_changed is True
    assert inc_2.decision.risk == RiskLevel.HIGH
    assert inc_2.decision.recommendation == RecommendationType.ESCALATE_TO_SUPERVISOR

    # Verify failed mitigation details
    assert len(inc_2.failed_mitigations) > 0
    fm = inc_2.failed_mitigations[0]
    assert "Monitored delivery van" in fm.prior_action
    assert "Repeating" in fm.current_implication

    # Verify actionable lesson details
    assert len(inc_2.actionable_lessons) > 0
    al = inc_2.actionable_lessons[0]
    assert "insufficient" in al.current_implication.lower()
    assert "Escalate" in al.recommended_adjustment

    # Verify structured evidence chain
    types = [item.type for item in inc_2.evidence_chain]
    assert EvidenceType.CURRENT_FACT in types
    assert EvidenceType.HISTORICAL_FACT in types
    assert EvidenceType.INFERENCE in types
    assert EvidenceType.RECOMMENDATION in types
    assert EvidenceType.UNKNOWN in types
