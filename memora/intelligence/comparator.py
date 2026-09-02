"""
Historical Pattern Comparator.
Analyzes retrieved historical memory from Sibyl against the current incident.
Identifies:
- Recurrence (how many times has this happened at this location?)
- Unresolved previous cases
- Failed previous decisions/outcomes (e.g. MONITOR_AND_VERIFY was insufficient)
- Actionable operational lessons
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from memora.incidents.models import IncidentFacts, RecommendationType
from memora.memory.retriever import MemoryRetrievalResult


class PatternComparison(BaseModel):
    is_recurrent: bool = False
    recurrent_count: int = 0
    has_unresolved_prior_incident: bool = False
    unresolved_incident_ids: List[str] = Field(default_factory=list)
    has_prior_failed_outcome: bool = False
    failed_prior_recommendations: List[str] = Field(default_factory=list)
    verified_mitigations: List[str] = Field(default_factory=list)
    applicable_lessons: List[str] = Field(default_factory=list)
    matched_location: str = ""
    summary: str = ""


class HistoricalComparator:
    """
    Compares current incident facts with retrieved Sibyl Memory.
    """

    def compare(self, facts: IncidentFacts, memory: MemoryRetrievalResult) -> PatternComparison:
        comparison = PatternComparison(matched_location=facts.location)

        # 1. Evaluate related incidents
        recurrent_count = 0
        unresolved_ids = []
        for inc in memory.related_incidents:
            recurrent_count += 1
            status = inc.get("status", "unresolved")
            inc_id = inc.get("incident_id") or inc.get("id") or "UNKNOWN"
            if status in ("unresolved", "active", "monitoring"):
                unresolved_ids.append(inc_id)

        comparison.recurrent_count = recurrent_count
        comparison.is_recurrent = recurrent_count > 0
        comparison.unresolved_incident_ids = unresolved_ids
        comparison.has_unresolved_prior_incident = len(unresolved_ids) > 0 or memory.has_unresolved_history()

        # 2. Evaluate previous outcomes & decisions for failed and verified mitigations
        failed_recs = []
        verified_recs = []
        for outcome in memory.previous_outcomes:
            if not outcome.get("is_resolved", True):
                comparison.has_prior_failed_outcome = True
                action = outcome.get("action_taken", "")
                if action:
                    failed_recs.append(action)
            else:
                action = outcome.get("action_taken", "")
                if action:
                    verified_recs.append(action)

        for lesson in memory.operational_lessons:
            rule = lesson.get("rule_or_insight", "")
            prior_action = lesson.get("failed_prior_action")
            successful_action = lesson.get("successful_mitigation")

            if successful_action:
                verified_recs.append(successful_action)

            # Lessons only escalate if there was a failed prior action or explicit escalation mandate
            if prior_action or lesson.get("escalation_recommendation") == RecommendationType.ESCALATE_TO_SUPERVISOR.value:
                if rule:
                    comparison.applicable_lessons.append(rule)
                if prior_action:
                    failed_recs.append(prior_action)

        comparison.failed_prior_recommendations = list(set(failed_recs))
        comparison.verified_mitigations = list(set(verified_recs))

        # 3. Generate structured summary of comparison
        findings = []
        if comparison.is_recurrent:
            findings.append(f"Identified {recurrent_count} prior incident(s) at {facts.location}.")
        if comparison.has_unresolved_prior_incident:
            findings.append(f"Found active unresolved prior incident(s): {', '.join(unresolved_ids) if unresolved_ids else 'General unresolved security risk'}.")
        if comparison.has_prior_failed_outcome:
            findings.append(f"Prior mitigation ({', '.join(comparison.failed_prior_recommendations) if comparison.failed_prior_recommendations else 'MONITOR_AND_VERIFY'}) did not resolve the recurring issue.")
        if comparison.verified_mitigations:
            findings.append(f"Historical evidence shows effective mitigation: {', '.join(comparison.verified_mitigations)}.")
        if comparison.applicable_lessons:
            findings.append(f"Operational lesson applies: {comparison.applicable_lessons[0]}")

        comparison.summary = " ".join(findings) if findings else "No historical pattern matches detected."
        return comparison
