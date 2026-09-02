# MEMORA — Frontend Integration Guide (Phase 2 Ready)

This guide provides the exact instructions for building the **Memora UI** against the existing Python backend.

You do **NOT** need to understand Sibyl Memory internals, SQLite tables, or Python classes to build the frontend. Everything is exposed cleanly through REST endpoints.

---

## 1. Quickstart & Local Backend Setup

### Running the Backend
From the project root:
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the FastAPI server
PYTHONPATH=. uvicorn memora.api.app:app --host 0.0.0.0 --port 8000 --reload
```

* **Backend Base URL**: `http://localhost:8000`
* **Swagger / OpenAPI Documentation**: `http://localhost:8000/docs`
* **Health Check**: `http://localhost:8000/health`
* **CORS**: Configured out-of-the-box for `http://localhost:3000`, `http://localhost:5173`, and `http://127.0.0.1:5173`.

---

## 2. Recommended Frontend UI Components

The Memora UI represents a **physical security operations dispatch console**. The following components map directly to the API response fields:

### A. The "Memory Changed This Decision" Banner
When an incoming incident's assessment is altered by historical memory, display a prominent indicator:
```typescript
if (response.decision_changed) {
  // Render high-visibility banner
  // "MEMORY-INFORMED ESCALATION DETECTED"
  // Show from -> to transition:
  // response.decision_change.from_risk -> response.decision_change.to_risk
  // response.decision_change.from_recommendation -> response.decision_change.to_recommendation
}
```

### B. Baseline vs. Final Decision Comparison Card
Side-by-side comparison illustrating why memory is load-bearing:
* **Left Column (Current Observation Alone)**:
  - Risk Badge: `response.baseline.risk` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
  - Recommendation: `response.baseline.recommendation`
  - Observation Factors: `response.baseline.factors`
* **Right Column (Memory-Informed Decision)**:
  - Final Risk Badge: `response.decision.risk`
  - Final Recommendation: `response.decision.recommendation`
  - Escalation Reason: `response.decision.escalation_reason`

### C. "Why Decision Changed" Rationale Box
Directly display `response.why_decision_changed`. This provides a complete, clear operational explanation justifying the shift.

### D. Historical Memory Timeline / Evidence Drawer
Render the cards inside `response.memory.records`:
* **Category Badge**: `rec.category` (`incidents`, `unresolved_risks`, `operational_lessons`, `outcomes`)
* **ID**: `rec.id` (e.g. `INC-B6E50E46`)
* **Status**: `rec.status` (`unresolved`, `open`, `mitigated`, `active`)
* **Summary**: `rec.summary`
* **Dynamic Recurrence / Mitigation**:
  - If `rec.recurrence_count > 1`: display *"Recurrence: {rec.recurrence_count} times"*
  - If `rec.successful_mitigation`: display *"Verified Effective Mitigation: {rec.successful_mitigation}"*

### E. Provenance & Audit Trail
Display the 4 provenance stages from `response.provenance`:
1. **Facts**: `response.provenance.facts`
2. **Retrieval**: `response.provenance.retrieval`
3. **Inference**: `response.provenance.inference`
4. **Decision Shift**: `response.provenance.decision_shift`

---

## 3. End-to-End User Flow for Demo or Review

To demonstrate the load-bearing memory loop in the UI:

### Step 1: Submit Initial Incident (Session 1)
Make a POST request to `/api/incidents/analyze`:
```json
{
  "raw_text": "Suspicious delivery vehicle observed near Gate 3.",
  "location": "Gate 3"
}
```
* **UI Behavior**:
  - Baseline Risk is `MEDIUM`, Recommendation is `MONITOR_AND_VERIFY`.
  - `decision_changed` is `false` (no prior history exists yet).
  - Note the returned `incident.incident_id` (e.g. `INC-001`).

### Step 2: Record Follow-Up Outcome
Operator selects the incident and records what occurred:
Make a POST request to `/api/outcomes`:
```json
{
  "incident_id": "INC-001",
  "action_taken": "MONITOR_AND_VERIFY",
  "observed_result": "Driver was evasive; vehicle departed without manifest.",
  "is_resolved": false,
  "unresolved_reason": "Vehicle returned during subsequent patrol cycle",
  "operational_lesson": "Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3."
}
```
* **UI Behavior**:
  - Confirm banner: *"Outcome persisted. Active risk recorded and operational lesson synthesized in Sibyl Memory."*

### Step 3: Ingest Related Incident in Fresh Session
Operator enters a new observation:
Make a POST request to `/api/incidents/analyze`:
```json
{
  "raw_text": "Suspicious delivery vehicle observed again near Gate 3.",
  "location": "Gate 3"
}
```
* **UI Behavior**:
  - `decision_changed` is now **`true`**!
  - Risk jumps to **`HIGH`**, Recommendation escalates to **`ESCALATE_TO_SUPERVISOR`**.
  - The Memory Timeline displays the unresolved incident and prior failed action.
  - "Why Decision Changed" clearly states:
    > *"Baseline produced MEDIUM risk ('MONITOR_AND_VERIFY'). However, Sibyl Memory revealed related unresolved cases and demonstrated that prior monitoring did not resolve the threat. Consequently, operational risk was escalated to HIGH and recommendation changed to 'ESCALATE_TO_SUPERVISOR'."*

---

## 4. Error Handling in UI

All error responses from the backend follow this schema:
```json
{
  "detail": {
    "code": "SIBYL_UNAVAILABLE",
    "message": "Sibyl Memory storage failure: SQLite disk I/O error"
  }
}
```

Handle HTTP status codes as follows:
* **422**: Show field validation error (e.g. "Incident text cannot be empty").
* **503**: Show service alert: "Memora operational memory unavailable. Check backend storage."
* **500**: Show general error: "Unexpected system error."
