#!/usr/bin/env bash
set -e

# MEMORA — Multi-Process Cold-Start Fresh Session Proof
# Strictly adheres to Phase 1.5 Requirement 4:
# "Verify cold-start recall using a new process, not merely a new object."

DB_PATH="/tmp/memora_cold_start_proof.db"
rm -f "$DB_PATH"

echo "=================================================================="
echo "COLD-START FRESH PROCESS PROOF (SEPARATE OS PROCESSES)"
echo "Database location: $DB_PATH"
echo "=================================================================="

echo ""
echo ">>> RUNNING PROCESS A: Incident Intake & Unresolved Outcome..."
PYTHONPATH=. .venv/bin/python - <<EOF
import sys
from memora.memory.client import SibylClientManager
from memora.incidents.service import IncidentService
from memora.incidents.models import IncidentCreate, OutcomeCreate

manager = SibylClientManager(db_path="$DB_PATH")
service = IncidentService(client_manager=manager)

# Ingest Session A Incident
res = service.analyze_incident(IncidentCreate(
    raw_text="Suspicious delivery vehicle observed near Gate 3.",
    location="Gate 3"
))
inc_id = res.incident.incident_id
print(f"[Process A] Incident created: {inc_id} at {res.incident.location}")
print(f"[Process A] Baseline Risk: {res.baseline_assessment.risk.value}, Recommendation: {res.baseline_assessment.recommendation.value}")

# Record outcome as unresolved
service.record_outcome(OutcomeCreate(
    incident_id=inc_id,
    action_taken="MONITOR_AND_VERIFY",
    observed_result="Vehicle returned without manifest; driver evaded checkpoint.",
    is_resolved=False,
    operational_lesson="Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3."
))
print(f"[Process A] Outcome recorded as UNRESOLVED and lesson saved.")
manager.close()
sys.exit(0)
EOF

EXIT_CODE_A=$?
if [ $EXIT_CODE_A -ne 0 ]; then
    echo "Process A failed!"
    exit 1
fi

echo ">>> PROCESS A TERMINATED COMPLETELY."
echo ">>> Process memory wiped. Operating system environment reset."
echo ""

echo ">>> STARTING PROCESS B (GENUINELY FRESH OS PROCESS)..."
PYTHONPATH=. .venv/bin/python - <<EOF
import sys
from memora.memory.client import SibylClientManager
from memora.incidents.service import IncidentService
from memora.incidents.models import IncidentCreate

# Genuinely fresh process instance - NO prior objects in RAM
manager = SibylClientManager(db_path="$DB_PATH")
service = IncidentService(client_manager=manager)

print("[Process B] Starting cold-start evaluation for related incident...")
res = service.analyze_incident(IncidentCreate(
    raw_text="Suspicious delivery vehicle observed again near Gate 3.",
    location="Gate 3"
))

print(f"[Process B] Extracted Incident ID: {res.incident.incident_id}")
print(f"[Process B] Records retrieved from Sibyl: {res.memory_influence.retrieval_count}")
print(f"[Process B] Baseline Risk (Without Memory): {res.baseline_assessment.risk.value}")
print(f"[Process B] Memory-Informed Risk: {res.memory_assessment.risk.value}")
print(f"[Process B] Baseline Recommendation: {res.baseline_assessment.recommendation.value}")
print(f"[Process B] Memory-Informed Recommendation: {res.memory_assessment.recommendation.value}")
print(f"[Process B] Decision Changed?: {res.memory_assessment.changed}")

assert res.memory_assessment.changed is True, "Decision MUST change due to persistent memory!"
assert res.memory_assessment.risk.value == "HIGH", "Risk MUST escalate to HIGH!"
assert res.memory_assessment.recommendation.value == "ESCALATE_TO_SUPERVISOR", "Recommendation MUST escalate!"
assert res.memory_influence.retrieval_count >= 1, "Must retrieve prior records!"

manager.close()
print("\n>>> [Process B] COLD-START PROOF PASSED! Memory successfully bridged the process boundary.")
sys.exit(0)
EOF

EXIT_CODE_B=$?
if [ $EXIT_CODE_B -ne 0 ]; then
    echo "Process B failed!"
    exit 1
fi

rm -f "$DB_PATH"
echo ""
echo "=================================================================="
echo "MULTI-PROCESS VERIFICATION COMPLETE: ALL CHECKS PASSED!"
echo "=================================================================="
