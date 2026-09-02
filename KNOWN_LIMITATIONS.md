# MEMORA Known Limitations & Technical Scope (Phase 1 & Phase 1.75)

In strict accordance with the **Memora Backend Engineering Constitution (Rule 29: Maintain a Known Limitations List)**, this document records all intentional boundaries, constraints, and current scope limits.

---

## 1. Single-Node SQLite Storage
* **Current Implementation**: Sibyl Memory operates via local SQLite with FTS5 search (`MemoryClient.local(...)`).
* **Limitation**: The storage is local-first. Concurrent writes across multiple distributed processes require file-locking or a dedicated service tier. For hackathon Phase 1 and 1.75, single-instance FastAPI operation is the intended architecture.

## 2. Fact Extraction Scope
* **Current Implementation**: Fact extraction uses deterministic regex and dictionary token matchers (`FactExtractor`) for facility locations (e.g. gates, sectors, checkpoints) and security entities (delivery vehicles, trespassers, packages).
* **Limitation**: Highly unstructured complex prose or foreign languages will fall back to `"Unknown Facility Location"` unless explicit metadata is provided in the intake payload. Full LLM semantic entity extraction can be connected in Phase 2.

## 3. External AI / LLM Integrations
* **Current Status**: **NOT YET CONNECTED** for decision synthesis.
* **Rationale**: In strict accordance with Constitution Rules 1, 7, and 8 ("No Fake AI", "Deterministic Core"), the Phase 1 decision engine uses strict deterministic escalation rules rather than simulated LLM calls. LLM summarization of explanations will be wired once API keys and provider rate-limits are configured.

## 4. Blockchain & Partner Integrations (Base, Virtuals)
* **Current Status**: **NOT IMPLEMENTED YET**.
* **Rationale**: In strict accordance with Constitution Rules 15, 16, and Phase 1 objectives, Base and Virtuals Protocol integrations are deliberately deferred until the core Sibyl Memory loop has been proven.

## 5. Free-Tier Storage Cap
* **Current Constraint**: Free-tier accounts in `sibyl-memory-client` are subject to a local 5 MB cap (`CapExceededError`). The test suite and demonstrations use light metadata that remains well below this threshold.

## 6. Authentication & User Accounts
* **Current Status**: **DELIBERATELY DEFERRED**.
* **Rationale**: The API currently accepts an optional `tenant_id` for organization boundary isolation. Production user authentication (OAuth/JWT/RBAC) is scheduled for post-UI evaluation.
