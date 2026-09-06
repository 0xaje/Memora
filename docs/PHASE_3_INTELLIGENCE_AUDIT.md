# Memora Phase 3 Intelligence Audit & Architecture Plan

## 1. Executive Summary

Memora has successfully completed Phase 2.5: Live Product Integration & Memory-Driven Decision Proof.
The FastAPI backend (`memora/`) is authoritative, the React console (`frontend/`) consumes the REST API directly, and Sibyl Memory is provably load-bearing through the verified Deletion Test.

The objective of Phase 3 is to elevate Memora's intelligence and operational reasoning without compromising deterministic stability, load-bearing memory proof, or architectural boundaries.

---

## 2. Current Architecture Audit

### 2.1 Current Incident Processing Pipeline
Located in `memora/incidents/service.py`:
1. `FactExtractor.extract(raw_text, location, type)`: Regex-based extraction of location, entities, indicators, and type.
2. `BaselineEngine.assess(facts)`: Stateless deterministic baseline (risk + recommendation).
3. `MemoryRetriever.retrieve_context(location, search_terms)`: Queries Sibyl Memory SQLite FTS5 for incidents, unresolved risks, decisions, outcomes, and operational lessons.
4. `HistoricalComparator.compare(facts, memory_results)`: Counts recurrence, checks unresolved status, identifies failed previous actions.
5. `DecisionEngine.decide(facts, baseline, memory, pattern)`: Applies deterministic escalation rules, outputs final risk, recommendation, and explanation.
6. `MemoryWriter`: Writes incident and decision records to Sibyl Memory.
7. Response serialization into `IncidentAnalysisResult`.

### 2.2 Current Fact Extraction
Located in `memora/intelligence/extractor.py`:
- Uses static regex patterns: `LOCATION_PATTERNS`, `ENTITY_PATTERNS`, `INDICATOR_PATTERNS`.
- Extracts: `location`, `incident_type`, `summary`, `indicators`, `entities_involved`.
- Gaps: Does not extract time/temporal information, duration, specific entity attributes (e.g., vehicle color/make), reporter details, or explicit unknowns.

### 2.3 Current Memory Retrieval
Located in `memora/memory/retriever.py`:
- Queries Sibyl by `location` across 5 categories: `incidents`, `unresolved_risks`, `operational_lessons`, `decisions`, `outcomes`.
- Also executes secondary queries for `search_terms` (entities involved).
- Gaps: Returns all matches without calculating nuanced relevance, category-specific weights, or location boundary verification for secondary search terms.

### 2.4 Current Decision Logic
Located in `memora/intelligence/decision_engine.py`:
- Deterministic rule-based:
  - If unresolved prior incident or failed prior mitigation: escalates `MEDIUM` -> `HIGH` (or `HIGH` -> `CRITICAL`).
  - Sets recommendation: `MONITOR_AND_VERIFY` -> `ESCALATE_TO_SUPERVISOR` (or `LOCKDOWN_AREA` for packages).
  - High recurrence count (>= 2): escalates to `DISPATCH_PATROL`.
- Gaps: Explanation string is template-driven; does not explicitly break down failed mitigation implications or translate lessons into actionable directives.

### 2.5 Current Inference Logic
Located in `memora/intelligence/comparator.py`:
- Checks `is_recurrent`, `recurrent_count`, `has_unresolved_prior_incident`, `has_prior_failed_outcome`, `failed_prior_recommendations`, `verified_mitigations`, `applicable_lessons`.
- Gaps: Does not separate facts from inferences in a structured schema, does not evaluate temporal recurrence, and does not flag resolved vs unresolved history cleanly.

### 2.6 Current Outcome / Learning Mechanism
Located in `memora/incidents/service.py`:
- `record_outcome(request)` writes `OutcomeMemory`, `UnresolvedRiskMemory`, and `OperationalLesson` into Sibyl SQLite database.
- Works reliably and is load-bearing.

---

## 3. Extension Points for Phase 3

| Extension Point | Current Implementation | Phase 3 Target |
|---|---|---|
| **Evidence Model** | Single `IncidentFacts` struct | Explicit taxonomy: `CURRENT_FACT`, `HISTORICAL_FACT`, `INFERENCE`, `RECOMMENDATION`, `UNKNOWN` |
| **Fact Extractor** | Basic location & keyword regex | Rich structured extraction: temporal windows, vehicle/entity specifics, duration, reporter, explicit unknowns |
| **Pattern Detection** | Recurrence count & unresolved flag | Structured operational patterns: location recurrence, unresolved recurrence, failed mitigation pattern, temporal pattern, resolved precedent |
| **Failed Mitigation** | String list of failed actions | Failed mitigation intelligence: identifies what was tried, why it failed, and produces current operational implication |
| **Actionable Lessons** | Passive lesson display | Active translation: historical lesson -> current operational implication |
| **Explanation Engine** | Generic template string | Evidence-backed transparent reasoning citing specific incident IDs, failed actions, and operational rationale |
| **Adversarial Safety** | Basic query filtering | Location boundary enforcement: prevents Gate 3 history from leaking into Gate 7; distinguishes resolved from unresolved history |

---

## 4. What Remains Deterministic vs AI Role

### Strictly Deterministic (Non-Negotiable)
- **Baseline Risk & Recommendation**: Must remain 100% deterministic code.
- **Memory-Informed Decision & Escalation**: Must remain 100% deterministic rules.
- **Storage & Retrieval Operations**: Direct Sibyl SQLite FTS5 queries.
- **Decision Engine Authorization**: AI models NEVER choose or modify the final operational risk level.

### Safe AI / Enhanced Intelligence Role
- **Rich Extraction & Entity Parsing**: Optional LLM-assisted or advanced regex parsing for messy human text, with 100% deterministic fallback.
- **Human-Readable Synthesis**: Evidence-backed narrative explanation of why the decision changed.
- **Operational Lesson Translation**: Translating historical findings into actionable operator guidance.

### Risks of External LLMs & Mitigations
1. **Hallucinated Historical Facts**: Mitigated by strictly grounding all statements in retrieved Sibyl SQLite records.
2. **Latency / Network Outages**: Mitigated by providing zero-dependency deterministic extractors and synthesizers as primary/fallback.
3. **Prompt Injection in Incident Text**: Mitigated by deterministic validation and refusal to evaluate prompt instructions inside incident text.

---

## 5. Proposed Phase 3 Architecture

```text
RAW OPERATIONAL INCIDENT
           │
           ▼
┌─────────────────────────────────────────┐
│ Enhanced Fact Extraction Engine        │
│ (Structured facts, entities, unknowns)  │
└────────────────────┬────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌───────────────────┐   ┌────────────────────────────────┐
│  Current Evidence │   │    Sibyl Memory Retrieval      │
│  (Direct Facts)   │   │ (Categorized & Verified Scope) │
└────────┬──────────┘   └───────────────┬────────────────┘
         │                              │
         │                              ▼
         │              ┌────────────────────────────────┐
         │              │ Historical Pattern Analysis    │
         │              │ - Location & Temporal Patterns │
         │              │ - Failed Mitigation Diagnosis  │
         │              │ - Actionable Lesson Implication│
         │              └───────────────┬────────────────┘
         │                              │
         ▼                              ▼
┌───────────────────┐   ┌────────────────────────────────┐
│ Baseline Engine   │   │ Deterministic Decision Engine  │
│ (Stateless Risk)  │──▶│ (Load-Bearing Escalation Rules)│
└───────────────────┘   └───────────────┬────────────────┘
                                        │
                                        ▼
                        ┌────────────────────────────────┐
                        │ Evidence-Backed Explanation    │
                        │ & Provenance Trace             │
                        └────────────────────────────────┘
```
