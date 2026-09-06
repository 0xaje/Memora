# Memora API Integration Guide

This document specifies the REST integration between the Memora React Operations Console and the authoritative FastAPI backend.

---

## 1. Environment Configuration

The frontend discovers the backend through the `VITE_MEMORA_API_URL` environment variable.

| Variable | Default Value | Description |
|---|---|---|
| `VITE_MEMORA_API_URL` | `http://localhost:8000` | Base URL of the running Memora FastAPI service |

Set this in `frontend/.env` if connecting to an alternative host or port.

---

## 2. Consumed REST Endpoints

The console consumes five core endpoints:

### 1. System Health
- **Endpoint**: `GET /health`
- **Purpose**: System liveness and Sibyl Memory connectivity status.
- **Response**:
  ```json
  {
    "status": "healthy",
    "sibyl_memory_connected": true,
    "version": "0.1.0"
  }
  ```

### 2. Memory Status
- **Endpoint**: `GET /api/memory/status`
- **Purpose**: Operational status of the underlying Sibyl Memory storage engine.
- **Response**:
  ```json
  {
    "status": "connected",
    "backend": "sqlite",
    "storage_state": "available",
    "tenant_id": "00000000-0000-0000-0000-000000000001",
    "counts": { "incidents": 12, "outcomes": 8, "lessons": 4 },
    "logical_size_bytes": 1048576
  }
  ```

### 3. Analyze Incident
- **Endpoint**: `POST /api/incidents/analyze`
- **Purpose**: Ingests new incident text, retrieves historical Sibyl memory, computes baseline vs memory-informed decision, persists incident facts, and returns complete audit provenance.
- **Request Payload**:
  ```json
  {
    "raw_text": "Suspicious delivery vehicle observed again near Gate 3.",
    "location": "Gate 3",
    "incident_type": "suspicious_vehicle",
    "reported_by": "field_operator",
    "session_id": "sess-live-01",
    "tenant_id": "00000000-0000-0000-0000-000000000001"
  }
  ```
- **Response**:
  ```json
  {
    "incident": {
      "incident_id": "INC-20260906-0001",
      "location": "Gate 3",
      "incident_type": "suspicious_vehicle",
      "summary": "Suspicious delivery vehicle observed again near Gate 3.",
      "indicators": ["vehicle", "gate 3"],
      "entities_involved": ["delivery vehicle"],
      "timestamp": "2026-09-06T02:15:00Z"
    },
    "session": { "id": "sess-live-01", "is_fresh": true },
    "baseline": {
      "risk": "MEDIUM",
      "recommendation": "MONITOR_AND_VERIFY",
      "confidence": 0.85,
      "factors": ["unverified observation"]
    },
    "decision": {
      "risk": "HIGH",
      "recommendation": "ESCALATE_TO_SUPERVISOR",
      "changed": true,
      "confidence": 0.92,
      "escalation_reason": "Prior unresolved incident at Gate 3 recurred."
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
      "count": 1,
      "records": [
        {
          "category": "incident",
          "id": "INC-20260906-0000",
          "location": "Gate 3",
          "summary": "Suspicious delivery vehicle observed near Gate 3.",
          "status": "unresolved",
          "timestamp": "2026-09-06T01:45:00Z"
        }
      ]
    },
    "inference": {
      "is_recurrent": true,
      "recurrence_count": 1,
      "unresolved_history": true,
      "summary": "Recurring suspicious vehicle activity at Gate 3 with unresolved prior monitoring.",
      "applicable_lessons": []
    },
    "why_decision_changed": "Previous similar activity remained unresolved after monitoring. The recurrence increased the operational risk, so Memora escalated the recommendation.",
    "provenance": {
      "facts": "Location: Gate 3 | Observation: delivery vehicle",
      "retrieval": "1 related incident retrieved from Sibyl Memory tier",
      "inference": "Pattern: recurring unresolved anomaly at Gate 3",
      "decision_shift": "Shifted baseline MONITOR_AND_VERIFY to ESCALATE_TO_SUPERVISOR"
    }
  }
  ```

### 4. Record Outcome
- **Endpoint**: `POST /api/outcomes`
- **Purpose**: Persists operational resolution or failure of an incident and updates operational learning in Sibyl Memory.
- **Request Payload**:
  ```json
  {
    "incident_id": "INC-20260906-0001",
    "action_taken": "Dispatched supervisor and secured gate log",
    "observed_result": "Driver identified and unauthorized access prevented",
    "is_resolved": true,
    "operational_lesson": "Supervisor escalation prevented unauthorized entry at Gate 3"
  }
  ```
- **Response**:
  ```json
  {
    "status": "recorded",
    "outcome_id": "OUT-20260906-0001",
    "incident_id": "INC-20260906-0001",
    "is_resolved": true,
    "action_taken": "Dispatched supervisor and secured gate log",
    "observed_result": "Driver identified and unauthorized access prevented",
    "lesson_id": "LES-20260906-0001",
    "lesson_rule": "Supervisor escalation prevented unauthorized entry at Gate 3",
    "recurrence_count": 1,
    "successful_mitigation": "Dispatched supervisor and secured gate log",
    "message": "Operational outcome and organizational lesson successfully recorded in Sibyl Memory."
  }
  ```

### 5. Memory Search
- **Endpoint**: `GET /api/memory/search?q={query}`
- **Purpose**: Direct full-text keyword search across historical incidents, outcomes, and lessons stored in Sibyl Memory.
- **Response**:
  ```json
  {
    "query": "Gate 3",
    "count": 2,
    "results": [
      {
        "category": "incident",
        "id": "INC-20260906-0000",
        "location": "Gate 3",
        "summary": "Suspicious delivery vehicle observed near Gate 3.",
        "status": "unresolved",
        "timestamp": "2026-09-06T01:45:00Z"
      }
    ]
  }
  ```

---

## 3. Error Contract & Handling

All API errors return standardized JSON envelopes:
```json
{
  "detail": {
    "code": "SIBYL_UNAVAILABLE",
    "message": "Sibyl Memory storage error: database locked or unavailable"
  }
}
```

Standardized Error Codes:
- `VALIDATION_ERROR` (HTTP 422): Input field constraint violated (e.g. empty raw_text).
- `SIBYL_UNAVAILABLE` (HTTP 503): Sibyl memory client failure or unwritable disk.
- `INTERNAL_SERVER_ERROR` (HTTP 500): Unhandled exception in backend.
- `NETWORK_ERROR` (Client-side): Backend process offline or unreachable.
- `MALFORMED_RESPONSE` (Client-side): Non-JSON or invalid payload received.
