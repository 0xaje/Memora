# MEMORA — API Contract Specification (Phase 1.75 Frozen)

This document specifies the exact, frozen HTTP API contract for **Memora**, an AI operational memory agent built for physical and perimeter security operations teams.

The frontend client communicates strictly with **Memora's domain API**. It does not require any knowledge of internal SQLite schemas, file paths, or the Sibyl SDK.

---

## 1. Overview & General Invariants

* **Base URL**: `http://localhost:8000` (development default)
* **Transport**: HTTP/1.1 JSON (REST)
* **Authentication**: None in Phase 1 (deliberately deferred; do not add simulated tokens)
* **CORS**: Configured for local development origins (`http://localhost:3000`, `http://localhost:5173`, `http://127.0.0.1:3000`, `http://127.0.0.1:5173`)
* **Identifiers**:
  - Incident ID: `INC-<8-char-hex>` (e.g. `INC-8FE28CA8`)
  - Decision ID: `DEC-<incident-id>` (e.g. `DEC-INC-8FE28CA8`)
  - Outcome ID: `OUT-<8-char-hex>` (e.g. `OUT-9F31C8D2`)
  - Lesson ID: `LES-<incident-id>` (e.g. `LES-INC-8FE28CA8`)
  - Risk ID: `RISK-<incident-id>` (e.g. `RISK-INC-8FE28CA8`)
* **Timestamps**: Timezone-aware ISO 8601 strings (UTC, e.g. `2026-09-02T11:20:43.271Z`).

---

## 2. Endpoints

### A. Health Check
`GET /health`

Communicates operational health and connection to real Sibyl Memory storage.

#### Request
No parameters or headers required.

#### Response (`200 OK`)
```json
{
  "status": "healthy",
  "sibyl_memory_connected": true,
  "version": "0.1.0"
}
```

---

### B. Operational Memory Status
`GET /api/memory/status`

Provides operational status, tenant configuration, and storage tier row counts.
**Security Note**: Does NOT expose database file paths or internal credentials.

#### Query Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `tenant_id` | `string` | Optional | Tenant UUID to inspect (defaults to configured system tenant) |

#### Response (`200 OK`)
```json
{
  "status": "connected",
  "backend": "Sibyl Memory (SQLite FTS5)",
  "storage_state": "healthy",
  "tenant_id": "00000000-0000-0000-0000-000000000001",
  "tier": "free",
  "counts": {
    "entities_warm": 14,
    "journal_cold": 8,
    "reference": 0
  },
  "logical_size_bytes": 49152
}
```

---

### C. Incident Intake & Analysis (Critical Endpoint)
`POST /api/incidents/analyze`

The primary operational endpoint. Ingests raw incident observations, extracts facts, retrieves historical memory from Sibyl, executes baseline evaluation, computes historical comparison, produces a memory-informed decision, and records the event into the cold audit journal.

#### Request Body
```json
{
  "raw_text": "Suspicious delivery vehicle observed again near Gate 3.",
  "location": "Gate 3",
  "incident_type": "suspicious_vehicle",
  "reported_by": "guard_shift_morning",
  "session_id": "sess_102",
  "tenant_id": "00000000-0000-0000-0000-000000000001",
  "memory_enabled": true
}
```

#### Request Fields
* `raw_text` (*string, required, length: 5–2000*): Incident log or observation text. Cannot be whitespace-only.
* `location` (*string, optional*): Explicit facility location (e.g. `"Gate 3"`). If omitted, extracted via deterministic NER patterns.
* `incident_type` (*string, optional*): Explicit incident category. If omitted, inferred from detected entities.
* `reported_by` (*string, optional, default: `"field_operator"`*): Sensor, camera, or guard identifier.
* `session_id` (*string, optional*): Client session identifier.
* `tenant_id` (*string, optional*): Tenant UUID for partition isolation.
* `memory_enabled` (*boolean, optional, default: `true`*): Toggle for load-bearing memory retrieval vs baseline.

#### Response Structure (`200 OK`)
```json
{
  "incident": {
    "incident_id": "INC-A29C0096",
    "location": "Gate 3",
    "incident_type": "suspicious_vehicle",
    "summary": "Suspicious delivery vehicle observed again near Gate 3.",
    "indicators": ["repeat occurrence", "suspicious activity"],
    "entities_involved": ["delivery vehicle"],
    "timestamp": "2026-09-02T11:07:58.210452Z"
  },
  "session": {
    "id": "sess_102",
    "is_fresh": true
  },
  "baseline": {
    "risk": "MEDIUM",
    "recommendation": "MONITOR_AND_VERIFY",
    "confidence": 0.75,
    "factors": [
      "Single observation of suspicious delivery vehicle near facility access point.",
      "Standard security protocol: verify credentials and monitor area."
    ]
  },
  "decision": {
    "risk": "HIGH",
    "recommendation": "ESCALATE_TO_SUPERVISOR",
    "changed": true,
    "confidence": 0.92,
    "escalation_reason": "Recurrence detected at Gate 3 with unresolved prior incident. Prior low-level action (MONITOR_AND_VERIFY) failed to eliminate the hazard."
  },
  "decision_changed": true,
  "decision_change": {
    "from_risk": "MEDIUM",
    "to_risk": "HIGH",
    "from_recommendation": "MONITOR_AND_VERIFY",
    "to_recommendation": "ESCALATE_TO_SUPERVISOR"
  },
  "memory": {
    "found": true,
    "count": 3,
    "records": [
      {
        "category": "incidents",
        "id": "INC-B6E50E46",
        "location": "Gate 3",
        "summary": "Suspicious delivery vehicle observed near Gate 3.",
        "status": "unresolved",
        "timestamp": "2026-09-02T11:07:56.104231Z"
      },
      {
        "category": "unresolved_risks",
        "id": "RISK-INC-B6E50E46",
        "location": "Gate 3",
        "summary": "Unresolved: Vehicle returned without manifest; driver evaded checkpoint. (Reason: Ongoing threat)",
        "status": "open",
        "timestamp": "2026-09-02T11:07:56.120932Z"
      },
      {
        "category": "operational_lessons",
        "id": "LES-INC-B6E50E46",
        "location": "Gate 3",
        "summary": "Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3.",
        "status": "active",
        "action_taken": "MONITOR_AND_VERIFY",
        "rule_or_insight": "Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3.",
        "recurrence_count": 1,
        "successful_mitigation": null,
        "timestamp": "2026-09-02T11:07:56.125192Z"
      }
    ]
  },
  "inference": {
    "is_recurrent": true,
    "recurrence_count": 1,
    "unresolved_history": true,
    "unresolved_incident_ids": ["INC-B6E50E46"],
    "has_prior_failed_outcome": true,
    "failed_prior_actions": ["MONITOR_AND_VERIFY"],
    "verified_mitigations": [],
    "applicable_lessons": ["Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3."],
    "summary": "Identified 1 prior incident(s) at Gate 3. Found active unresolved prior incident(s): INC-B6E50E46. Prior mitigation (MONITOR_AND_VERIFY) did not resolve the recurring issue. Operational lesson applies: Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3."
  },
  "why_decision_changed": "Baseline evaluation without memory produced MEDIUM risk and 'MONITOR_AND_VERIFY'. However, Sibyl Memory revealed related unresolved case(s) [INC-B6E50E46]. Prior action (MONITOR_AND_VERIFY) proved insufficient to eliminate the hazard. Consequently, operational risk was escalated to HIGH and recommendation changed to 'ESCALATE_TO_SUPERVISOR'.",
  "provenance": {
    "facts": "Observation at Gate 3: 'Suspicious delivery vehicle observed again near Gate 3.'. Identified entities: delivery vehicle. Indicators: repeat occurrence, suspicious activity.",
    "retrieval": "Retrieved 3 records from Sibyl Memory: 1 incident(s) (INC-B6E50E46), 1 open risk(s), 1 operational lesson(s).",
    "inference": "Identified 1 prior incident(s) at Gate 3. Found active unresolved prior incident(s): INC-B6E50E46. Prior mitigation (MONITOR_AND_VERIFY) did not resolve the recurring issue. Operational lesson applies: Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3.",
    "decision_shift": "Baseline evaluation without memory produced MEDIUM risk and 'MONITOR_AND_VERIFY'. However, Sibyl Memory revealed related unresolved case(s) [INC-B6E50E46]. Prior action (MONITOR_AND_VERIFY) proved insufficient to eliminate the hazard. Consequently, operational risk was escalated to HIGH and recommendation changed to 'ESCALATE_TO_SUPERVISOR'."
  }
}
```

---

### D. Record Incident Outcome
`POST /api/outcomes`

Submits follow-up operational actions and observed outcomes.
- If `is_resolved: false`: records an active `UnresolvedRiskMemory`, increments `recurrence_count`, and synthesizes/updates an `OperationalLesson`.
- If `is_resolved: true`: closes active unresolved risks (`status="mitigated"`), updates the operational lesson with the confirmed `successful_mitigation`, and marks the incident resolved.

#### Request Body
```json
{
  "incident_id": "INC-A29C0096",
  "action_taken": "ESCALATE_TO_SUPERVISOR",
  "observed_result": "Supervisor escorted vehicle off premises and issued formal trespass notice.",
  "is_resolved": true,
  "operational_lesson": "Supervisor dispatch with trespass warning successfully eliminated repeat loitering at Gate 3.",
  "tenant_id": "00000000-0000-0000-0000-000000000001"
}
```

#### Response (`200 OK`)
```json
{
  "status": "success",
  "outcome_id": "OUT-F4A19B22",
  "incident_id": "INC-A29C0096",
  "is_resolved": true,
  "action_taken": "ESCALATE_TO_SUPERVISOR",
  "observed_result": "Supervisor escorted vehicle off premises and issued formal trespass notice.",
  "unresolved_reason": null,
  "lesson_id": "LES-INC-A29C0096",
  "lesson_rule": "Confirmed resolution: 'ESCALATE_TO_SUPERVISOR' successfully resolved the incident.",
  "recurrence_count": null,
  "successful_mitigation": "ESCALATE_TO_SUPERVISOR",
  "message": "Outcome and operational learning persisted to Sibyl Memory."
}
```

---

### E. Memory Search
`GET /api/memory/search?q={query}&tenant_id={tenant_id}`

Direct full-text cross-tier search across Sibyl Memory (entities, journal, reference documents).

#### Query Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `q` | `string` | **Yes** | Search keyword (length: 1–200 characters, non-whitespace) |
| `tenant_id` | `string` | Optional | Tenant UUID for partition isolation |

#### Response (`200 OK`)
```json
{
  "query": "Gate 3",
  "tenant_id": "00000000-0000-0000-0000-000000000001",
  "count": 3,
  "results": [
    {
      "id": "INC-B6E50E46",
      "tier": "entity",
      "category": "incidents",
      "location": "Gate 3",
      "summary": "Suspicious delivery vehicle observed near Gate 3.",
      "status": "unresolved",
      "timestamp": "2026-09-02T11:07:56.104231Z",
      "score": -1.25e-06
    }
  ]
}
```

---

## 3. Standardized Error Contract

All API errors conform to the standard error envelope:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of what went wrong."
  }
}
```

### Standard Error Codes
| HTTP Status | Error Code | Description |
| :--- | :--- | :--- |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | Malformed payload, empty string, or out-of-range value. |
| `503 Service Unavailable` | `SIBYL_UNAVAILABLE` | Real Sibyl storage failure, unwritable path, or connection error. |
| `503 Service Unavailable` | `SIBYL_SERVICE_ERROR` | Search query or cross-tier retrieval failure. |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | Unexpected server execution error. |
