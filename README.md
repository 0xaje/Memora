# MEMORA — AI Operational Memory Agent for Security Operations

MEMORA is an AI operational memory agent designed for physical and perimeter security operations teams.
It solves a critical security vulnerability: **shift-to-shift knowledge loss**, ensuring that recurring threats, unmitigated risks, and historical operational lessons inform future security decisions.

> **Core Product Principle:**
> *"What happened before changes what Memora does now."*

---

## 1. Architecture Overview

MEMORA is engineered with a **load-bearing memory architecture** powered by **Sibyl Memory** (`sibyl-memory-client` v0.8.0, SQLite + FTS5).

```
                      ┌────────────────────────────────────────┐
                      │          Incoming Incident             │
                      │  "Suspicious delivery vehicle near..." │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │        Operational Fact Extractor      │
                      │   (Location, Entities, Indicators)     │
                      └──────────────────┬─────────────────────┘
                                         │
                   ┌─────────────────────┴──────────────────────┐
                   │                                            │
                   ▼                                            ▼
       ┌────────────────────────┐                  ┌────────────────────────┐
       │   Baseline Evaluator   │                  │  Sibyl Memory Retrieve │
       │  (Current Facts Only)  │                  │  (Warm Entities, Cold) │
       └───────────┬────────────┘                  └────────────┬───────────┘
                   │                                            │
                   └─────────────────────┬──────────────────────┘
                                         ▼
                      ┌────────────────────────────────────────┐
                      │       Historical Pattern Engine        │
                      │  (Recurrence, Unresolved, Past Lessons)│
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │   Load-Bearing Decision Engine         │
                      │  Baseline: MEDIUM / MONITOR            │
                      │  Memory:   HIGH / ESCALATE             │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │     Persist Operational Knowledge      │
                      │     (WARM entities, COLD journal)      │
                      └────────────────────────────────────────┘
```

### The 5 Memory Categories
Memora models operational knowledge into 5 active categories:
1. **INCIDENT MEMORY (`incidents`)**: Structured observations, locations, timestamps, involved entities, and status.
2. **DECISION MEMORY (`decisions`)**: Baseline vs. memory-informed risks, recommendations, and justification.
3. **OUTCOME MEMORY (`outcomes`)**: Physical actions taken and subsequent observations.
4. **UNRESOLVED RISK MEMORY (`unresolved_risks`)**: Persistent gaps, unresolved threats, and active hazards.
5. **OPERATIONAL LEARNING (`operational_lessons`)**: Synthesized operational rules (e.g., *"Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3"*).

---

## 2. Sibyl Integration Points

The integration with Sibyl Memory is strictly modular and auditable in under 2 minutes:

| File | Purpose | Sibyl API Used |
| :--- | :--- | :--- |
| [`memora/memory/client.py`](file:///home/oyeolorun/Memora/memora/memory/client.py) | Client initialization & connection lifecycle | `MemoryClient.local(path, tenant_id, tier)` |
| [`memora/memory/writer.py`](file:///home/oyeolorun/Memora/memora/memory/writer.py) | Real persistence across tiers | `client.set_entity(...)` (WARM), `client.write_event(...)` (COLD journal) |
| [`memora/memory/retriever.py`](file:///home/oyeolorun/Memora/memora/memory/retriever.py) | Full-text search & cross-tier query | `client.search_entities(query, category)` & `client.search(query)` |
| [`memora/intelligence/decision_engine.py`](file:///home/oyeolorun/Memora/memora/intelligence/decision_engine.py) | Memory-informed decision path | Evaluates retrieved history to drive risk escalation & recommendation changes |

---

## 3. Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `SIBYL_DB_PATH` | Path to Sibyl SQLite database file | `~/.sibyl-memory/memora.db` |
| `SIBYL_TENANT_ID` | UUID for tenant isolation | `00000000-0000-0000-0000-000000000001` |
| `SIBYL_TIER` | Sibyl licensing tier | `free` |
| `PORT` | API server port | `8000` |
| `LOG_LEVEL` | Application logging verbosity | `INFO` |

---

## 4. Quickstart & Local Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.13)

### Installation
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API Server
```bash
PYTHONPATH=. uvicorn memora.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be available at: `http://localhost:8000/docs`

---

## 5. API Endpoints

### 1. Ingest & Analyze Incident
- **`POST /api/incidents/analyze`**
- **Payload:**
  ```json
  {
    "raw_text": "Suspicious delivery vehicle observed again near Gate 3.",
    "location": "Gate 3",
    "memory_enabled": true
  }
  ```
- **Response Structure:**
  ```json
  {
    "incident": { "incident_id": "INC-8FE28CA8", "location": "Gate 3", "incident_type": "suspicious_vehicle" },
    "session": { "id": "sess_001", "is_fresh": true },
    "baseline_assessment": { "risk": "MEDIUM", "recommendation": "MONITOR_AND_VERIFY" },
    "memory_assessment": { "risk": "HIGH", "recommendation": "ESCALATE_TO_SUPERVISOR", "changed": true },
    "memory_influence": {
      "related_incidents": [...],
      "unresolved_risks": [...],
      "operational_lessons": [...],
      "retrieval_count": 3
    },
    "explanation": {
      "what_happened": "Observation at Gate 3...",
      "what_was_retrieved": "Retrieved 3 records from Sibyl Memory...",
      "what_pattern_was_inferred": "Found active unresolved prior incident(s)...",
      "why_decision_changed": "Baseline produced MEDIUM risk and 'MONITOR_AND_VERIFY'. However, Sibyl Memory revealed related unresolved cases..."
    }
  }
  ```

### 2. Record Incident Outcome
- **`POST /api/outcomes`**
- **Payload:**
  ```json
  {
    "incident_id": "INC-8FE28CA8",
    "action_taken": "MONITOR_AND_VERIFY",
    "observed_result": "Similar suspicious activity occurred again.",
    "is_resolved": false,
    "unresolved_reason": "Vehicle returned during subsequent patrol cycle",
    "operational_lesson": "Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3."
  }
  ```

### 3. Sibyl Memory Status & Search
- **`GET /api/memory/status`**: Inspects connection status, database file path, and tier counts (`entities_warm`, `journal_cold`, `reference_documents`).
- **`GET /api/memory/search?q=Gate 3`**: Direct cross-tier search against Sibyl Memory.

---

## 6. Fresh-Session Recall Proof

To verify the load-bearing memory loop across fresh sessions:

```bash
PYTHONPATH=. python scripts/run_proof.py
```

This executable demonstration runs the exact constitutional test:
1. **Session A**: Ingests `"Suspicious delivery vehicle observed near Gate 3."` $\to$ Evaluates baseline (`MEDIUM` / `MONITOR_AND_VERIFY`) $\to$ Writes to Sibyl Memory.
2. **Outcome**: Records unresolved follow-up $\to$ Persists `UnresolvedRiskMemory` and `OperationalLesson` into Sibyl.
3. **Session B (Genuinely Fresh)**: Completely clean process instance without in-memory state.
4. **Session B Ingest**: Ingests `"Suspicious delivery vehicle observed again near Gate 3."`
5. **Sibyl Recall**: Retrieves Session A's unresolved incident and operational lesson.
6. **Decision Escalation**: Risk escalates to `HIGH` and recommendation changes to `ESCALATE_TO_SUPERVISOR`.
7. **Audit Explanation**: Displays the full audit trail detailing *why* the decision changed.

---

## 7. Deletion Test Procedure

To verify that Sibyl Memory is truly load-bearing and not cosmetic:

```bash
PYTHONPATH=. python scripts/test_deletion_proof.py
```

This demonstrates side-by-side:
- **Case A (With Sibyl Memory)**: Escalates to `HIGH` risk and `ESCALATE_TO_SUPERVISOR`.
- **Case B (Without Sibyl Memory)**: Remains at baseline `MEDIUM` risk and `MONITOR_AND_VERIFY`.
- Demonstrates that removing historical memory naturally causes the agent to lose its repeat-pattern detection capability.

---

## 8. Test Suite Verification

Run the full automated pytest suite:

```bash
PYTHONPATH=. pytest -v tests/
```
All 9 automated unit, integration, and deletion tests pass cleanly.
