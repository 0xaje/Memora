"""
Load-Bearing Decision Engine.
Produces the memory-informed risk assessment, escalated recommendation,
and complete audit explanation.
"""

from typing import Tuple
from memora.incidents.models import (
    IncidentFacts,
    BaselineAssessment,
    MemoryAssessment,
    DecisionExplanation,
    RiskLevel,
    RecommendationType
)
from memora.intelligence.comparator import PatternComparison
from memora.memory.retriever import MemoryRetrievalResult


class DecisionEngine:
    """
    Executes the memory-informed decision.
    Strictly adheres to the load-bearing requirement:
    'What happened before changes what Memora does now.'
    """

    def decide(
        self,
        facts: IncidentFacts,
        baseline: BaselineAssessment,
        memory: MemoryRetrievalResult,
        pattern: PatternComparison
    ) -> Tuple[MemoryAssessment, DecisionExplanation]:

        # Default: if no relevant memory, memory assessment mirrors baseline
        final_risk = baseline.risk
        recommendation = baseline.recommendation
        changed = False
        escalation_reason = None

        # Load-bearing escalation rules:
        # Rule 1: Recurring incident + Unresolved previous incident at the same location
        # Rule 2: Prior mitigation (e.g. MONITOR_AND_VERIFY) failed to resolve the risk
        # Rule 3: Operational lesson mandates escalation
        if pattern.has_unresolved_prior_incident or pattern.has_prior_failed_outcome or pattern.applicable_lessons:
            changed = True

            if baseline.risk in (RiskLevel.LOW, RiskLevel.MEDIUM):
                final_risk = RiskLevel.HIGH
            elif baseline.risk == RiskLevel.HIGH:
                final_risk = RiskLevel.CRITICAL

            # Recommendation escalation logic
            if baseline.recommendation == RecommendationType.MONITOR_AND_VERIFY:
                # Monitoring failed previously, escalate to supervisor or dispatch patrol
                recommendation = RecommendationType.ESCALATE_TO_SUPERVISOR
                escalation_reason = (
                    f"Recurrence detected at {facts.location} with unresolved prior incident. "
                    f"Prior low-level action failed to eliminate the hazard."
                )
            elif baseline.recommendation == RecommendationType.DISPATCH_PATROL:
                recommendation = RecommendationType.ESCALATE_TO_SUPERVISOR
                escalation_reason = f"Patrol previously deployed; unresolved recurrence at {facts.location} requires supervisory intervention."
            else:
                recommendation = RecommendationType.ESCALATE_TO_SUPERVISOR
                escalation_reason = f"Historical recurrence pattern mandates supervisory review."

        elif pattern.is_recurrent and pattern.recurrent_count >= 2:
            # High frequency recurrence even if technically marked resolved
            changed = True
            final_risk = RiskLevel.HIGH
            recommendation = RecommendationType.DISPATCH_PATROL
            escalation_reason = f"High recurrence count ({pattern.recurrent_count}) observed at {facts.location}."

        memory_assessment = MemoryAssessment(
            risk=final_risk,
            recommendation=recommendation,
            changed=changed,
            confidence=0.92 if changed else baseline.confidence,
            escalation_reason=escalation_reason
        )

        # Build full auditable explanation
        explanation = self._build_explanation(facts, baseline, memory, pattern, memory_assessment)
        return memory_assessment, explanation

    def _build_explanation(
        self,
        facts: IncidentFacts,
        baseline: BaselineAssessment,
        memory: MemoryRetrievalResult,
        pattern: PatternComparison,
        assessment: MemoryAssessment
    ) -> DecisionExplanation:

        what_happened = (
            f"Observation at {facts.location}: '{facts.summary}'. "
            f"Identified entities: {', '.join(facts.entities_involved) or 'None'}. "
            f"Indicators: {', '.join(facts.indicators) or 'None'}."
        )

        if memory.total_hits > 0:
            retrieved_items = []
            if memory.related_incidents:
                ids = [i.get('incident_id', i.get('id', '')) for i in memory.related_incidents]
                retrieved_items.append(f"{len(memory.related_incidents)} incident(s) ({', '.join(ids)})")
            if memory.unresolved_risks:
                retrieved_items.append(f"{len(memory.unresolved_risks)} open risk(s)")
            if memory.operational_lessons:
                retrieved_items.append(f"{len(memory.operational_lessons)} operational lesson(s)")
            what_was_retrieved = f"Retrieved {memory.total_hits} records from Sibyl Memory: " + ", ".join(retrieved_items) + "."
        else:
            what_was_retrieved = "No relevant historical memory found in Sibyl Memory for this location."

        what_pattern_was_inferred = pattern.summary

        if assessment.changed:
            unresolved_detail = f"related unresolved case(s) [{', '.join(pattern.unresolved_incident_ids)}]" if pattern.unresolved_incident_ids else "open risk history"
            why_decision_changed = (
                f"Baseline evaluation without memory produced {baseline.risk.value} risk and '{baseline.recommendation.value}'. "
                f"However, Sibyl Memory revealed {unresolved_detail} and demonstrated that prior monitoring did not resolve the threat. "
                f"Consequently, operational risk was escalated to {assessment.risk.value} and recommendation changed to '{assessment.recommendation.value}'."
            )
        else:
            why_decision_changed = (
                f"Decision remained at baseline {baseline.risk.value} ('{baseline.recommendation.value}') because no prior "
                f"unresolved incidents or failed mitigations were discovered in Sibyl Memory."
            )

        return DecisionExplanation(
            what_happened=what_happened,
            what_was_retrieved=what_was_retrieved,
            what_pattern_was_inferred=what_pattern_was_inferred,
            why_decision_changed=why_decision_changed
        )
