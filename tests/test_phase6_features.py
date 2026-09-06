"""
Test Suite for Phase 6 Operational Upgrades.
Tests:
- Fact extraction with license plates and perpetrator breach methods
- Temporal decay calculation and location hierarchy inheritance
- Shift Handover Report API (/api/reports/shift-handover)
- Legal & Compliance Audit Export API (/api/audit/export)
- Sibyl Storage Tier Status & Escalation API (/api/memory/tier)
- Multi-Tenant Site Isolation
"""

import pytest
from fastapi.testclient import TestClient
from memora.api.app import app
from memora.intelligence.extractor import FactExtractor
from memora.intelligence.comparator import HistoricalComparator
from memora.memory.client import SibylClientManager
from memora.incidents.service import IncidentService
from memora.incidents.models import IncidentCreate, OutcomeCreate

client = TestClient(app)


def test_license_plate_and_breach_extraction():
    """Verify license plate extraction and breach method detection."""
    extractor = FactExtractor()
    raw = "Silver box truck license plate XYZ-9876 tailgating through Gate 3 without stopping."
    facts = extractor.extract(raw)

    assert facts.location == "Gate 3"
    assert facts.entity_attributes.get("license_plate") == "XYZ-9876"
    assert facts.entity_attributes.get("vehicle_type") == "box truck"
    assert facts.entity_attributes.get("color") == "silver"
    assert facts.entity_attributes.get("breach_method") == "tailgating"
    # Plate was detected, so plate unverified should NOT be in unknowns
    assert not any("License plate" in u for u in facts.unknowns)


def test_location_hierarchy_sector_inheritance():
    """Verify that locations in the same operational sector inherit threat context."""
    comparator = HistoricalComparator()

    # Gate 3 and Loading Dock B are both in the logistics sector
    assert comparator._is_location_relevant("Gate 3", "Loading Dock B") is True

    # Gate 3 and Gate 7 are adversarial gates and must NOT cross-contaminate
    assert comparator._is_location_relevant("Gate 3", "Gate 7") is False


def test_shift_handover_report_endpoint():
    """Verify shift handover report summarizes active threats and failed mitigations."""
    response = client.get("/api/reports/shift-handover?hours=48")
    assert response.status_code == 200
    data = response.json()

    assert "shift_period_hours" in data
    assert "threat_level" in data
    assert "active_unresolved_threats" in data
    assert "failed_mitigations_to_avoid" in data
    assert "supervisor_directives" in data
    assert len(data["supervisor_directives"]) > 0


def test_legal_audit_export_sha256():
    """Verify cryptographic legal audit export reads events and verifies root hash."""
    response = client.get("/api/audit/export?limit=50")
    assert response.status_code == 200
    data = response.json()

    assert data["compliance_framework"] == "SIBYL-COLD-TAMPER-EVIDENT-v1"
    assert data["chain_verified"] is True
    assert "cryptographic_root_digest" in data
    assert len(data["cryptographic_root_digest"]) == 64  # SHA-256 length


def test_sibyl_tier_inspection_and_escalation():
    """Verify querying and updating Sibyl storage tier."""
    # 1. Query tier status
    get_res = client.get("/api/memory/tier")
    assert get_res.status_code == 200
    status_data = get_res.json()
    assert "current_tier" in status_data
    assert "capabilities" in status_data
    assert "status" in status_data

    # 2. Escalate tier to pro
    post_res = client.post("/api/memory/tier", json={"tier": "pro"})
    assert post_res.status_code == 200
    assert post_res.json()["active_tier"] == "pro"

    # Reset back to free
    reset_res = client.post("/api/memory/tier", json={"tier": "free"})
    assert reset_res.status_code == 200
    assert reset_res.json()["active_tier"] == "free"


def test_multi_tenant_site_partition_isolation(tmp_path):
    """Verify that tenant A and tenant B remain strictly partitioned."""
    test_db = str(tmp_path / "partition_test.db")
    mgr = SibylClientManager(db_path=test_db)
    service = IncidentService(client_manager=mgr)

    tenant_a = "11111111-1111-1111-1111-111111111111"
    tenant_b = "22222222-2222-2222-2222-222222222222"

    # Record unresolved outcome in Site Alpha
    res_a = service.analyze_incident(IncidentCreate(
        raw_text="Unauthorized courier loitering at Gate 3.",
        location="Gate 3",
        tenant_id=tenant_a
    ))
    service.record_outcome(OutcomeCreate(
        incident_id=res_a.incident.incident_id,
        action_taken="Monitored Gate 3",
        observed_result="Driver evaded guard",
        is_resolved=False,
        operational_lesson="Do not use passive monitoring.",
        tenant_id=tenant_a
    ))

    # Site Beta analyzes incident at same Gate 3
    res_b = service.analyze_incident(IncidentCreate(
        raw_text="Unauthorized courier observed again at Gate 3.",
        location="Gate 3",
        tenant_id=tenant_b
    ))

    # Tenant B must NOT see Tenant A's memories!
    assert res_b.memory_influence.retrieval_count == 0
    assert res_b.memory_assessment.changed is False
    assert res_b.memory_assessment.risk.value == "MEDIUM"

    mgr.close()


def test_all_five_sibyl_tiers_and_linter():
    """Verify official Sibyl documentation alignment: 5 tiers + memory linter."""
    from fastapi.testclient import TestClient
    from memora.api.app import app

    client = TestClient(app)

    # 1. HOT state tier
    res_set_state = client.post("/api/memory/state/active_shift_test", json={"patrol_leader": "Officer Vance", "status": "ON_PATROL"})
    assert res_set_state.status_code == 200
    res_get_state = client.get("/api/memory/state/active_shift_test")
    assert res_get_state.status_code == 200
    assert res_get_state.json()["state"]["body"]["patrol_leader"] == "Officer Vance"

    # 2. REFERENCE tier
    res_set_ref = client.post("/api/memory/reference/gate_lockdown_sop", json={"protocol": "Perimeter Lockdown SOP", "steps": ["Seal gate", "Alert dispatch"]})
    assert res_set_ref.status_code == 200
    res_get_ref = client.get("/api/memory/reference/gate_lockdown_sop")
    assert res_get_ref.status_code == 200
    assert "Perimeter Lockdown SOP" in res_get_ref.json()["reference"]["body"]

    # 3. Memory status reflects all 5 tiers
    res_status = client.get("/api/memory/status")
    assert res_status.status_code == 200
    counts = res_status.json()["counts"]
    assert "entities_warm" in counts
    assert "journal_cold" in counts
    assert "reference" in counts
    assert "state_hot" in counts
    assert "archived" in counts

    # 4. Memory linter on free vs stake tier
    res_free_lint = client.get("/api/memory/lint")
    assert res_free_lint.status_code == 200
    assert res_free_lint.json()["linter_available"] is False

    # Unlock via stake tier
    client.post("/api/memory/tier", json={"tier": "stake"})
    res_stake_lint = client.get("/api/memory/lint")
    assert res_stake_lint.status_code == 200
    assert "counts" in res_stake_lint.json()

    # Reset back to free tier
    client.post("/api/memory/tier", json={"tier": "free"})

