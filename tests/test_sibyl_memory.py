import pytest
from memora.memory.writer import MemoryWriter
from memora.memory.retriever import MemoryRetriever
from memora.memory.models import (
    IncidentMemory,
    DecisionMemory,
    OutcomeMemory,
    UnresolvedRiskMemory,
    OperationalLesson
)


def test_real_sibyl_write_and_retrieve_incident(temp_sibyl_manager):
    writer = MemoryWriter(temp_sibyl_manager)
    retriever = MemoryRetriever(temp_sibyl_manager)

    # 1. Write incident
    incident = IncidentMemory(
        incident_id="INC-TEST-001",
        title="Suspicious vehicle at Gate 3",
        location="Gate 3",
        incident_type="suspicious_vehicle",
        summary="White delivery van observed idling near Gate 3 without manifest.",
        indicators=["suspicious activity", "loitering"],
        entities_involved=["delivery vehicle"],
        status="unresolved"
    )
    res = writer.write_incident(incident)
    assert res is not None
    assert res["name"] == "INC-TEST-001"

    # 2. Retrieve from Sibyl
    results = retriever.retrieve_context(location="Gate 3")
    assert results.total_hits >= 1
    assert len(results.related_incidents) == 1
    assert results.related_incidents[0]["incident_id"] == "INC-TEST-001"
    assert results.related_incidents[0]["status"] == "unresolved"


def test_real_sibyl_cross_tier_search(temp_sibyl_manager):
    writer = MemoryWriter(temp_sibyl_manager)
    retriever = MemoryRetriever(temp_sibyl_manager)

    lesson = OperationalLesson(
        lesson_id="LES-TEST-001",
        incident_id="INC-TEST-001",
        location="Gate 3",
        rule_or_insight="Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3.",
        failed_prior_action="MONITOR_AND_VERIFY"
    )
    writer.write_operational_lesson(lesson)

    # Cross tier search
    hits = retriever.search_all_tiers("Gate 3")
    assert len(hits) >= 1
    assert any("Gate 3" in str(h) for h in hits)
