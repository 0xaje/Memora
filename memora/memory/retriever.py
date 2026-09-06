"""
Sibyl Memory Retriever.
Executes real FTS5 and multi-category queries across Sibyl Memory.
Respects the Sibyl Verdict contract and fails honestly if storage faults occur.
"""

import logging
from typing import Dict, List, Any, Optional
from sibyl_memory_client import MemoryClient
from sibyl_memory_client.exceptions import StorageError

from memora.memory.models import (
    IncidentMemory,
    DecisionMemory,
    OutcomeMemory,
    UnresolvedRiskMemory,
    OperationalLesson,
    MemoryCategory
)
from memora.memory.client import SibylClientManager, SibylServiceError

logger = logging.getLogger("memora.memory.retriever")


class MemoryRetrievalResult:
    """Encapsulates categorized memories retrieved from Sibyl."""

    def __init__(
        self,
        query: str,
        related_incidents: List[Dict[str, Any]],
        unresolved_risks: List[Dict[str, Any]],
        previous_decisions: List[Dict[str, Any]],
        previous_outcomes: List[Dict[str, Any]],
        operational_lessons: List[Dict[str, Any]],
        verdict: str = "ok",
        total_hits: int = 0
    ):
        self.query = query
        self.related_incidents = related_incidents
        self.unresolved_risks = unresolved_risks
        self.previous_decisions = previous_decisions
        self.previous_outcomes = previous_outcomes
        self.operational_lessons = operational_lessons
        self.verdict = verdict
        self.total_hits = total_hits

    def has_unresolved_history(self) -> bool:
        """Returns True if any retrieved incident or risk is in 'unresolved' or 'open' status."""
        for inc in self.related_incidents:
            if inc.get("status") == "unresolved":
                return True
        for risk in self.unresolved_risks:
            if risk.get("status") in ("open", "unresolved"):
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "related_incidents": self.related_incidents,
            "unresolved_risks": self.unresolved_risks,
            "previous_decisions": self.previous_decisions,
            "previous_outcomes": self.previous_outcomes,
            "operational_lessons": self.operational_lessons,
            "total_hits": self.total_hits,
            "verdict": self.verdict
        }


class MemoryRetriever:
    """
    Executes targeted and cross-tier retrieval from Sibyl Memory.
    """

    def __init__(self, client_manager: Optional[SibylClientManager] = None):
        self.manager = client_manager or SibylClientManager()

    def _get_client(self, tenant_id: Optional[str] = None) -> MemoryClient:
        return self.manager.get_client(tenant_id=tenant_id)

    def retrieve_context(
        self,
        location: str,
        search_terms: Optional[List[str]] = None,
        tenant_id: Optional[str] = None
    ) -> MemoryRetrievalResult:
        """
        Retrieves all relevant historical memories from Sibyl for a specific location and terms.
        Queries each category (incidents, unresolved_risks, decisions, outcomes, operational_lessons).
        """
        client = self._get_client(tenant_id=tenant_id)
        query = location.strip()
        logger.info("Querying Sibyl Memory for location: '%s', tenant: %s, additional terms: %s",
                    location, tenant_id or self.manager.tenant_id, search_terms)

        related_incidents: List[Dict[str, Any]] = []
        unresolved_risks: List[Dict[str, Any]] = []
        previous_decisions: List[Dict[str, Any]] = []
        previous_outcomes: List[Dict[str, Any]] = []
        operational_lessons: List[Dict[str, Any]] = []

        try:
            # 1. Search incidents category
            inc_res = client.search_entities(query=query, category=MemoryCategory.INCIDENTS.value)
            for row in inc_res:
                body = row.get("body", {})
                body["status"] = row.get("status", body.get("status", "unresolved"))
                body["id"] = row.get("name", row.get("id"))
                related_incidents.append(body)

            # 2. Search unresolved risks category
            risk_res = client.search_entities(query=query, category=MemoryCategory.UNRESOLVED_RISKS.value)
            for row in risk_res:
                body = row.get("body", {})
                body["status"] = row.get("status", "open")
                unresolved_risks.append(body)

            # 3. Search operational lessons category
            lesson_res = client.search_entities(query=query, category=MemoryCategory.OPERATIONAL_LESSONS.value)
            for row in lesson_res:
                body = row.get("body", {})
                operational_lessons.append(body)

            # 4. Search decisions category
            decision_res = client.search_entities(query=query, category=MemoryCategory.DECISIONS.value)
            for row in decision_res:
                body = row.get("body", {})
                previous_decisions.append(body)

            # 5. Search outcomes category
            outcome_res = client.search_entities(query=query, category=MemoryCategory.OUTCOMES.value)
            for row in outcome_res:
                body = row.get("body", {})
                previous_outcomes.append(body)

            # If search_terms provided (e.g. "delivery vehicle"), also run targeted queries
            if search_terms:
                for term in search_terms:
                    term_clean = term.strip()
                    if not term_clean or term_clean.lower() == location.lower():
                        continue
                    extra_lessons = client.search_entities(query=term_clean, category=MemoryCategory.OPERATIONAL_LESSONS.value)
                    for row in extra_lessons:
                        body = row.get("body", {})
                        if not any(l.get("lesson_id") == body.get("lesson_id") for l in operational_lessons):
                            operational_lessons.append(body)

            total_hits = (len(related_incidents) + len(unresolved_risks) +
                          len(previous_decisions) + len(previous_outcomes) +
                          len(operational_lessons))

            logger.info("Sibyl retrieval finished. Total hits: %d (incidents: %d, risks: %d, lessons: %d)",
                        total_hits, len(related_incidents), len(unresolved_risks), len(operational_lessons))

            return MemoryRetrievalResult(
                query=query,
                related_incidents=related_incidents,
                unresolved_risks=unresolved_risks,
                previous_decisions=previous_decisions,
                previous_outcomes=previous_outcomes,
                operational_lessons=operational_lessons,
                verdict="ok" if total_hits > 0 else "no_match",
                total_hits=total_hits
            )

        except Exception as e:
            logger.error("Sibyl retrieval failed for query '%s': %s", query, e)
            raise SibylServiceError(f"Sibyl Memory retrieval failed: {e}") from e

    def search_all_tiers(self, query: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Cross-tier full-text search directly through Sibyl Memory.
        Sanitizes raw SQLite/Sibyl rows into UI-safe memory records and enforces tenant isolation.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        client = self._get_client(tenant_id=tenant_id)
        try:
            results = client.search(query=clean_query)
            sanitized: List[Dict[str, Any]] = []
            for item in results:
                tier = item.get("tier", "entity")
                category = item.get("category", tier)
                body = item.get("body", {}) if isinstance(item.get("body"), dict) else {}
                key = item.get("key") or item.get("id") or "RECORD"
                summary = (
                    body.get("summary")
                    or body.get("rule_or_insight")
                    or body.get("hazard_description")
                    or body.get("title")
                    or body.get("observed_result")
                    or item.get("snippet")
                    or "Historical operational memory"
                )
                sanitized.append({
                    "id": key,
                    "tier": tier,
                    "category": category,
                    "location": body.get("location", "Perimeter Facility"),
                    "summary": summary,
                    "status": body.get("status", item.get("status", "recorded")),
                    "timestamp": body.get("timestamp") or item.get("ts"),
                    "score": item.get("rank")
                })
            return sanitized
        except Exception as e:
            logger.error("Cross-tier search failed for '%s': %s", clean_query, e)
            raise SibylServiceError(f"Sibyl search failed: {e}") from e

    def get_state(self, key: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves active working state from Sibyl's native HOT state tier.
        """
        client = self._get_client(tenant_id=tenant_id)
        try:
            return client.get_state(key=key)
        except Exception as e:
            logger.error("Failed to get state %s from Sibyl: %s", key, e)
            raise SibylServiceError(f"Failed to get state from Sibyl: {e}") from e

    def get_reference(self, key: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves operational protocol/SOP documents from Sibyl's native REFERENCE tier.
        """
        client = self._get_client(tenant_id=tenant_id)
        try:
            return client.get_reference(key=key)
        except Exception as e:
            logger.error("Failed to get reference %s from Sibyl: %s", key, e)
            raise SibylServiceError(f"Failed to get reference from Sibyl: {e}") from e

