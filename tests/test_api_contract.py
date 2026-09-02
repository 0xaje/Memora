import pytest
from fastapi.testclient import TestClient
from memora.api.app import create_app
from memora.memory.client import SibylClientManager


def test_api_contract_freeze_full_response_structure(tmp_path, monkeypatch):
    """
    Phase 1.75 API Contract Test:
    Verifies that POST /api/incidents/analyze returns all frozen frontend contract fields:
    - incident
    - baseline (risk, recommendation, confidence, factors)
    - memory (found, count, records)
    - inference (recurrence_count, unresolved_history, relevant_patterns, etc.)
    - decision (risk, recommendation, changed, confidence)
    - decision_changed (boolean)
    - decision_change (from_risk, to_risk, from_recommendation, to_recommendation)
    - why_decision_changed (string)
    - provenance (facts, retrieval, inference, decision_shift)
    """
    db_file = str(tmp_path / "contract_test.db")
    test_manager = SibylClientManager(db_path=db_file)

    import memora.memory.client as client_mod
    import memora.api.routes_memory as r_mem_mod
    import memora.api.app as app_mod
    import memora.incidents.service as s_mod

    monkeypatch.setattr(client_mod, "sibyl_manager", test_manager)
    monkeypatch.setattr(r_mem_mod, "sibyl_manager", test_manager)
    monkeypatch.setattr(app_mod, "sibyl_manager", test_manager)
    monkeypatch.setattr(s_mod, "sibyl_manager", test_manager)

    client = TestClient(app_mod.create_app())

    # 1. First event: baseline behavior (zero memory found)
    res_1 = client.post("/api/incidents/analyze", json={
        "raw_text": "Suspicious delivery vehicle observed near Gate 7.",
        "location": "Gate 7"
    })
    assert res_1.status_code == 200
    data_1 = res_1.json()

    # Verify frozen top-level contract keys exist
    for key in [
        "incident", "session", "baseline", "decision", "decision_changed",
        "decision_change", "memory", "inference", "why_decision_changed",
        "provenance", "baseline_assessment", "memory_assessment",
        "memory_influence", "explanation"
    ]:
        assert key in data_1, f"Missing required top-level key: {key}"

    # Baseline assertions
    assert data_1["decision_changed"] is False
    assert data_1["decision_change"] is None
    assert data_1["memory"]["found"] is False
    assert data_1["memory"]["count"] == 0
    assert len(data_1["memory"]["records"]) == 0
    assert data_1["baseline"]["risk"] == "MEDIUM"
    assert data_1["baseline"]["recommendation"] == "MONITOR_AND_VERIFY"
    assert data_1["decision"]["risk"] == "MEDIUM"
    assert data_1["decision"]["recommendation"] == "MONITOR_AND_VERIFY"

    # Provenance assertions
    prov_1 = data_1["provenance"]
    assert "Gate 7" in prov_1["facts"]
    assert "No relevant historical memory found" in prov_1["retrieval"]

    inc_1_id = data_1["incident"]["incident_id"]

    # 2. Record outcome as unresolved -> check OutcomeResponse contract
    res_outcome = client.post("/api/outcomes", json={
        "incident_id": inc_1_id,
        "action_taken": "MONITOR_AND_VERIFY",
        "observed_result": "Driver was evasive; returned without delivery manifest.",
        "is_resolved": False,
        "unresolved_reason": "Suspect loitering on perimeter",
        "operational_lesson": "Monitoring alone did not eliminate suspicious vehicle at Gate 7."
    })
    assert res_outcome.status_code == 200
    out_data = res_outcome.json()

    # Verify OutcomeResponse structure
    assert out_data["status"] == "success"
    assert out_data["incident_id"] == inc_1_id
    assert out_data["is_resolved"] is False
    assert out_data["action_taken"] == "MONITOR_AND_VERIFY"
    assert out_data["observed_result"] == "Driver was evasive; returned without delivery manifest."
    assert out_data["lesson_id"] is not None
    assert out_data["recurrence_count"] == 1
    assert "Monitoring alone did not eliminate" in out_data["lesson_rule"]

    # 3. Second event: memory-informed escalation
    res_2 = client.post("/api/incidents/analyze", json={
        "raw_text": "Suspicious delivery vehicle observed again near Gate 7.",
        "location": "Gate 7"
    })
    assert res_2.status_code == 200
    data_2 = res_2.json()

    # Verify memory-informed escalation
    assert data_2["decision_changed"] is True
    assert data_2["decision_change"] is not None
    assert data_2["decision_change"]["from_risk"] == "MEDIUM"
    assert data_2["decision_change"]["to_risk"] == "HIGH"
    assert data_2["decision_change"]["from_recommendation"] == "MONITOR_AND_VERIFY"
    assert data_2["decision_change"]["to_recommendation"] == "ESCALATE_TO_SUPERVISOR"

    # Memory records UI-safety check: no internal DB paths or raw sqlite rows
    mem_2 = data_2["memory"]
    assert mem_2["found"] is True
    assert mem_2["count"] >= 2
    for rec in mem_2["records"]:
        assert "category" in rec
        assert "id" in rec
        assert "summary" in rec
        assert "status" in rec
        assert "db_path" not in rec  # No internal database paths leaked
        assert "_client" not in rec

    # Inference check
    inf_2 = data_2["inference"]
    assert inf_2["is_recurrent"] is True
    assert inf_2["unresolved_history"] is True
    assert len(inf_2["unresolved_incident_ids"]) >= 1

    test_manager.close()


def test_api_memory_status_and_search_contracts(tmp_path, monkeypatch):
    """
    Verifies GET /api/memory/status and GET /api/memory/search contracts:
    - Does not leak filesystem paths
    - Returns structured tier counts and storage state
    - Validates search queries and isolates tenants
    """
    db_file = str(tmp_path / "memory_api_contract.db")
    test_manager = SibylClientManager(db_path=db_file)

    import memora.memory.client as client_mod
    import memora.api.routes_memory as r_mem_mod
    import memora.api.app as app_mod
    import memora.incidents.service as s_mod

    monkeypatch.setattr(client_mod, "sibyl_manager", test_manager)
    monkeypatch.setattr(r_mem_mod, "sibyl_manager", test_manager)
    monkeypatch.setattr(app_mod, "sibyl_manager", test_manager)
    monkeypatch.setattr(s_mod, "sibyl_manager", test_manager)

    client = TestClient(app_mod.create_app())

    # 1. GET /api/memory/status
    res_status = client.get("/api/memory/status")
    assert res_status.status_code == 200
    st = res_status.json()
    assert st["status"] == "connected"
    assert st["storage_state"] == "healthy"
    assert "counts" in st
    assert "entities_warm" in st["counts"]
    assert "journal_cold" in st["counts"]
    assert "reference" in st["counts"]
    # Verify no filesystem paths are exposed
    assert "db_path" not in st

    # 2. Ingest record for Tenant Alpha
    tenant_a = "00000000-0000-0000-0000-00000000000a"
    tenant_b = "00000000-0000-0000-0000-00000000000b"

    client.post("/api/incidents/analyze", json={
        "raw_text": "Sensitive perimeter incident at Perimeter Fence 9.",
        "location": "Perimeter Fence 9",
        "tenant_id": tenant_a
    })

    # 3. GET /api/memory/search with Tenant Alpha
    res_search_a = client.get(f"/api/memory/search?q=Fence&tenant_id={tenant_a}")
    assert res_search_a.status_code == 200
    data_search_a = res_search_a.json()
    assert data_search_a["count"] >= 1
    assert data_search_a["tenant_id"] == tenant_a
    # Records must be sanitized
    first_hit = data_search_a["results"][0]
    assert "id" in first_hit
    assert "summary" in first_hit
    assert "location" in first_hit
    assert "db_path" not in first_hit

    # 4. GET /api/memory/search with Tenant Beta -> MUST be zero (isolated)
    res_search_b = client.get(f"/api/memory/search?q=Fence&tenant_id={tenant_b}")
    assert res_search_b.status_code == 200
    data_search_b = res_search_b.json()
    assert data_search_b["count"] == 0
    assert len(data_search_b["results"]) == 0

    # 5. Empty search validation
    res_empty = client.get("/api/memory/search?q=   ")
    assert res_empty.status_code == 422
    err_body = res_empty.json()
    assert err_body["detail"]["code"] == "VALIDATION_ERROR"

    test_manager.close()


def test_api_standardized_error_handling(tmp_path, monkeypatch):
    """
    Verifies standardized error payloads on service failures.
    """
    import memora.incidents.service as s_mod
    import memora.api.routes_incidents as r_inc_mod
    import memora.api.app as app_mod
    from memora.memory.client import SibylServiceError

    client = TestClient(app_mod.create_app())

    # Mock service to raise SibylServiceError
    def failing_service():
        class MockService:
            def analyze_incident(self, payload):
                raise SibylServiceError("Simulated disk storage failure")
        return MockService()

    app = app_mod.create_app()
    app.dependency_overrides[r_inc_mod.get_incident_service] = failing_service
    test_client = TestClient(app)

    res = test_client.post("/api/incidents/analyze", json={
        "raw_text": "Observation at Sector 1",
        "location": "Sector 1"
    })
    assert res.status_code == 503
    err = res.json()["detail"]
    assert err["code"] == "SIBYL_UNAVAILABLE"
    assert "Simulated disk storage failure" in err["message"]
