import pytest
from fastapi.testclient import TestClient
from memora.api.app import create_app
from memora.memory.client import SibylClientManager


def test_api_incident_analyze_and_outcome_flow(tmp_path, monkeypatch):
    """Verifies HTTP endpoints work with real Sibyl Memory backend."""
    db_file = str(tmp_path / "api_test.db")
    test_manager = SibylClientManager(db_path=db_file)

    import memora.memory.client as client_mod
    import memora.api.routes_memory as r_mem_mod
    import memora.api.app as app_mod
    import memora.incidents.service as s_mod

    monkeypatch.setattr(client_mod, "sibyl_manager", test_manager)
    monkeypatch.setattr(r_mem_mod, "sibyl_manager", test_manager)
    monkeypatch.setattr(app_mod, "sibyl_manager", test_manager)
    monkeypatch.setattr(s_mod, "sibyl_manager", test_manager)

    # Re-instantiate app with the patched manager
    test_app = app_mod.create_app()
    client = TestClient(test_app)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["sibyl_memory_connected"] is True

    # 2. Analyze incident (Session A)
    payload_a = {
        "raw_text": "Suspicious delivery vehicle observed near Gate 3.",
        "location": "Gate 3"
    }
    res_a = client.post("/api/incidents/analyze", json=payload_a)
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["baseline_assessment"]["risk"] == "MEDIUM"
    assert data_a["baseline_assessment"]["recommendation"] == "MONITOR_AND_VERIFY"
    assert data_a["memory_assessment"]["changed"] is False
    inc_id = data_a["incident"]["incident_id"]

    # 3. Record outcome
    outcome_payload = {
        "incident_id": inc_id,
        "action_taken": "MONITOR_AND_VERIFY",
        "observed_result": "Similar suspicious activity occurred again.",
        "is_resolved": False,
        "unresolved_reason": "Vehicle returned repeatedly during shift",
        "operational_lesson": "Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3."
    }
    res_outcome = client.post("/api/outcomes", json=outcome_payload)
    assert res_outcome.status_code == 200
    assert res_outcome.json()["status"] == "success"

    # 4. Memory Status check
    res_status = client.get("/api/memory/status")
    assert res_status.status_code == 200
    counts = res_status.json()["counts"]
    assert counts["entities_warm"] >= 2  # incident + unresolved_risk + lesson

    # 5. Analyze related incident (Session B)
    payload_b = {
        "raw_text": "Suspicious delivery vehicle observed again near Gate 3."
    }
    res_b = client.post("/api/incidents/analyze", json=payload_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    # Risk and recommendation MUST escalate in Session B
    assert data_b["baseline_assessment"]["risk"] == "MEDIUM"
    assert data_b["memory_assessment"]["risk"] == "HIGH"
    assert data_b["memory_assessment"]["recommendation"] == "ESCALATE_TO_SUPERVISOR"
    assert data_b["memory_assessment"]["changed"] is True
    assert "Gate 3" in data_b["explanation"]["what_happened"]
    assert data_b["memory_influence"]["retrieval_count"] >= 1

    test_manager.close()
