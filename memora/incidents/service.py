"""
Incident Service Orchestrator.
Coordinates the load-bearing operational memory loop:
1. Extract current incident facts.
2. Retrieve relevant Sibyl Memory.
3. Assess current facts (baseline).
4. Compare facts with history.
5. Generate memory-informed decision.
6. Persist incident & decision to Sibyl Memory.
7. Support later outcome recording and lesson synthesis.
"""

import uuid
import logging
from typing import Optional, Dict, Any

from memora.incidents.models import (
    IncidentCreate,
    IncidentFacts,
    OutcomeCreate,
    SessionContext,
    BaselineAssessment,
    MemoryAssessment,
    MemoryInfluence,
    DecisionExplanation,
    IncidentAnalysisResult,
    DecisionChangeDetails,
    PatternInferenceSummary,
    ProvenanceSummary,
    MemoryRecordUI,
    MemorySummary,
    OutcomeResponse,
    RiskLevel,
    RecommendationType,
    EvidenceType,
    EvidenceItem,
    FailedMitigation,
    ActionableLesson,
    HistoricalPatternDetail
)
from memora.intelligence.extractor import FactExtractor
from memora.intelligence.baseline import BaselineEngine
from memora.intelligence.comparator import HistoricalComparator
from memora.intelligence.decision_engine import DecisionEngine
from memora.memory.writer import MemoryWriter
from memora.memory.retriever import MemoryRetriever, MemoryRetrievalResult
from memora.memory.models import (
    IncidentMemory,
    DecisionMemory,
    OutcomeMemory,
    UnresolvedRiskMemory,
    OperationalLesson,
    MemoryCategory
)
from memora.memory.client import sibyl_manager, SibylClientManager

logger = logging.getLogger("memora.incidents.service")


class IncidentService:
    """
    Coordinates the core operational memory pipeline.
    """

    def __init__(self, client_manager: Optional[SibylClientManager] = None):
        self.manager = client_manager or sibyl_manager
        self.writer = MemoryWriter(client_manager=self.manager)
        self.retriever = MemoryRetriever(client_manager=self.manager)
        self.extractor = FactExtractor()
        self.baseline_engine = BaselineEngine()
        self.comparator = HistoricalComparator()
        self.decision_engine = DecisionEngine()

    def analyze_incident(
        self,
        request: IncidentCreate,
        session_id: Optional[str] = None,
        is_fresh_session: bool = True
    ) -> IncidentAnalysisResult:
        """
        Executes the load-bearing incident analysis pipeline.
        """
        sid = session_id or request.session_id or f"sess_{uuid.uuid4().hex[:10]}"
        logger.info("Starting incident analysis. Session ID: %s, Fresh: %s, Memory Enabled: %s",
                    sid, is_fresh_session, request.memory_enabled)

        # 1. Extract current operational facts
        facts: IncidentFacts = self.extractor.extract(
            raw_text=request.raw_text,
            explicit_location=request.location,
            explicit_type=request.incident_type
        )
        logger.info("Extracted facts: ID=%s, Location='%s', Type='%s'",
                    facts.incident_id, facts.location, facts.incident_type)

        # 2. Baseline assessment of current facts alone (NO memory)
        baseline: BaselineAssessment = self.baseline_engine.assess(facts)
        logger.info("Baseline assessment: Risk=%s, Recommendation=%s",
                    baseline.risk.value, baseline.recommendation.value)

        # 3. Retrieve relevant Sibyl Memory (if memory_enabled)
        if request.memory_enabled:
            logger.info("Querying Sibyl Memory for location: '%s' (tenant: %s)...",
                        facts.location, request.tenant_id or "default")
            memory_results: MemoryRetrievalResult = self.retriever.retrieve_context(
                location=facts.location,
                search_terms=facts.entities_involved,
                tenant_id=request.tenant_id
            )
        else:
            logger.info("Memory retrieval bypassed (baseline mode requested for deletion test).")
            memory_results = MemoryRetrievalResult(
                query=facts.location,
                related_incidents=[],
                unresolved_risks=[],
                previous_decisions=[],
                previous_outcomes=[],
                operational_lessons=[],
                verdict="disabled",
                total_hits=0
            )

        # 4. Compare current observations with historical memory
        pattern = self.comparator.compare(facts, memory_results)
        logger.info("Historical pattern: is_recurrent=%s (count=%d), unresolved=%s",
                    pattern.is_recurrent, pattern.recurrent_count, pattern.has_unresolved_prior_incident)

        # 5. Make memory-informed decision
        memory_assessment, explanation = self.decision_engine.decide(
            facts=facts,
            baseline=baseline,
            memory=memory_results,
            pattern=pattern
        )
        logger.info("Final memory assessment: Risk=%s, Rec=%s, Changed=%s",
                    memory_assessment.risk.value, memory_assessment.recommendation.value,
                    memory_assessment.changed)

        # 6. Persist incident observation and decision to Sibyl Memory (if memory enabled)
        if request.memory_enabled:
            try:
                # Write incident entity
                inc_entity = IncidentMemory(
                    incident_id=facts.incident_id,
                    title=f"{facts.incident_type} at {facts.location}",
                    location=facts.location,
                    incident_type=facts.incident_type,
                    summary=facts.summary,
                    indicators=facts.indicators,
                    entities_involved=facts.entities_involved,
                    status="unresolved"
                )
                self.writer.write_incident(inc_entity, tenant_id=request.tenant_id)

                # Write decision entity
                decision_entity = DecisionMemory(
                    decision_id=f"DEC-{facts.incident_id}",
                    incident_id=facts.incident_id,
                    baseline_risk=baseline.risk.value,
                    final_risk=memory_assessment.risk.value,
                    recommendation=memory_assessment.recommendation.value,
                    rationale=explanation.why_decision_changed,
                    memory_informed=memory_assessment.changed
                )
                self.writer.write_decision(decision_entity, tenant_id=request.tenant_id)
            except Exception as e:
                logger.error("Failed persisting operational knowledge to Sibyl: %s", e)
                # Re-raise to fail honestly per constitution
                raise

        # 7. Construct memory influence payload
        memory_influence = MemoryInfluence(
            related_incidents=memory_results.related_incidents,
            unresolved_risks=memory_results.unresolved_risks,
            previous_decisions=memory_results.previous_decisions,
            previous_outcomes=memory_results.previous_outcomes,
            operational_lessons=memory_results.operational_lessons,
            retrieval_count=memory_results.total_hits
        )

        # 8. Build explicit UI-safe memory summary
        ui_records: List[MemoryRecordUI] = []
        for inc in memory_results.related_incidents:
            ui_records.append(MemoryRecordUI(
                category="incidents",
                id=inc.get("incident_id") or inc.get("id") or "UNKNOWN",
                location=inc.get("location", facts.location),
                summary=inc.get("summary") or inc.get("title") or "Historical incident record",
                status=inc.get("status", "unresolved"),
                timestamp=inc.get("timestamp")
            ))
        for risk in memory_results.unresolved_risks:
            ui_records.append(MemoryRecordUI(
                category="unresolved_risks",
                id=risk.get("risk_id") or "UNKNOWN",
                location=risk.get("location", facts.location),
                summary=risk.get("hazard_description") or "Active unresolved hazard",
                status=risk.get("status", "open"),
                timestamp=risk.get("last_updated") or risk.get("first_observed")
            ))
        for les in memory_results.operational_lessons:
            ui_records.append(MemoryRecordUI(
                category="operational_lessons",
                id=les.get("lesson_id") or "UNKNOWN",
                location=les.get("location", facts.location),
                summary=les.get("rule_or_insight") or "Operational lesson",
                status="active",
                action_taken=les.get("failed_prior_action"),
                rule_or_insight=les.get("rule_or_insight"),
                recurrence_count=les.get("recurrence_count", 1),
                successful_mitigation=les.get("successful_mitigation"),
                timestamp=les.get("updated_at") or les.get("created_at")
            ))
        for out in memory_results.previous_outcomes:
            ui_records.append(MemoryRecordUI(
                category="outcomes",
                id=out.get("outcome_id") or "UNKNOWN",
                location=facts.location,
                summary=f"Action '{out.get('action_taken')}': {out.get('observed_result')}",
                status="resolved" if out.get("is_resolved") else "unresolved",
                action_taken=out.get("action_taken"),
                is_resolved=out.get("is_resolved"),
                timestamp=out.get("timestamp")
            ))

        memory_summary = MemorySummary(
            found=memory_results.total_hits > 0,
            count=memory_results.total_hits,
            records=ui_records
        )

        # 9. Build explicit pattern inference summary
        inference_summary = PatternInferenceSummary(
            is_recurrent=pattern.is_recurrent,
            recurrence_count=pattern.recurrent_count,
            unresolved_history=pattern.has_unresolved_prior_incident,
            unresolved_incident_ids=pattern.unresolved_incident_ids,
            has_prior_failed_outcome=pattern.has_prior_failed_outcome,
            failed_prior_actions=pattern.failed_prior_recommendations,
            verified_mitigations=pattern.verified_mitigations,
            applicable_lessons=pattern.applicable_lessons,
            failed_mitigation_details=pattern.failed_mitigation_details,
            actionable_lessons_details=pattern.actionable_lessons_details,
            patterns_detected=pattern.patterns_detected,
            is_resolved_precedent=pattern.is_resolved_precedent,
            temporal_weight=pattern.temporal_weight,
            temporal_urgency=pattern.temporal_urgency,
            summary=pattern.summary
        )

        # 10. Build decision change details
        decision_change = None
        if memory_assessment.changed:
            decision_change = DecisionChangeDetails(
                from_risk=baseline.risk,
                to_risk=memory_assessment.risk,
                from_recommendation=baseline.recommendation,
                to_recommendation=memory_assessment.recommendation
            )

        # 11. Build provenance summary
        provenance = ProvenanceSummary(
            facts=explanation.what_happened,
            retrieval=explanation.what_was_retrieved,
            inference=explanation.what_pattern_was_inferred,
            decision_shift=explanation.why_decision_changed
        )

        # 12. Build structured evidence chain
        evidence_chain: List[EvidenceItem] = []
        evidence_chain.append(EvidenceItem(
            source="current_observation",
            type=EvidenceType.CURRENT_FACT,
            confidence=1.0,
            entity_or_location=facts.location,
            supporting_record_id=facts.incident_id,
            text=f"Observed at {facts.location}: '{facts.summary}'"
        ))
        if facts.approximate_time:
            evidence_chain.append(EvidenceItem(
                source="current_observation",
                type=EvidenceType.CURRENT_FACT,
                confidence=0.95,
                text=f"Approximate time of observation: {facts.approximate_time}"
            ))
        if facts.entities_involved:
            evidence_chain.append(EvidenceItem(
                source="current_observation",
                type=EvidenceType.CURRENT_FACT,
                confidence=1.0,
                text=f"Identified entities: {', '.join(facts.entities_involved)}"
            ))

        for rec in ui_records[:5]:
            evidence_chain.append(EvidenceItem(
                source="sibyl_memory",
                type=EvidenceType.HISTORICAL_FACT,
                confidence=1.0,
                entity_or_location=rec.location,
                supporting_record_id=rec.id,
                text=f"[{rec.category.upper()}] {rec.summary} (Status: {rec.status})"
            ))

        if pattern.is_recurrent:
            evidence_chain.append(EvidenceItem(
                source="inference_engine",
                type=EvidenceType.INFERENCE,
                confidence=0.92,
                entity_or_location=facts.location,
                text=f"Pattern detected: {pattern.recurrent_count} prior incident(s) at {facts.location}"
            ))

        if pattern.has_prior_failed_outcome and pattern.failed_mitigation_details:
            fm = pattern.failed_mitigation_details[0]
            evidence_chain.append(EvidenceItem(
                source="inference_engine",
                type=EvidenceType.INFERENCE,
                confidence=0.90,
                text=fm.current_implication
            ))

        for unk in facts.unknowns:
            evidence_chain.append(EvidenceItem(
                source="evidence_validator",
                type=EvidenceType.UNKNOWN,
                confidence=1.0,
                text=unk
            ))

        evidence_chain.append(EvidenceItem(
            source="decision_engine",
            type=EvidenceType.RECOMMENDATION,
            confidence=memory_assessment.confidence,
            text=f"{memory_assessment.risk.value}: {memory_assessment.recommendation.value}"
        ))

        return IncidentAnalysisResult(
            incident=facts,
            session=SessionContext(id=sid, is_fresh=is_fresh_session),
            baseline_assessment=baseline,
            memory_assessment=memory_assessment,
            memory_influence=memory_influence,
            explanation=explanation,
            baseline=baseline,
            decision=memory_assessment,
            decision_changed=memory_assessment.changed,
            decision_change=decision_change,
            memory=memory_summary,
            inference=inference_summary,
            why_decision_changed=explanation.why_decision_changed,
            provenance=provenance,
            evidence_chain=evidence_chain,
            failed_mitigations=pattern.failed_mitigation_details,
            actionable_lessons=pattern.actionable_lessons_details,
            patterns_detected=pattern.patterns_detected,
            unknowns=facts.unknowns
        )

    def record_outcome(self, request: OutcomeCreate) -> OutcomeResponse:
        """
        Records the outcome of an incident and writes operational learnings to Sibyl.
        """
        logger.info("Recording outcome for incident: %s (resolved=%s)",
                    request.incident_id, request.is_resolved)

        client = self.manager.get_client(tenant_id=request.tenant_id)
        location = "Perimeter Facility"
        try:
            parent_inc = client.get_entity("incidents", request.incident_id)
            if parent_inc and "body" in parent_inc:
                location = parent_inc["body"].get("location", location)
        except Exception as e:
            logger.warning("Could not fetch parent incident %s for location: %s", request.incident_id, e)

        outcome_id = f"OUT-{uuid.uuid4().hex[:8].upper()}"

        outcome = OutcomeMemory(
            outcome_id=outcome_id,
            incident_id=request.incident_id,
            action_taken=request.action_taken,
            observed_result=request.observed_result,
            is_resolved=request.is_resolved,
            unresolved_reason=request.unresolved_reason,
            location=location
        )

        # Write outcome to Sibyl
        self.writer.write_outcome(outcome, tenant_id=request.tenant_id)

        lesson_id = None
        lesson_rule = None
        recurrence_count = None
        successful_mitigation = None

        if not request.is_resolved:
            # Case 1: Unresolved outcome -> persist or escalate UnresolvedRisk & OperationalLesson
            risk_entity = UnresolvedRiskMemory(
                risk_id=f"RISK-{request.incident_id}",
                incident_id=request.incident_id,
                location=location,
                hazard_description=f"Unresolved: {request.observed_result} (Reason: {request.unresolved_reason or 'Ongoing threat'})",
                severity="HIGH"
            )
            self.writer.write_unresolved_risk(risk_entity, tenant_id=request.tenant_id)

            # Check if an operational lesson already exists for this location to dynamically refine it
            existing_lesson = None
            try:
                lesson_hits = client.search_entities(query=location, category=MemoryCategory.OPERATIONAL_LESSONS.value)
                if lesson_hits:
                    existing_lesson = lesson_hits[0].get("body", {})
            except Exception as find_err:
                logger.debug("No existing lesson found for location %s: %s", location, find_err)

            lesson_id = existing_lesson.get("lesson_id", f"LES-{request.incident_id}") if existing_lesson else f"LES-{request.incident_id}"
            recurrence_count = (existing_lesson.get("recurrence_count", 1) + 1) if existing_lesson else 1

            lesson_rule = request.operational_lesson or (
                f"Action '{request.action_taken}' failed to resolve recurring activity related to {request.incident_id}. "
                f"Escalation required on subsequent observations (recurrence count: {recurrence_count})."
            )

            lesson_entity = OperationalLesson(
                lesson_id=lesson_id,
                incident_id=request.incident_id,
                location=location,
                rule_or_insight=lesson_rule,
                failed_prior_action=request.action_taken,
                escalation_recommendation=RecommendationType.ESCALATE_TO_SUPERVISOR.value,
                recurrence_count=recurrence_count
            )
            self.writer.write_operational_lesson(lesson_entity, tenant_id=request.tenant_id)

        else:
            # Case 2: Resolved outcome -> close active risk and record what successfully resolved the threat
            successful_mitigation = request.action_taken
            try:
                # Mark unresolved risk as mitigated/closed if exists
                risk_id = f"RISK-{request.incident_id}"
                existing_risk = client.get_entity(MemoryCategory.UNRESOLVED_RISKS.value, risk_id)
                if existing_risk:
                    risk_body = existing_risk.get("body", {}).copy()
                    risk_body["status"] = "mitigated"
                    risk_body["mitigation_action"] = request.action_taken
                    client.set_entity(
                        category=MemoryCategory.UNRESOLVED_RISKS.value,
                        name=risk_id,
                        body=risk_body,
                        status="mitigated"
                    )
            except Exception as risk_close_err:
                logger.debug("No active risk entity found to close: %s", risk_close_err)

            # Update or write operational lesson documenting the confirmed successful mitigation
            try:
                lesson_hits = client.search_entities(query=location, category=MemoryCategory.OPERATIONAL_LESSONS.value)
                if lesson_hits:
                    top_lesson = lesson_hits[0]
                    lesson_id = top_lesson.get("name") or top_lesson.get("id")
                    body = top_lesson.get("body", {}).copy()
                    body["successful_mitigation"] = request.action_taken
                    lesson_rule = (
                        f"{body.get('rule_or_insight', '')} Confirmed resolution: '{request.action_taken}' "
                        f"successfully resolved the incident."
                    )
                    body["rule_or_insight"] = lesson_rule
                    client.set_entity(
                        category=MemoryCategory.OPERATIONAL_LESSONS.value,
                        name=top_lesson["name"],
                        body=body,
                        status="verified"
                    )
                else:
                    # Create new lesson noting the effective procedure
                    lesson_id = f"LES-{request.incident_id}"
                    lesson_rule = f"Action '{request.action_taken}' successfully resolved incident {request.incident_id}."
                    new_lesson = OperationalLesson(
                        lesson_id=lesson_id,
                        incident_id=request.incident_id,
                        location=location,
                        rule_or_insight=lesson_rule,
                        successful_mitigation=request.action_taken,
                        escalation_recommendation=request.action_taken
                    )
                    self.writer.write_operational_lesson(new_lesson, tenant_id=request.tenant_id)
            except Exception as lesson_update_err:
                logger.warning("Could not update operational lesson on resolution: %s", lesson_update_err)

        return OutcomeResponse(
            status="success",
            outcome_id=outcome_id,
            incident_id=request.incident_id,
            is_resolved=request.is_resolved,
            action_taken=request.action_taken,
            observed_result=request.observed_result,
            unresolved_reason=request.unresolved_reason,
            lesson_id=lesson_id,
            lesson_rule=lesson_rule,
            recurrence_count=recurrence_count,
            successful_mitigation=successful_mitigation,
            message="Outcome and operational learning persisted to Sibyl Memory."
        )
