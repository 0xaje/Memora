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

### Backend Setup (FastAPI & Sibyl Memory)
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
PYTHONPATH=. uvicorn memora.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation is available at: `http://localhost:8000/docs`

### Frontend Setup (Operations Console)
```bash
cd frontend
pnpm install
pnpm dev
```
The Operations Console will be available at: `http://localhost:5173`

---

## 5. Official 3-Minute Hackathon Demo & Proof Scripts

### 1. Automated Judge Verification Script (9-Step E2E Proof)
Run the standalone, end-to-end verification script proving cold-start recall, decision shift (`MEDIUM` → `HIGH`), and the deletion test:
```bash
PYTHONPATH=. .venv/bin/python scripts/verify_memora_demo.py
```
> See [`docs/DEMO_RUNBOOK.md`](docs/DEMO_RUNBOOK.md) for the live 3-minute presentation script.

### 2. Multi-Process Cold-Start Proof (Separate OS Processes)
To verify that Sibyl Memory bridges completely independent operating system processes:
```bash
bash scripts/run_cold_start_process_proof.sh
```

### 3. Deletion Test Procedure
To verify that Sibyl Memory is truly load-bearing and that decisions revert when memory is isolated:
```bash
PYTHONPATH=. .venv/bin/python scripts/test_deletion_proof.py
```

---

---

## 6. Full Verification Test Suites

### Backend Test Suite (29 Passing Tests)
```bash
.venv/bin/pytest -v
```
Covers API contracts, validation, failure modes, tenant isolation, adversarial boundaries, load-bearing proofs, license plate extraction, location hierarchy sector inheritance, shift handover reports, legal audit SHA-256 export, and Sibyl tier escalation.

### Frontend Test Suite (17 Passing Tests across 6 Suites)
```bash
cd frontend && pnpm test
```
Covers API client contracts, live state transitions, UI rendering, and mock-free error handling.

---

## 7. Advanced Capabilities (Phase 6)

1. **Browser-Native Voice Incident Dictation**:
   - Uses the browser's native Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`) with zero external API key requirements.
   - Real-time streaming transcription directly into the incident description intake with active recording pulse indicators.

2. **24-Hour Shift Handover Digest (`GET /api/reports/shift-handover`)**:
   - Instantly compiles an actionable briefing across active incidents, unresolved threats, failed mitigations to avoid repeating, and operational lessons from Sibyl Memory.

3. **Multi-Facility Tenant Partitioning**:
   - Supports seamless switching between facility partitions (`Facility Alpha: Perimeter HQ`, `Facility Beta: Logistics Docks`, `Facility Gamma: Secure Core`) with strict cross-tenant isolation.

4. **Cryptographic Legal Audit Export (`GET /api/audit/export`)**:
   - Generates an immutable, SHA-256 chained audit manifest over all historical events in Sibyl Memory's COLD journal tier, verifying chain integrity for compliance.

5. **Sibyl Storage Tier Escalation (`GET /api/memory/tier` & `POST /api/memory/tier`)**:
   - Direct introspection of Sibyl storage quota (`free_tier_status`), byte usage, and runtime tier switching (`free`, `pro`, `enterprise`).

6. **Location Hierarchy Zoning & Sector Threat Inheritance**:
   - Understands nested facility sectors (`Perimeter -> Gate 3 -> Loading Dock B`). Unresolved threats within the same perimeter zone inherit risk context, while distinct gates (e.g. Gate 3 vs Gate 7) remain adversarially isolated.

7. **Temporal Memory Decay Weighting**:
   - Applies time-decay weighting to historical evidence (`<24h`: 1.0x, `7d`: 0.85x, `30d`: 0.70x, `>30d`: 0.50x), prioritizing urgent immediate threats while maintaining long-term pattern recognition.


