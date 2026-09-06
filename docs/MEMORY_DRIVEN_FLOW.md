# Memora Memory-Driven Decision Flow & Deletion Proof

## 1. The Core Product Thesis

> **“What happened before changes what Memora does now.”**

Memora is not an LLM chat interface, a decorative dashboard, or a stateless decision rulebook. Memora is an operational memory engine that bridges the gap between historical incidents and live operator decisions.

---

## 2. The Complete Closed-Loop Operational Flow

```text
       ┌────────────────────────┐
       │   Operator Incident    │  "Suspicious delivery vehicle near Gate 3"
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Sibyl Memory Retrieval │  Search: semantic + FTS5 against historical tier
       └───────────┬────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌──────────────────┐ ┌──────────────────┐
│ Baseline Engine  │ │ Historical Memory│  Previous similar incident retrieved:
│ (Stateless)      │ │ Context          │  - Prior status: UNRESOLVED
│ MEDIUM / MONITOR │ │                  │  - Prior action: Monitored vehicle
└────────┬─────────┘ └────────┬─────────┘
         │                    │
         └─────────┬──────────┘
                   ▼
       ┌────────────────────────┐
       │  Pattern Inference     │  Detected: Recurring unresolved vehicle anomaly
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Memory-Informed Dec.   │  Transformed:
       │ (HIGH / ESCALATE)      │  "Memory Changed This Decision"
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Operator Action Taken  │  Operator dispatches supervisor & secures log
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Operational Outcome    │  Recorded via POST /api/outcomes
       │ & Learning Persisted   │  - Resolution status: RESOLVED
       └───────────┬────────────┘  - Learning rule: "Supervisor escalation..."
                   │
                   ▼
       ┌────────────────────────┐
       │ Closed Memory Loop     │  Future incidents at Gate 3 will leverage
       │                        │  the verified mitigation and lessons learned!
       └────────────────────────┘
```

---

## 3. Load-Bearing Sibyl Proof: The Deletion Test

The central proof of load-bearing memory is the **Deletion Test**:

1. **State A (With Memory)**:
   - Incident: `Suspicious delivery vehicle observed again near Gate 3`
   - Memory State: Previous unresolved incident exists in Sibyl Memory.
   - Outcome: **HIGH / ESCALATE_TO_SUPERVISOR** (`decision_changed: true`).

2. **State B (Without Memory - Memory Isolated or Reset)**:
   - Incident: `Suspicious delivery vehicle observed again near Gate 3`
   - Memory State: Sibyl database is wiped, isolated, or bypassed.
   - Outcome: **MEDIUM / MONITOR_AND_VERIFY** (`decision_changed: false`).

> [!IMPORTANT]
> **Why this matters**:
> If the decision in State B were still `HIGH / ESCALATE_TO_SUPERVISOR`, the memory layer would be purely decorative. The fact that the decision returns to baseline proves mathematically and operationally that **Sibyl Memory is load-bearing**.
