import pytest
from memora.incidents.models import (
    IncidentCreate,
    OutcomeCreate,
    RiskLevel,
    RecommendationType
)
from memora.incidents.service import IncidentService
from memora.memory.client import SibylClientManager


def test_deletion_test_via_toggle(tmp_path):
    """
    Verifies that when memory retrieval is disabled (e.g. deletion test baseline),
    the system performs only a baseline assessment of the current incident,
    losing historical intelligence and repeat-pattern escalation.
    """
    db_path = str(tmp_path / "deletion_toggle.db")
    manager = SibylClientManager(db_path=db_path)
    service = IncidentService(client_manager=manager)

    # 1. Ingest incident 1 & record unresolved outcome
    r1 = service.analyze_incident(IncidentCreate(raw_text="Suspicious delivery vehicle observed near Gate 3."))
    service.record_outcome(OutcomeCreate(
        incident_id=r1.incident.incident_id,
        action_taken="MONITOR_AND_VERIFY",
        observed_result="Vehicle remained parked without authorization",
        is_resolved=False
    ))

    # 2. Deletion mode test (memory_enabled=False)
    # Even though Sibyl has records on disk, the system evaluates only current facts
    req_no_mem = IncidentCreate(
        raw_text="Suspicious delivery vehicle observed again near Gate 3.",
        memory_enabled=False
    )
    res_no_mem = service.analyze_incident(req_no_mem)

    # Risk and recommendation MUST NOT escalate without memory
    assert res_no_mem.memory_assessment.changed is False
    assert res_no_mem.memory_assessment.risk == RiskLevel.MEDIUM
    assert res_no_mem.memory_assessment.recommendation == RecommendationType.MONITOR_AND_VERIFY
    assert res_no_mem.memory_influence.retrieval_count == 0

    # 3. Memory enabled test
    req_with_mem = IncidentCreate(
        raw_text="Suspicious delivery vehicle observed again near Gate 3.",
        memory_enabled=True
    )
    res_with_mem = service.analyze_incident(req_with_mem)

    # Risk and recommendation MUST escalate with memory
    assert res_with_mem.memory_assessment.changed is True
    assert res_with_mem.memory_assessment.risk == RiskLevel.HIGH
    assert res_with_mem.memory_assessment.recommendation == RecommendationType.ESCALATE_TO_SUPERVISOR

    manager.close()


def test_deletion_test_via_database_wipe(tmp_path):
    """
    Verifies that physically removing/clearing the Sibyl SQLite database
    removes historical intelligence naturally without artificial errors.
    """
    db_path = tmp_path / "wiped_memory.db"
    manager = SibylClientManager(db_path=str(db_path))
    service = IncidentService(client_manager=manager)

    # 1. Seed incident and outcome
    r1 = service.analyze_incident(IncidentCreate(raw_text="Suspicious delivery vehicle observed near Gate 3."))
    service.record_outcome(OutcomeCreate(
        incident_id=r1.incident.incident_id,
        action_taken="MONITOR_AND_VERIFY",
        observed_result="Unresolved recurrence",
        is_resolved=False
    ))
    manager.close()

    # 2. Physically wipe the SQLite database file
    if db_path.exists():
        db_path.unlink()

    # 3. New session opens fresh against wiped DB
    fresh_manager = SibylClientManager(db_path=str(db_path))
    fresh_service = IncidentService(client_manager=fresh_manager)

    res = fresh_service.analyze_incident(IncidentCreate(
        raw_text="Suspicious delivery vehicle observed again near Gate 3."
    ))

    # Without the historical database, it falls back gracefully to baseline assessment
    assert res.memory_influence.retrieval_count == 0
    assert res.memory_assessment.changed is False
    assert res.memory_assessment.risk == RiskLevel.MEDIUM
    assert res.memory_assessment.recommendation == RecommendationType.MONITOR_AND_VERIFY

    fresh_manager.close()
