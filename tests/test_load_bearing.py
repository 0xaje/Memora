import pytest
from memora.incidents.models import (
    IncidentCreate,
    OutcomeCreate,
    RiskLevel,
    RecommendationType
)
from memora.incidents.service import IncidentService
from memora.memory.client import SibylClientManager


def test_end_to_end_load_bearing_memory_proof(tmp_path):
    """
    Complete automated proof of the 8 required steps:
    1. Initial incident intake (Session A).
    2. Store baseline assessment & decision in Sibyl.
    3. Record unresolved outcome and synthesize operational lesson into Sibyl.
    4. Start genuinely fresh session (new process/instance with zero conversational context).
    5. Submit related incident to fresh session.
    6. Verify Sibyl retrieves previous context.
    7. Verify memory-enabled assessment differs materially from baseline.
    8. Verify decision explanation identifies the exact retrieved memory.
    """
    db_path = str(tmp_path / "load_bearing_proof.db")

    # ==========================================
    # SESSION A: INITIAL INCIDENT & UNRESOLVED OUTCOME
    # ==========================================
    manager_a = SibylClientManager(db_path=db_path)
    service_a = IncidentService(client_manager=manager_a)

    req_a = IncidentCreate(
        raw_text="Suspicious delivery vehicle observed near Gate 3.",
        session_id="session_A_initial"
    )

    # STEP 1 & 2: Analyze & Persist
    result_a = service_a.analyze_incident(req_a, session_id="session_A_initial", is_fresh_session=True)

    # Verify Session A initial assessment
    assert result_a.baseline_assessment.risk == RiskLevel.MEDIUM
    assert result_a.baseline_assessment.recommendation == RecommendationType.MONITOR_AND_VERIFY
    assert result_a.memory_assessment.changed is False  # No prior history existed yet
    assert result_a.memory_assessment.risk == RiskLevel.MEDIUM
    assert result_a.memory_assessment.recommendation == RecommendationType.MONITOR_AND_VERIFY

    incident_a_id = result_a.incident.incident_id

    # STEP 3: Record unresolved outcome
    outcome_req = OutcomeCreate(
        incident_id=incident_a_id,
        action_taken="MONITOR_AND_VERIFY",
        observed_result="Similar suspicious activity occurred again. The previous case remains unresolved.",
        is_resolved=False,
        unresolved_reason="Vehicle departed before patrol arrived and returned later.",
        operational_lesson="Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3."
    )
    outcome_res = service_a.record_outcome(outcome_req)
    assert outcome_res["status"] == "success"

    # Close Session A completely
    manager_a.close()
    del service_a
    del manager_a

    # ==========================================
    # SESSION B: GENUINELY FRESH SESSION
    # ==========================================
    # New manager, new service, NO prior in-memory state or prompt injection
    manager_b = SibylClientManager(db_path=db_path)
    service_b = IncidentService(client_manager=manager_b)

    req_b = IncidentCreate(
        raw_text="Suspicious delivery vehicle observed again near Gate 3.",
        session_id="session_B_fresh"
    )

    # STEP 4 & 5: Fresh session receives related incident
    result_b = service_b.analyze_incident(req_b, session_id="session_B_fresh", is_fresh_session=True)

    # STEP 6: Verify Sibyl retrieved previous context
    assert result_b.memory_influence.retrieval_count >= 1
    assert len(result_b.memory_influence.related_incidents) >= 1
    assert len(result_b.memory_influence.unresolved_risks) >= 1
    assert len(result_b.memory_influence.operational_lessons) >= 1

    # STEP 7: Verify memory assessment differs materially from baseline
    # Without memory, baseline is still MEDIUM / MONITOR_AND_VERIFY
    assert result_b.baseline_assessment.risk == RiskLevel.MEDIUM
    assert result_b.baseline_assessment.recommendation == RecommendationType.MONITOR_AND_VERIFY

    # WITH retrieved Sibyl Memory, risk escalated to HIGH and recommendation changed to ESCALATE_TO_SUPERVISOR!
    assert result_b.memory_assessment.changed is True
    assert result_b.memory_assessment.risk == RiskLevel.HIGH
    assert result_b.memory_assessment.recommendation == RecommendationType.ESCALATE_TO_SUPERVISOR

    # STEP 8: Verify explanation explicitly accounts for retrieved memory
    explanation = result_b.explanation
    assert "Gate 3" in explanation.what_happened
    assert "Retrieved" in explanation.what_was_retrieved
    assert "Sibyl Memory" in explanation.what_was_retrieved
    assert "ESCALATE_TO_SUPERVISOR" in explanation.why_decision_changed
    assert "HIGH" in explanation.why_decision_changed

    manager_b.close()
