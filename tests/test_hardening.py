import pytest
from memora.incidents.models import (
    IncidentCreate,
    OutcomeCreate,
    RiskLevel,
    RecommendationType
)
from memora.incidents.service import IncidentService
from memora.memory.client import SibylClientManager


def test_multi_scenario_generalization(tmp_path):
    """
    Requirement 5: Test generalization across at least 3 completely different scenarios:
    - Scenario 1: Unattended package near Loading Dock -> unresolved recurrence -> LOCKDOWN_AREA
    - Scenario 2: Unauthorized trespasser at North Wing -> unresolved loitering -> ESCALATE_TO_SUPERVISOR
    - Scenario 3: Routine observation at Warehouse B -> resolved outcome -> no escalation
    """
    db_path = str(tmp_path / "generalization_test.db")
    manager = SibylClientManager(db_path=db_path)
    service = IncidentService(client_manager=manager)

    # -------------------------------------------------------------
    # SCENARIO 1: Suspicious package at Loading Dock
    # -------------------------------------------------------------
    # Session 1: Intake package observation
    res_dock_1 = service.analyze_incident(IncidentCreate(
        raw_text="Unattended package observed near Loading Dock 4.",
        location="Loading Dock 4"
    ))
    assert res_dock_1.baseline_assessment.risk == RiskLevel.MEDIUM
    assert res_dock_1.baseline_assessment.recommendation == RecommendationType.DISPATCH_PATROL
    assert res_dock_1.memory_assessment.changed is False

    # Record unresolved outcome: patrol could not locate owner, package remains unaccounted for
    service.record_outcome(OutcomeCreate(
        incident_id=res_dock_1.incident.incident_id,
        action_taken="DISPATCH_PATROL",
        observed_result="Package still present; no courier manifest found.",
        is_resolved=False,
        unresolved_reason="Potential explosive or hazardous contraband.",
        operational_lesson="Standard patrol verification insufficient for unattended package at Loading Dock 4."
    ))

    # Fresh intake for Scenario 1
    res_dock_2 = service.analyze_incident(IncidentCreate(
        raw_text="Unattended package observed again near Loading Dock 4.",
        location="Loading Dock 4"
    ))
    # MUST escalate to CRITICAL/HIGH and recommend LOCKDOWN_AREA
    assert res_dock_2.memory_assessment.changed is True
    assert res_dock_2.memory_assessment.recommendation == RecommendationType.LOCKDOWN_AREA
    assert res_dock_2.memory_influence.retrieval_count >= 1
    assert "Loading Dock 4" in res_dock_2.explanation.what_happened

    # -------------------------------------------------------------
    # SCENARIO 2: Unauthorized trespasser at North Wing
    # -------------------------------------------------------------
    res_north_1 = service.analyze_incident(IncidentCreate(
        raw_text="Unauthorized individual observed loitering near North Wing checkpoint.",
        location="North Wing"
    ))
    assert res_north_1.baseline_assessment.risk == RiskLevel.MEDIUM
    assert res_north_1.baseline_assessment.recommendation == RecommendationType.MONITOR_AND_VERIFY
    assert res_north_1.memory_assessment.changed is False

    # Record outcome: individual fled before questioning, risk remains open
    service.record_outcome(OutcomeCreate(
        incident_id=res_north_1.incident.incident_id,
        action_taken="MONITOR_AND_VERIFY",
        observed_result="Individual evaded security cameras and returned to perimeter.",
        is_resolved=False,
        unresolved_reason="Surveillance blindspot in North Wing.",
        operational_lesson="Monitoring alone did not prevent repeated loitering at North Wing."
    ))

    # Fresh intake for Scenario 2
    res_north_2 = service.analyze_incident(IncidentCreate(
        raw_text="Unauthorized person observed again near North Wing.",
        location="North Wing"
    ))
    assert res_north_2.memory_assessment.changed is True
    assert res_north_2.memory_assessment.risk == RiskLevel.HIGH
    assert res_north_2.memory_assessment.recommendation == RecommendationType.ESCALATE_TO_SUPERVISOR
    assert res_north_2.memory_influence.retrieval_count >= 1

    # -------------------------------------------------------------
    # SCENARIO 3: Routine observation at Warehouse B (Resolved outcome)
    # -------------------------------------------------------------
    res_wh_1 = service.analyze_incident(IncidentCreate(
        raw_text="Routine contractor movement near Warehouse B.",
        location="Warehouse B"
    ))
    assert res_wh_1.baseline_assessment.risk == RiskLevel.LOW
    assert res_wh_1.baseline_assessment.recommendation == RecommendationType.LOG_AND_PASS

    # Record outcome: Verified and resolved
    service.record_outcome(OutcomeCreate(
        incident_id=res_wh_1.incident.incident_id,
        action_taken="LOG_AND_PASS",
        observed_result="Contractor badges confirmed and authorized.",
        is_resolved=True
    ))

    # Fresh intake for Warehouse B
    res_wh_2 = service.analyze_incident(IncidentCreate(
        raw_text="Routine contractor movement near Warehouse B.",
        location="Warehouse B"
    ))
    # Should NOT escalate because prior outcome was cleanly resolved
    assert res_wh_2.memory_assessment.changed is False
    assert res_wh_2.memory_assessment.risk == RiskLevel.LOW
    assert res_wh_2.memory_assessment.recommendation == RecommendationType.LOG_AND_PASS

    manager.close()


def test_dynamic_learning_feedback_loop(tmp_path):
    """
    Requirement 6: Dynamic Memory Feedback Loop.
    Verifies that when an unresolved incident later achieves confirmed resolution:
    1. Incident is marked unresolved -> lesson created noting monitoring failed.
    2. Later action resolves it -> lesson updated with confirmed resolution and risk marked mitigated.
    3. Subsequent query reflects the confirmed resolution.
    """
    db_path = str(tmp_path / "dynamic_learning.db")
    manager = SibylClientManager(db_path=db_path)
    service = IncidentService(client_manager=manager)

    # 1. First event: Gate 5
    r1 = service.analyze_incident(IncidentCreate(
        raw_text="Suspicious delivery vehicle near Gate 5.",
        location="Gate 5"
    ))
    inc_1_id = r1.incident.incident_id

    # Outcome 1: Failed monitoring -> unresolved
    service.record_outcome(OutcomeCreate(
        incident_id=inc_1_id,
        action_taken="MONITOR_AND_VERIFY",
        observed_result="Vehicle returned; driver refused to display manifest.",
        is_resolved=False,
        operational_lesson="Monitoring alone did not resolve recurring activity near Gate 5."
    ))

    # Check lesson was written
    retrieval_1 = service.retriever.retrieve_context(location="Gate 5")
    assert len(retrieval_1.operational_lessons) == 1
    assert retrieval_1.operational_lessons[0]["failed_prior_action"] == "MONITOR_AND_VERIFY"

    # 2. Second event: Escalated action taken and successfully resolves the threat
    r2 = service.analyze_incident(IncidentCreate(
        raw_text="Suspicious delivery vehicle near Gate 5.",
        location="Gate 5"
    ))
    inc_2_id = r2.incident.incident_id

    # Outcome 2: Supervisor escalation dispatched police -> RESOLVED
    service.record_outcome(OutcomeCreate(
        incident_id=inc_2_id,
        action_taken="ESCALATE_TO_SUPERVISOR",
        observed_result="Supervisor escorted vehicle off premises and issued formal trespass notice.",
        is_resolved=True
    ))

    # 3. Verify dynamic refinement:
    # Top lesson at Gate 5 now documents the confirmed successful mitigation
    retrieval_2 = service.retriever.retrieve_context(location="Gate 5")
    assert len(retrieval_2.operational_lessons) >= 1
    lesson = retrieval_2.operational_lessons[0]
    assert lesson.get("successful_mitigation") == "ESCALATE_TO_SUPERVISOR"
    assert "Confirmed resolution" in lesson.get("rule_or_insight", "")

    manager.close()


def test_tenant_isolation_boundary(tmp_path):
    """
    Requirement 9: Tenant Isolation.
    Ensures Tenant Alpha's operational memory cannot be retrieved by Tenant Beta.
    """
    db_path = str(tmp_path / "tenant_isolation.db")
    manager = SibylClientManager(db_path=db_path)
    service = IncidentService(client_manager=manager)

    tenant_alpha = "00000000-0000-0000-0000-00000000000a"
    tenant_beta = "00000000-0000-0000-0000-00000000000b"

    # 1. Tenant Alpha ingests incident and unresolved outcome
    r_alpha = service.analyze_incident(IncidentCreate(
        raw_text="Confidential breach at Sector 7.",
        location="Sector 7",
        tenant_id=tenant_alpha
    ))
    service.record_outcome(OutcomeCreate(
        incident_id=r_alpha.incident.incident_id,
        action_taken="DISPATCH_PATROL",
        observed_result="Intruder observed near server vault.",
        is_resolved=False,
        tenant_id=tenant_alpha
    ))

    # 2. Tenant Beta queries the same location
    r_beta = service.analyze_incident(IncidentCreate(
        raw_text="Routine observation at Sector 7.",
        location="Sector 7",
        tenant_id=tenant_beta
    ))

    # Tenant Beta MUST NOT see Tenant Alpha's memory!
    assert r_beta.memory_influence.retrieval_count == 0
    assert len(r_beta.memory_influence.related_incidents) == 0
    assert r_beta.memory_assessment.changed is False

    # 3. Tenant Alpha queries the same location -> receives its own history
    r_alpha_recall = service.analyze_incident(IncidentCreate(
        raw_text="Observation at Sector 7.",
        location="Sector 7",
        tenant_id=tenant_alpha
    ))
    assert r_alpha_recall.memory_influence.retrieval_count >= 1
    assert len(r_alpha_recall.memory_influence.related_incidents) >= 1

    manager.close()
