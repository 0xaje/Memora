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
    RiskLevel,
    RecommendationType
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
    OperationalLesson
)
from memora.memory.client import sibyl_manager, SibylClientManager

logger = logging.getLogger("memora.incidents.service")


class IncidentService:
    """
    Main domain service coordinating incident analysis, outcomes, and Sibyl persistence.
    """

    def __init__(self, client_manager: Optional[SibylClientManager] = None):
        self.manager = client_manager or sibyl_manager
        self.writer = MemoryWriter(self.manager)
        self.retriever = MemoryRetriever(self.manager)
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
            logger.info("Querying Sibyl Memory for location: '%s'...", facts.location)
            memory_results: MemoryRetrievalResult = self.retriever.retrieve_context(
                location=facts.location,
                search_terms=facts.entities_involved
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

        # 4. Compare current incident with retrieved history
        pattern = self.comparator.compare(facts, memory_results)
        logger.info("Historical pattern: is_recurrent=%s (count=%d), unresolved=%s",
                    pattern.is_recurrent, pattern.recurrent_count, pattern.has_unresolved_prior_incident)

        # 5. Generate memory-informed decision & auditable explanation
        memory_assessment, explanation = self.decision_engine.decide(
            facts=facts,
            baseline=baseline,
            memory=memory_results,
            pattern=pattern
        )
        logger.info("Final memory assessment: Risk=%s, Rec=%s, Changed=%s",
                    memory_assessment.risk.value, memory_assessment.recommendation.value, memory_assessment.changed)

        # 6. Persist new operational knowledge to Sibyl Memory (if memory_enabled)
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
                self.writer.write_incident(inc_entity)

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
                self.writer.write_decision(decision_entity)
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

        return IncidentAnalysisResult(
            incident=facts,
            session=SessionContext(id=sid, is_fresh=is_fresh_session),
            baseline_assessment=baseline,
            memory_assessment=memory_assessment,
            memory_influence=memory_influence,
            explanation=explanation
        )

    def record_outcome(self, request: OutcomeCreate) -> Dict[str, Any]:
        """
        Records the outcome of an incident and writes operational learnings to Sibyl.
        """
        logger.info("Recording outcome for incident: %s (resolved=%s)",
                    request.incident_id, request.is_resolved)

        outcome_id = f"OUT-{uuid.uuid4().hex[:8].upper()}"

        outcome = OutcomeMemory(
            outcome_id=outcome_id,
            incident_id=request.incident_id,
            action_taken=request.action_taken,
            observed_result=request.observed_result,
            is_resolved=request.is_resolved,
            unresolved_reason=request.unresolved_reason
        )

        # Write outcome to Sibyl
        self.writer.write_outcome(outcome)

        # If unresolved, write or update an UnresolvedRiskMemory
        if not request.is_resolved:
            # Query incident directly by ID from Sibyl to obtain exact location
            client = self.manager.get_client()
            location = "Perimeter Facility"
            try:
                parent_inc = client.get_entity("incidents", request.incident_id)
                if parent_inc and "body" in parent_inc:
                    location = parent_inc["body"].get("location", location)
            except Exception as e:
                logger.warning("Could not fetch parent incident %s for location: %s", request.incident_id, e)

            risk_entity = UnresolvedRiskMemory(
                risk_id=f"RISK-{request.incident_id}",
                incident_id=request.incident_id,
                location=location,
                hazard_description=f"Unresolved: {request.observed_result} (Reason: {request.unresolved_reason or 'Ongoing threat'})",
                severity="HIGH"
            )
            self.writer.write_unresolved_risk(risk_entity)

            # Synthesize operational lesson
            lesson_rule = request.operational_lesson or (
                f"Action '{request.action_taken}' failed to resolve recurring activity related to {request.incident_id}. "
                f"Escalation required on subsequent observations."
            )
            lesson_entity = OperationalLesson(
                lesson_id=f"LES-{request.incident_id}",
                incident_id=request.incident_id,
                location=location,
                rule_or_insight=lesson_rule,
                failed_prior_action=request.action_taken,
                escalation_recommendation=RecommendationType.ESCALATE_TO_SUPERVISOR.value
            )
            self.writer.write_operational_lesson(lesson_entity)

        return {
            "status": "success",
            "outcome_id": outcome_id,
            "incident_id": request.incident_id,
            "is_resolved": request.is_resolved,
            "message": "Outcome and operational learning persisted to Sibyl Memory."
        }
