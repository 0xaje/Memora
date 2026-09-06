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
