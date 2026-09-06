"""
Historical Pattern Comparator.
Analyzes retrieved historical memory from Sibyl against the current incident.
Identifies:
- Location Recurrence (enforces location boundaries)
- Unresolved vs Resolved History
- Failed Prior Mitigations & Operational Diagnoses
- Actionable Operational Lessons
- Multi-dimensional Pattern Classification
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from memora.incidents.models import (
    IncidentFacts,
    RecommendationType,
    FailedMitigation,
    ActionableLesson,
    HistoricalPatternDetail
)
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
    failed_mitigation_details: List[FailedMitigation] = Field(default_factory=list)
    actionable_lessons_details: List[ActionableLesson] = Field(default_factory=list)
    patterns_detected: List[HistoricalPatternDetail] = Field(default_factory=list)
    is_resolved_precedent: bool = False
    matched_location: str = ""
    summary: str = ""


class HistoricalComparator:
    """
    Compares current incident facts with retrieved Sibyl Memory.
    Enforces strict location relevance and clear separation between resolved and unresolved history.
    """

    @staticmethod
    def _is_location_relevant(item_loc: Optional[str], target_loc: Optional[str]) -> bool:
        """
        Validates if an item's location is relevant to the target incident location.
        Enforces adversarial isolation between distinct gates/facilities (e.g. Gate 3 vs Gate 7).
        """
        if not item_loc or not target_loc:
            return False
        l1 = item_loc.strip().lower()
        l2 = target_loc.strip().lower()
        if l1 == l2:
            return True
        # Facility wide or perimeter facility applies broadly
        if "facility" in l1 or "perimeter" in l1:
            return True
        # Explicit gate / building / sector isolation
        return l1 in l2 or l2 in l1

    def compare(self, facts: IncidentFacts, memory: MemoryRetrievalResult) -> PatternComparison:
        comparison = PatternComparison(matched_location=facts.location)

        # 1. Filter and evaluate related incidents by location relevance
        relevant_incidents = [
            inc for inc in memory.related_incidents
            if self._is_location_relevant(inc.get("location"), facts.location)
        ]

        recurrent_count = len(relevant_incidents)
        unresolved_ids: List[str] = []
        resolved_count = 0

        for inc in relevant_incidents:
            status = inc.get("status", "unresolved")
            inc_id = inc.get("incident_id") or inc.get("id") or "UNKNOWN"
            if status in ("unresolved", "active", "monitoring", "open"):
                unresolved_ids.append(inc_id)
            elif status == "resolved":
                resolved_count += 1

        comparison.recurrent_count = recurrent_count
        comparison.is_recurrent = recurrent_count > 0
        comparison.unresolved_incident_ids = unresolved_ids

        # Check unresolved risks with location relevancy
        relevant_unresolved_risks = [
            r for r in memory.unresolved_risks
            if self._is_location_relevant(r.get("location"), facts.location) and r.get("status") in ("open", "unresolved")
        ]

        comparison.has_unresolved_prior_incident = (
            len(unresolved_ids) > 0 or len(relevant_unresolved_risks) > 0
        )
        comparison.is_resolved_precedent = (
            recurrent_count > 0 and len(unresolved_ids) == 0 and len(relevant_unresolved_risks) == 0
        )

        # 2. Evaluate previous outcomes for failed and verified mitigations
        failed_recs: List[str] = []
        verified_recs: List[str] = []
        failed_mitigation_details: List[FailedMitigation] = []

        for outcome in memory.previous_outcomes:
            action = outcome.get("action_taken", "")
            result = outcome.get("observed_result", "")
            is_resolved = outcome.get("is_resolved", True)

            if not is_resolved:
                comparison.has_prior_failed_outcome = True
                if action:
                    failed_recs.append(action)
                failure_diagnosis = (
                    f"Prior action '{action}' did not resolve the incident ('{result}'). "
                    f"The subject or hazard remained unverified."
                )
                current_implication = (
                    f"Repeating '{action}' risks leaving the same operational uncertainty unresolved. "
                    f"Physical intercept or supervisor escalation required."
                )
                failed_mitigation_details.append(FailedMitigation(
                    prior_action=action or "Passive monitoring",
                    observed_result=result or "Unresolved outcome",
                    failure_diagnosis=failure_diagnosis,
                    current_implication=current_implication
                ))
            else:
                if action:
                    verified_recs.append(action)

        # 3. Evaluate operational lessons with actionable translations
        actionable_lessons: List[ActionableLesson] = []
        for lesson in memory.operational_lessons:
            rule = lesson.get("rule_or_insight", "")
            lesson_id = lesson.get("lesson_id", "LES-OPERATIONAL")
            prior_action = lesson.get("failed_prior_action")
            successful_action = lesson.get("successful_mitigation")
            lesson_loc = lesson.get("location")

            # Check location applicability or facility-wide rule
            if lesson_loc and not self._is_location_relevant(lesson_loc, facts.location):
                continue

            if successful_action:
                verified_recs.append(successful_action)

            if prior_action or lesson.get("escalation_recommendation") == RecommendationType.ESCALATE_TO_SUPERVISOR.value:
                if rule:
                    comparison.applicable_lessons.append(rule)
                if prior_action:
                    failed_recs.append(prior_action)
                    if not any(fm.prior_action == prior_action for fm in failed_mitigation_details):
                        failed_mitigation_details.append(FailedMitigation(
                            prior_action=prior_action,
                            observed_result=rule or "Prior action failed to eliminate recurring hazard",
                            failure_diagnosis=f"Prior operational action '{prior_action}' was documented as insufficient in institutional lesson {lesson_id}.",
                            current_implication=f"Repeating '{prior_action}' is contraindicated at {facts.location}. Escalate to supervisor."
                        ))

                actionable_lessons.append(ActionableLesson(
                    lesson_id=lesson_id,
                    historical_rule=rule or "Escalate recurrent anomalies.",
                    current_implication=f"Historical lesson indicates previous monitoring at {facts.location} was insufficient.",
                    recommended_adjustment="Escalate to supervisor rather than relying solely on passive surveillance."
                ))

        comparison.failed_prior_recommendations = list(set(failed_recs))
        comparison.verified_mitigations = list(set(verified_recs))
        comparison.failed_mitigation_details = failed_mitigation_details
        comparison.actionable_lessons_details = actionable_lessons

        # 4. Multi-dimensional pattern detection
        patterns: List[HistoricalPatternDetail] = []
        if comparison.is_recurrent:
            patterns.append(HistoricalPatternDetail(
                pattern_type="location_recurrence",
                title="Location Recurrence Detected",
                description=f"{recurrent_count} prior similar incident(s) recorded at {facts.location}.",
                supporting_record_ids=[i.get("incident_id") or i.get("id", "REC") for i in relevant_incidents]
            ))

        if comparison.has_unresolved_prior_incident:
            patterns.append(HistoricalPatternDetail(
                pattern_type="unresolved_hazard",
                title="Unresolved Prior Hazard",
                description=f"Previous incident(s) ({', '.join(unresolved_ids) if unresolved_ids else 'active risk'}) remain open at {facts.location}.",
                supporting_record_ids=unresolved_ids
            ))
        elif comparison.is_resolved_precedent:
            patterns.append(HistoricalPatternDetail(
                pattern_type="resolved_precedent",
                title="Resolved Precedent",
                description=f"Prior similar occurrence at {facts.location} was successfully resolved; no open hazard persists.",
                supporting_record_ids=[i.get("incident_id") or i.get("id", "REC") for i in relevant_incidents]
            ))

        if comparison.has_prior_failed_outcome:
            patterns.append(HistoricalPatternDetail(
                pattern_type="failed_mitigation",
                title="Failed Historical Mitigation",
                description=f"Prior response action ('{', '.join(comparison.failed_prior_recommendations)}') was proven ineffective at resolving this hazard.",
                supporting_record_ids=[o.get("outcome_id", "OUT") for o in memory.previous_outcomes if not o.get("is_resolved", True)]
            ))

        comparison.patterns_detected = patterns

        # 5. Generate structured findings summary
        findings = []
        if comparison.is_recurrent:
            findings.append(f"Identified {recurrent_count} prior incident(s) at {facts.location}.")
        if comparison.has_unresolved_prior_incident:
            findings.append(f"Found active unresolved prior incident(s): {', '.join(unresolved_ids) if unresolved_ids else 'General unresolved security risk'}.")
        elif comparison.is_resolved_precedent:
            findings.append(f"Prior incident at {facts.location} was successfully resolved; recurrence noted without active hazard escalation.")
        if comparison.has_prior_failed_outcome:
            findings.append(f"Prior mitigation ({', '.join(comparison.failed_prior_recommendations) if comparison.failed_prior_recommendations else 'MONITOR_AND_VERIFY'}) did not resolve the recurring issue.")
        if comparison.verified_mitigations:
            findings.append(f"Historical evidence shows effective mitigation: {', '.join(comparison.verified_mitigations)}.")
        if comparison.applicable_lessons:
            findings.append(f"Operational lesson applies: {comparison.applicable_lessons[0]}")

        comparison.summary = " ".join(findings) if findings else "No historical pattern matches detected."
        return comparison
