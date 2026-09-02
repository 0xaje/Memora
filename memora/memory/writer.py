"""
Sibyl Memory Writer.
Implements persistent storage across Sibyl's native tiers:
- WARM tier (`set_entity`): For entities with single source of truth (incidents, unresolved risks, operational lessons).
- COLD tier (`write_event`): For append-only audit journal events.
- REFERENCE tier (`set_reference`): For operational protocols.
"""

import logging
from typing import Dict, Any, Optional
from sibyl_memory_client import MemoryClient
from sibyl_memory_client.exceptions import StorageError, ValidationError, CapExceededError

from memora.memory.models import (
    IncidentMemory,
    DecisionMemory,
    OutcomeMemory,
    UnresolvedRiskMemory,
    OperationalLesson,
    MemoryCategory
)
from memora.memory.client import SibylClientManager, SibylServiceError

logger = logging.getLogger("memora.memory.writer")


class MemoryWriter:
    """
    Handles all write operations to Sibyl Memory.
    Provides auditable, typed write methods for the 5 memory categories.
    """

    def __init__(self, client_manager: Optional[SibylClientManager] = None):
        self.manager = client_manager or SibylClientManager()

    def _get_client(self, tenant_id: Optional[str] = None) -> MemoryClient:
        return self.manager.get_client(tenant_id=tenant_id)

    def write_incident(self, incident: IncidentMemory, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Persists an incident entity into the WARM tier and logs an audit event in COLD tier.
        """
        client = self._get_client(tenant_id=tenant_id)
        category = MemoryCategory.INCIDENTS.value
        name = incident.incident_id
        body = incident.model_dump()
        status = incident.status

        logger.info("Writing incident entity to Sibyl: category=%s, name=%s, status=%s", category, name, status)
        try:
            entity_row = client.set_entity(
                category=category,
                name=name,
                body=body,
                status=status
            )

            # Record append-only journal event in COLD tier
            client.write_event(
                evaluated={"incident_id": name, "title": incident.title, "location": incident.location},
                acted={"action": "INCIDENT_CREATED", "status": status},
                forward={"follow_up": "ASSESSMENT_PENDING"}
            )

            return entity_row
        except Exception as e:
            logger.error("Failed to write incident %s to Sibyl Memory: %s", name, e)
            raise SibylServiceError(f"Failed to persist incident in Sibyl Memory: {e}") from e

    def write_decision(self, decision: DecisionMemory, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Persists an assessment/decision into Sibyl Memory.
        Updates the incident status and appends an audit event to the journal.
        """
        client = self._get_client(tenant_id=tenant_id)
        category = MemoryCategory.DECISIONS.value
        name = decision.decision_id
        body = decision.model_dump()

        logger.info("Writing decision to Sibyl: name=%s, incident=%s, final_risk=%s (tenant: %s)",
                    name, decision.incident_id, decision.final_risk, tenant_id or self.manager.tenant_id)
        try:
            entity_row = client.set_entity(
                category=category,
                name=name,
                body=body,
                status="active"
            )

            client.write_event(
                evaluated={"decision_id": name, "incident_id": decision.incident_id, "baseline_risk": decision.baseline_risk},
                acted={"action": "ASSESSMENT_DECIDED", "final_risk": decision.final_risk, "recommendation": decision.recommendation},
                forward={"memory_informed": decision.memory_informed, "rationale": decision.rationale}
            )

            return entity_row
        except Exception as e:
            logger.error("Failed to write decision %s to Sibyl Memory: %s", name, e)
            raise SibylServiceError(f"Failed to persist decision in Sibyl Memory: {e}") from e

    def write_outcome(self, outcome: OutcomeMemory, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Persists an incident outcome to Sibyl Memory.
        Updates the underlying incident status (e.g. resolved vs unresolved).
        """
        client = self._get_client(tenant_id=tenant_id)
        category = MemoryCategory.OUTCOMES.value
        name = outcome.outcome_id
        body = outcome.model_dump()
        status = "resolved" if outcome.is_resolved else "unresolved"

        logger.info("Writing outcome to Sibyl: name=%s, incident=%s, status=%s (tenant: %s)",
                    name, outcome.incident_id, status, tenant_id or self.manager.tenant_id)
        try:
            entity_row = client.set_entity(
                category=category,
                name=name,
                body=body,
                status=status
            )

            # Update the original incident entity status in Sibyl
            incident_category = MemoryCategory.INCIDENTS.value
            try:
                # Merge with existing body so location & summary are preserved for FTS5
                existing_entity = client.get_entity(incident_category, outcome.incident_id)
                merged_body = existing_entity.get("body", {}).copy() if existing_entity else {}
                merged_body.update({
                    "outcome_summary": outcome.observed_result,
                    "action_taken": outcome.action_taken,
                    "is_resolved": outcome.is_resolved
                })
                client.set_entity(
                    category=incident_category,
                    name=outcome.incident_id,
                    body=merged_body,
                    status=status
                )
            except Exception as update_err:
                logger.warning("Could not update parent incident %s status: %s", outcome.incident_id, update_err)

            # Record outcome event in journal
            client.write_event(
                evaluated={"outcome_id": name, "incident_id": outcome.incident_id},
                acted={"action": "OUTCOME_RECORDED", "status": status, "action_taken": outcome.action_taken},
                forward={"observed_result": outcome.observed_result}
            )

            return entity_row
        except Exception as e:
            logger.error("Failed to write outcome %s to Sibyl Memory: %s", name, e)
            raise SibylServiceError(f"Failed to persist outcome in Sibyl Memory: {e}") from e

    def write_unresolved_risk(self, risk: UnresolvedRiskMemory, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Persists an active unresolved risk entity into Sibyl Memory.
        """
        client = self._get_client(tenant_id=tenant_id)
        category = MemoryCategory.UNRESOLVED_RISKS.value
        name = risk.risk_id
        body = risk.model_dump()

        logger.info("Writing unresolved risk to Sibyl: name=%s, location=%s, severity=%s (tenant: %s)",
                    name, risk.location, risk.severity, tenant_id or self.manager.tenant_id)
        try:
            return client.set_entity(
                category=category,
                name=name,
                body=body,
                status=risk.status
            )
        except Exception as e:
            logger.error("Failed to write unresolved risk %s to Sibyl: %s", name, e)
            raise SibylServiceError(f"Failed to persist unresolved risk in Sibyl: {e}") from e

    def write_operational_lesson(self, lesson: OperationalLesson, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Persists a synthesized operational lesson into Sibyl Memory.
        """
        client = self._get_client(tenant_id=tenant_id)
        category = MemoryCategory.OPERATIONAL_LESSONS.value
        name = lesson.lesson_id
        body = lesson.model_dump()

        logger.info("Writing operational lesson to Sibyl: name=%s, location=%s, rule=%s (tenant: %s)",
                    name, lesson.location, lesson.rule_or_insight, tenant_id or self.manager.tenant_id)
        try:
            return client.set_entity(
                category=category,
                name=name,
                body=body,
                status="active"
            )
        except Exception as e:
            logger.error("Failed to write operational lesson %s to Sibyl: %s", name, e)
            raise SibylServiceError(f"Failed to persist operational lesson in Sibyl: {e}") from e
