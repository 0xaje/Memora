# MEMORA Known Limitations & Technical Scope (Phase 4: Operational Intelligence & Cold-Start Proof)

In strict accordance with the **Memora Backend Engineering Constitution (Rule 29: Maintain a Known Limitations List)**, this document records all intentional boundaries, constraints, and current scope limits as of Phase 4.

---

## 1. Single-Node SQLite Storage
* **Current Implementation**: Sibyl Memory operates via local SQLite with FTS5 search (`MemoryClient.local(...)`).
* **Limitation**: The storage is local-first. Concurrent writes across multiple distributed processes require file-locking or a dedicated service tier. For hackathon Phases 1 through 4, single-instance FastAPI operation is the verified architecture.

## 2. Fact Extraction Scope
* **Current Implementation**: Fact extraction uses deterministic regex and dictionary token matchers (`FactExtractor`) for facility locations (e.g. gates, sectors, checkpoints) and security entities (delivery vehicles, trespassers, packages). Phase 3 added structured temporal indicators and explicit unknown detection.
* **Limitation**: Highly unstructured complex prose or foreign languages will fall back to `"Unknown Facility Location"` unless explicit location metadata is provided in the intake payload. Full LLM semantic entity extraction can be connected as an optional parsing enhancement.

## 3. External AI / LLM Integrations
* **Current Status**: **DELIBERATELY DEFERRED FOR DECISION CORE**.
* **Rationale**: In strict accordance with Constitution Rules 1, 7, and 8 ("No Fake AI", "Deterministic Core"), the decision engine uses strict deterministic escalation rules rather than unvetted LLM calls. The core escalation from `MEDIUM` to `HIGH` is mathematically grounded in retrieved historical failure records. LLM summarization of operational narratives can be connected as a post-processing layer once API keys are configured.

## 4. Blockchain & Partner Integrations (Base, Virtuals)
* **Current Status**: **NOT IMPLEMENTED YET**.
* **Rationale**: In strict accordance with Constitution Rules 15, 16, and Phase 1–4 objectives, Base and Virtuals Protocol integrations are deliberately deferred until the core Sibyl Memory loop has been completely proven and delivered.

## 5. Free-Tier Storage Cap
* **Current Constraint**: Free-tier accounts in `sibyl-memory-client` are subject to a local 5 MB cap (`CapExceededError`). The test suite and demonstrations use light metadata and targeted entities that remain well below this threshold.

## 6. Authentication & User Accounts
* **Current Status**: **DELIBERATELY DEFERRED**.
* **Rationale**: The API currently accepts an optional `tenant_id` for multi-tenant boundary isolation. Production user authentication (OAuth/JWT/RBAC) is scheduled for post-hackathon evaluation.
