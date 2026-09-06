# MEMORA — 3-MINUTE HACKATHON DEMO RUNBOOK
## Judge Verification & Live Execution Guide

**Core Thesis:** *“What happened before changes what Memora does now.”*  
Memora is an AI operational memory agent with real, load-bearing Sibyl Memory SQLite persistence and deterministic reasoning.

---

### Phase 1: Pre-Demo Readiness Check (30 Seconds)

1. **Start Backend Service:**
   ```bash
   source .venv/bin/activate && PYTHONPATH=. uvicorn memora.api.app:app --host 0.0.0.0 --port 8000
   ```
2. **Start Frontend Console:**
   ```bash
   npm run dev
   ```
3. **Verify System Health:**
   ```bash
   curl -s http://localhost:8000/health
   # Expected: {"status":"healthy","sibyl_memory_connected":true,"version":"0.1.0"}
   ```
4. **Open Browser Console:**
   - Navigate to `http://localhost:3000/`.
   - Verify topbar displays: `SIBYL CONNECTED`.
   - Verify session bar displays: `COLD-START / FRESH CONTEXT`, `BACKEND: HEALTHY (:8000)`, and real Git commit SHA.

---

### Phase 2: The Live Operational Demo (2 Minutes)

#### Step 1: Submit Incident A (Stateless Baseline)
- **Action:** In the Intake Panel (*"What happened?"*), enter:
  > `"Suspicious delivery vehicle observed lingering near Gate 3 for 45 minutes."`
- **Location:** `Gate 3`
- **Type:** `suspicious_vehicle`
- **Click:** **"Analyze incident"**
- **Observe:**
  - `BASELINE`: `MEDIUM · MONITOR_AND_VERIFY`
  - `SIBYL MEMORY`: `Found=False (0 retrieved)`
  - `MEMORA DECISION`: `MEDIUM · MONITOR_AND_VERIFY`
  - `DECISION CHANGED`: `False`
  - *Proof point:* In absence of memory, Memora applies standard stateless operational protocol.

#### Step 2: Record Unresolved Outcome (Persisting Failure)
- **Action:** Scroll to **Section 06 / OUTCOME + LEARNING**.
- **Action Taken:** `Monitored delivery vehicle via Gate 3 perimeter cameras`
- **Observed Result:** `Vehicle departed before license or driver credentials could be verified`
- **Resolution State:** Select **"Unresolved"**
- **Reason Unresolved:** `Camera resolution was insufficient to capture driver credentials`
- **Operational Lesson:** `Passive monitoring alone failed to resolve suspicious vehicle at Gate 3. Require physical patrol intercept.`
- **Click:** **"Record outcome & update learning"**
- **Observe:** Green confirmation card indicating `OUTCOME ID`, `INCIDENT REF`, and persistence into Sibyl SQLite.

#### Step 3: Establish Fresh Cold-Start Session
- **Action:** In the Session Bar at the top of the workspace, click:
  - **"Start Fresh Session"**
- **Observe:**
  - Notice alert: *"Fresh cold-start session initialized. Prior React state cleared; ready for clean incident input."*
  - Badge returns to: `COLD-START / FRESH CONTEXT`.
  - Prior analysis results cleared; no lingering client-side state.

#### Step 4: Submit Incident B (Memory Recall & Transformation)
- **Action:** In the Intake Panel, enter:
  > `"Suspicious delivery vehicle observed again near Gate 3."`
- **Location:** `Gate 3`
- **Click:** **"Analyze incident"**
- **Observe the Central Transformation Moment:**
  - **Hero Banner:** `MEMORY CHANGED THIS DECISION`
  - **Flow Card 01 (Baseline):** `MEDIUM · MONITOR_AND_VERIFY`
  - **Flow Arrow:** `SIBYL MEMORY (4 retrieved)`
  - **Flow Card 02 (Transformed):** `HIGH · ESCALATE_TO_SUPERVISOR`
  - **Why It Shifted:** Prior action (`Monitored delivery vehicle via Gate 3 cameras`) proved insufficient. Repeating it is contraindicated.

#### Step 5: Inspect Operational Intelligence Proof Surface
- **Failed Mitigation Card (Orange):** Diagnoses why the prior action failed and why active physical verification is mandatory.
- **Actionable Lesson Card (Green):** Institutional directive surfaced from Sibyl Memory.
- **Section 05 Memory Recall Proof Surface:**
  - `01 CURRENT FACTS`: Observable signals today.
  - `02 SIBYL REMEMBERED`: Real Sibyl record IDs and historical outcomes.
  - `03 INFERRED PATTERNS`: Recurrence count and failure pattern.
  - `04 UNKNOWNS`: Explicit operational unknowns identified (e.g. driver identity).
  - `05 RECOMMENDATION`: Memory-informed escalation.

#### Step 6: Audit Traceability in Provenance View
- **Action:** Click **"Provenance"** in the top navigation.
- **Observe:** 8-stage evidence chain from `CURRENT INPUT` $\to$ `CURRENT FACTS` $\to$ `SIBYL RETRIEVAL` $\to$ `HISTORICAL EVIDENCE` $\to$ `PATTERN DETECTED` $\to$ `INFERENCE` $\to$ `DECISION SHIFT` $\to$ `RECOMMENDATION`.
- **Technical Audit:** Click **"Inspect Raw API Payload"** to view real JSON with backend IDs, confidence scores, and timestamps.

---

### Phase 3: Automated Load-Bearing Proof (30 Seconds)

Execute the official standalone demo verification script:

```bash
source .venv/bin/activate && PYTHONPATH=. python scripts/verify_memora_demo.py
```

**Expected Judge Output:**
```text
===========================================================================
WITH SIBYL
Decision: HIGH
Reason:   Historical unresolved evidence from Gate 3 contraindicated baseline monitoring.

WITHOUT SIBYL
Decision: MEDIUM
Reason:   Historical evidence unavailable; fell back to stateless baseline.

LOAD-BEARING MEMORY PROOF: PASS
===========================================================================
```

---

### Phase 4: Full Regression Commands

```bash
# Backend pytest suite (23 tests: unit, contract, adversarial, hardening, deletion)
source .venv/bin/activate && PYTHONPATH=. pytest -v

# Frontend TypeScript check
npm run check

# Frontend test suite (17 unit/integration tests)
npm run test

# Production build validation
npm run build
```
