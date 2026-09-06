"""
Memora Phase 2.5 Live Verification & Memory-Driven Decision Proof Script.

Verifies against the real FastAPI backend and real Sibyl Memory client:
1. System Health and Sibyl status
2. Session A: Initial incident -> baseline MEDIUM / MONITOR_AND_VERIFY
3. Outcome A: Unresolved outcome recorded -> persisted to Sibyl Memory
4. Session B (Fresh Session): Recurrent incident -> Sibyl retrieves memory -> ESCALATE_TO_SUPERVISOR (decision_changed: True)
5. Deletion Proof: Sibyl memory isolated -> decision drops back to baseline MEDIUM / MONITOR_AND_VERIFY (decision_changed: False)
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from memora.config import settings
from memora.memory.client import SibylClientManager, sibyl_manager
from memora.api.app import create_app


def run_phase_2_5_live_proof():
    print("=" * 70)
    print("MEMORA PHASE 2.5 — LIVE PRODUCT INTEGRATION & MEMORY-DRIVEN DECISION PROOF")
    print("=" * 70)

    # 1. Setup isolated temporary Sibyl Memory database for clean verification
    temp_dir = tempfile.TemporaryDirectory()
    isolated_db_path = str(Path(temp_dir.name) / "live_proof_sibyl.db")
    print(f"[SETUP] Using isolated Sibyl SQLite DB at: {isolated_db_path}")

    # Reinitialize global sibyl manager with isolated path
    sibyl_manager.db_path = isolated_db_path
    sibyl_manager._client = None
    sibyl_manager._client = sibyl_manager.get_client()

    app = create_app()
    client = TestClient(app)

    try:
        # STEP 1: Check Health & Memory Status
        print("\n--- STEP 1: SYSTEM HEALTH & MEMORY STATUS ---")
        health_resp = client.get("/health")
        assert health_resp.status_code == 200, f"Health failed: {health_resp.text}"
        health_data = health_resp.json()
        print(f"GET /health -> status: {health_data.get('status')}, sibyl_connected: {health_data.get('sibyl_memory_connected')}")
        assert health_data["sibyl_memory_connected"] is True

        status_resp = client.get("/api/memory/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        print(f"GET /api/memory/status -> status: {status_data.get('status')}, backend: {status_data.get('backend')}")
        assert status_data["status"] == "connected"

        # STEP 2: Session A - First Incident (No Prior Memory)
        print("\n--- STEP 2: SESSION A (CLEAN INITIAL STATE) ---")
        session_a_payload = {
            "raw_text": "Suspicious delivery vehicle observed near Gate 3.",
            "location": "Gate 3",
            "incident_type": "suspicious_vehicle",
            "session_id": "session-live-a",
        }
        print(f"Submitting Incident A: '{session_a_payload['raw_text']}'")
        res_a = client.post("/api/incidents/analyze", json=session_a_payload)
        assert res_a.status_code == 200, f"Analysis A failed: {res_a.text}"
        data_a = res_a.json()

        incident_id_a = data_a["incident"]["incident_id"]
        baseline_risk_a = data_a["baseline"]["risk"]
        baseline_rec_a = data_a["baseline"]["recommendation"]
        final_risk_a = data_a["decision"]["risk"]
        final_rec_a = data_a["decision"]["recommendation"]
        decision_changed_a = data_a["decision_changed"]
        memory_found_a = data_a["memory"]["found"]

        print(f"  Incident ID: {incident_id_a}")
        print(f"  Baseline:    {baseline_risk_a} · {baseline_rec_a}")
        print(f"  Memory:      Found={memory_found_a}, Count={data_a['memory']['count']}")
        print(f"  Decision:    {final_risk_a} · {final_rec_a}")
        print(f"  Changed:     {decision_changed_a}")

        assert baseline_risk_a == "MEDIUM"
        assert baseline_rec_a == "MONITOR_AND_VERIFY"
        assert final_risk_a == "MEDIUM"
        assert final_rec_a == "MONITOR_AND_VERIFY"
        assert decision_changed_a is False
        print("✓ Session A verified: Clean baseline decision applied without memory shift.")

        # STEP 3: Record Unresolved Outcome for Session A
        print("\n--- STEP 3: RECORD UNRESOLVED OUTCOME (SESSION A) ---")
        outcome_payload = {
            "incident_id": incident_id_a,
            "action_taken": "Monitored delivery vehicle via Gate 3 cameras",
            "observed_result": "Vehicle departed before physical verification; driver unverified",
            "is_resolved": False,
            "unresolved_reason": "Vehicle departed before verification",
            "operational_lesson": "Monitoring alone failed to identify vehicle at Gate 3",
        }
        print(f"Posting Outcome for {incident_id_a} (is_resolved=False)...")
        res_outcome = client.post("/api/outcomes", json=outcome_payload)
        assert res_outcome.status_code == 200, f"Outcome failed: {res_outcome.text}"
        data_outcome = res_outcome.json()

        print(f"  Outcome ID:       {data_outcome.get('outcome_id')}")
        print(f"  Status:           {data_outcome.get('status')}")
        print(f"  Lesson ID:        {data_outcome.get('lesson_id')}")
        print(f"  Recurrence Count: {data_outcome.get('recurrence_count')}")
        print(f"  Message:          {data_outcome.get('message')}")
        assert data_outcome["status"] in ("success", "recorded")
        assert data_outcome["is_resolved"] is False
        print("✓ Outcome persisted: Operational failure recorded in Sibyl Memory.")

        # STEP 4: Session B - Fresh Session (Recurrent Incident)
        print("\n--- STEP 4: SESSION B (FRESH PROCESS/SESSION WITH MEMORY) ---")
        session_b_payload = {
            "raw_text": "Suspicious delivery vehicle observed again near Gate 3.",
            "location": "Gate 3",
            "incident_type": "suspicious_vehicle",
            "session_id": "session-live-b-fresh-99",
        }
        print(f"Submitting Incident B in fresh session: '{session_b_payload['raw_text']}'")
        res_b = client.post("/api/incidents/analyze", json=session_b_payload)
        assert res_b.status_code == 200, f"Analysis B failed: {res_b.text}"
        data_b = res_b.json()

        incident_id_b = data_b["incident"]["incident_id"]
        baseline_risk_b = data_b["baseline"]["risk"]
        baseline_rec_b = data_b["baseline"]["recommendation"]
        final_risk_b = data_b["decision"]["risk"]
        final_rec_b = data_b["decision"]["recommendation"]
        decision_changed_b = data_b["decision_changed"]
        memory_found_b = data_b["memory"]["found"]
        memory_count_b = data_b["memory"]["count"]

        print(f"  Incident ID: {incident_id_b}")
        print(f"  Baseline:    {baseline_risk_b} · {baseline_rec_b}")
        print(f"  Memory:      Found={memory_found_b}, Count={memory_count_b}")
        print(f"  Transformed: {final_risk_b} · {final_rec_b}")
        print(f"  Changed:     {decision_changed_b}")
        print(f"  Why:         {data_b.get('why_decision_changed')}")
        print(f"  Provenance:  {data_b.get('provenance')}")

        assert baseline_risk_b == "MEDIUM"
        assert baseline_rec_b == "MONITOR_AND_VERIFY"
        assert memory_found_b is True
        assert memory_count_b >= 1
        assert final_risk_b == "HIGH"
        assert final_rec_b == "ESCALATE_TO_SUPERVISOR"
        assert decision_changed_b is True
        print("✓ Session B verified: Real Sibyl Memory transformed decision from MEDIUM to HIGH!")

        # STEP 5: Deletion Proof (Isolate Sibyl Memory)
        print("\n--- STEP 5: SIBYL DELETION PROOF ---")
        print("Simulating memory isolation / reset (wiping Sibyl SQLite DB)...")
        # Remove the SQLite database file to simulate memory deletion
        sibyl_manager.close()
        if os.path.exists(isolated_db_path):
            os.remove(isolated_db_path)
        # Re-initialize fresh empty client
        sibyl_manager._client = sibyl_manager.get_client()

        print("Submitting the exact same incident into fresh memory-wiped environment...")
        res_del = client.post("/api/incidents/analyze", json=session_b_payload)
        assert res_del.status_code == 200, f"Analysis Del failed: {res_del.text}"
        data_del = res_del.json()

        baseline_risk_del = data_del["baseline"]["risk"]
        baseline_rec_del = data_del["baseline"]["recommendation"]
        final_risk_del = data_del["decision"]["risk"]
        final_rec_del = data_del["decision"]["recommendation"]
        decision_changed_del = data_del["decision_changed"]
        memory_found_del = data_del["memory"]["found"]

        print(f"  Memory Found: {memory_found_del}")
        print(f"  Baseline:     {baseline_risk_del} · {baseline_rec_del}")
        print(f"  Decision:     {final_risk_del} · {final_rec_del}")
        print(f"  Changed:      {decision_changed_del}")

        assert memory_found_del is False
        assert final_risk_del == "MEDIUM"
        assert final_rec_del == "MONITOR_AND_VERIFY"
        assert decision_changed_del is False
        print("✓ Deletion proof verified: Decision escalation disappeared without Sibyl Memory!")

        print("\n" + "=" * 70)
        print("ALL VERIFICATION CHECKS PASSED: SIBYL MEMORY IS LOAD-BEARING PROVEN!")
        print("=" * 70)
        return True
    finally:
        sibyl_manager.close()
        temp_dir.cleanup()


if __name__ == "__main__":
    success = run_phase_2_5_live_proof()
    sys.exit(0 if success else 1)
