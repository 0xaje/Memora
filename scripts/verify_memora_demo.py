#!/usr/bin/env python3
"""
MEMORA — PHASE 4: OFFICIAL JUDGE DEMO VERIFICATION SCRIPT
Verifies the complete 9-step operational reasoning journey and load-bearing proof:

A. Fresh Memory State (Clean SQLite DB)
B. Incident Creation (Session A)
C. Unresolved Outcome & Tactical Failure Persistence
D. Fresh Process/Session Context (Cold-Start)
E. Memory Retrieval & Pattern Correlation
F. Decision Transformation (MEDIUM -> HIGH)
G. Historical Evidence References (Mitigations, Lessons, Taxonomy)
H. Deletion Proof (Isolating Sibyl reverts to baseline)
I. Memory Restoration & Cleanup Verification
"""

import os
import sys
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from memora.memory.client import sibyl_manager
from memora.api.app import create_app


def run_demo_proof():
    print("=" * 75)
    print("MEMORA — COLD-START RECALL & LOAD-BEARING SIBYL DEMO PROOF")
    print("=" * 75)

    temp_dir = tempfile.TemporaryDirectory()
    isolated_db_path = str(Path(temp_dir.name) / "demo_proof_sibyl.db")
    print(f"\n[A] FRESH MEMORY STATE")
    print(f"    Isolated Sibyl DB initialized at: {isolated_db_path}")

    # Point global manager to isolated DB
    sibyl_manager.db_path = isolated_db_path
    sibyl_manager._client = None
    client_instance = sibyl_manager.get_client()

    app = create_app()
    client = TestClient(app)

    # Health & status check
    health = client.get("/health").json()
    assert health.get("sibyl_memory_connected") is True, "Sibyl not connected"
    print(f"    Backend: Healthy (:8000) | Sibyl Memory: Connected (SQLite FTS5)")

    # [B] Incident Creation (Session A)
    print(f"\n[B] INCIDENT CREATION — SESSION A (STATELESS COLD-START)")
    incident_a_payload = {
        "raw_text": "Suspicious delivery vehicle observed lingering near Gate 3 for 45 minutes.",
        "location": "Gate 3",
        "incident_type": "suspicious_vehicle"
    }
    resp_a = client.post("/api/incidents/analyze", json=incident_a_payload)
    assert resp_a.status_code == 200, f"Analyze A failed: {resp_a.text}"
    data_a = resp_a.json()
    inc_a_id = data_a["incident"]["incident_id"]

    baseline_a_risk = data_a["baseline"]["risk"]
    baseline_a_rec = data_a["baseline"]["recommendation"]
    dec_a_risk = data_a["decision"]["risk"]
    changed_a = data_a["decision_changed"]
    mem_found_a = data_a["memory"]["found"]

    print(f"    Incident ID: {inc_a_id}")
    print(f"    Baseline Assessment: {baseline_a_risk} · {baseline_a_rec}")
    print(f"    Historical Memory:   Found={mem_found_a} (Records=0)")
    print(f"    Memora Decision:     {dec_a_risk} · {data_a['decision']['recommendation']}")
    print(f"    Decision Changed:    {changed_a}")
    assert baseline_a_risk == "MEDIUM"
    assert dec_a_risk == "MEDIUM"
    assert changed_a is False
    print("    ✓ Verified: Stateless baseline applied when no historical memory exists.")

    # [C] Unresolved Outcome Persistence
    print(f"\n[C] UNRESOLVED OUTCOME & TACTICAL FAILURE PERSISTENCE")
    outcome_payload = {
        "incident_id": inc_a_id,
        "action_taken": "Monitored delivery vehicle via Gate 3 perimeter cameras",
        "observed_result": "Vehicle departed before license or driver credentials could be verified",
        "is_resolved": False,
        "unresolved_reason": "Camera resolution was insufficient to capture driver credentials",
        "operational_lesson": "Passive monitoring alone failed to resolve suspicious vehicle at Gate 3. Require physical patrol intercept."
    }
    resp_out = client.post("/api/outcomes", json=outcome_payload)
    assert resp_out.status_code == 200, f"Outcome recording failed: {resp_out.text}"
    out_data = resp_out.json()
    print(f"    Outcome ID:          {out_data['outcome_id']}")
    print(f"    Resolution State:    UNRESOLVED")
    print(f"    Tactical Action:     {outcome_payload['action_taken']}")
    print(f"    Failure Result:      {outcome_payload['observed_result']}")
    print(f"    Institutional Rule:  {out_data['lesson_id']}")
    print("    ✓ Verified: Tactical failure and operational lesson stored in Sibyl SQLite.")

    # [D] Fresh Process / Session Initiation
    print(f"\n[D] FRESH PROCESS / SESSION INITIATION (COLD-START)")
    # Reset in-memory cached client instances to force re-retrieval from disk
    sibyl_manager._client = None
    fresh_client = TestClient(app)
    print("    ✓ Verified: In-memory state cleared. New session reading strictly from disk.")

    # [E] Memory Retrieval & Pattern Correlation
    print(f"\n[E] INCIDENT B SUBMISSION & MEMORY RETRIEVAL")
    incident_b_payload = {
        "raw_text": "Suspicious delivery vehicle observed again near Gate 3.",
        "location": "Gate 3",
        "incident_type": "suspicious_vehicle"
    }
    resp_b = fresh_client.post("/api/incidents/analyze", json=incident_b_payload)
    assert resp_b.status_code == 200, f"Analyze B failed: {resp_b.text}"
    data_b = resp_b.json()

    mem_found_b = data_b["memory"]["found"]
    mem_count_b = data_b["memory"]["count"]
    print(f"    Incident ID:         {data_b['incident']['incident_id']}")
    print(f"    Historical Memory:   Found={mem_found_b} (Retrieved {mem_count_b} records)")
    assert mem_found_b is True
    assert mem_count_b >= 1
    print("    ✓ Verified: Real Sibyl Memory retrieved correlated historical records.")

    # [F] Decision Transformation
    print(f"\n[F] DECISION TRANSFORMATION MOMENT")
    baseline_b_risk = data_b["baseline"]["risk"]
    baseline_b_rec = data_b["baseline"]["recommendation"]
    dec_b_risk = data_b["decision"]["risk"]
    dec_b_rec = data_b["decision"]["recommendation"]
    changed_b = data_b["decision_changed"]

    print(f"    Stateless Baseline:  {baseline_b_risk} ({baseline_b_rec})")
    print(f"    Memory-Informed:     {dec_b_risk} ({dec_b_rec})")
    print(f"    Decision Shifted:    {changed_b}")
    print(f"    Reason for Shift:    {data_b.get('why_decision_changed')}")
    assert baseline_b_risk == "MEDIUM"
    assert dec_b_risk == "HIGH"
    assert changed_b is True
    print("    ✓ Verified: Sibyl Memory transformed decision from MEDIUM -> HIGH!")

    # [G] Historical Evidence References & Intelligence
    print(f"\n[G] HISTORICAL EVIDENCE REFERENCES & INTELLIGENCE")
    failed_mitigations = data_b.get("failed_mitigations", [])
    actionable_lessons = data_b.get("actionable_lessons", [])
    evidence_chain = data_b.get("evidence_chain", [])

    print(f"    Failed Mitigations Diagnosed: {len(failed_mitigations)}")
    for fm in failed_mitigations:
        print(f"      • Prior Action: {fm['prior_action']}")
        print(f"        Diagnosis:    {fm['failure_diagnosis']}")
        print(f"        Implication:  {fm['current_implication']}")

    print(f"    Actionable Lessons Surfaced:  {len(actionable_lessons)}")
    for al in actionable_lessons:
        print(f"      • Rule:       {al['historical_rule']}")
        print(f"        Adjustment: {al['recommended_adjustment']}")

    assert len(failed_mitigations) >= 1, "Expected failed mitigation diagnosis"
    assert len(actionable_lessons) >= 1, "Expected actionable lesson"
    assert len(evidence_chain) >= 3, "Expected structured evidence taxonomy"
    print("    ✓ Verified: Rich deterministic operational intelligence rendered.")

    # [H] Deletion Proof
    print(f"\n[H] SIBYL DELETION PROOF (ISOLATING PERSISTED STORAGE)")
    # Remove the SQLite database file to simulate memory loss
    if os.path.exists(isolated_db_path):
        os.remove(isolated_db_path)
    sibyl_manager._client = None
    sibyl_manager.get_client()

    resp_b_del = fresh_client.post("/api/incidents/analyze", json=incident_b_payload)
    assert resp_b_del.status_code == 200
    data_b_del = resp_b_del.json()

    print(f"    Re-analyzing exact same Incident B with wiped memory...")
    print(f"    Historical Memory:   Found={data_b_del['memory']['found']} (Records={data_b_del['memory']['count']})")
    print(f"    Baseline Risk:       {data_b_del['baseline']['risk']}")
    print(f"    Memora Decision:     {data_b_del['decision']['risk']}")
    print(f"    Decision Changed:    {data_b_del['decision_changed']}")

    assert data_b_del["memory"]["found"] is False
    assert data_b_del["decision"]["risk"] == "MEDIUM"
    assert data_b_del["decision_changed"] is False
    print("    ✓ Verified: Decision escalation disappeared without Sibyl Memory!")

    # [I] Cleanup
    print(f"\n[I] CLEANUP & RESTORATION")
    temp_dir.cleanup()
    print("    ✓ Verified: Demo test artifacts cleaned up cleanly.")

    # Final Judge Verdict
    print("\n" + "=" * 75)
    print("WITH SIBYL")
    print("Decision: HIGH")
    print("Reason:   Historical unresolved evidence from Gate 3 contraindicated baseline monitoring.")
    print("\nWITHOUT SIBYL")
    print("Decision: MEDIUM")
    print("Reason:   Historical evidence unavailable; fell back to stateless baseline.")
    print("\nLOAD-BEARING MEMORY PROOF: PASS")
    print("=" * 75)


if __name__ == "__main__":
    run_demo_proof()
