import pytest
from memora.incidents.models import (
    IncidentCreate,
    OutcomeCreate,
    RiskLevel,
    RecommendationType
)
from memora.incidents.service import IncidentService
from memora.memory.client import SibylClientManager, SibylServiceError
from memora.memory.retriever import MemoryRetriever
from memora.memory.writer import MemoryWriter


def test_failure_mode_unwritable_db_path(tmp_path):
    """
    Requirement 10: Fail honestly on storage failure.
    If Sibyl cannot write due to an invalid path or storage error,
    it must raise an explicit SibylServiceError and NOT claim success.
    """
    # Pointing to a read-only or invalid filesystem node
    invalid_db_path = "/dev/null/impossible_dir/sibyl.db"
    failing_manager = SibylClientManager(db_path=invalid_db_path)
    service = IncidentService(client_manager=failing_manager)

    with pytest.raises(SibylServiceError) as excinfo:
        service.analyze_incident(IncidentCreate(
            raw_text="Observation at Checkpoint Charlie.",
            location="Checkpoint Charlie"
        ))

    assert "Sibyl Memory" in str(excinfo.value) or "initialization failed" in str(excinfo.value)


def test_failure_mode_retriever_fails_honestly(tmp_path, monkeypatch):
    """
    Requirement 10: Ensure memory retrieval failures NEVER convert silently
    into 'no memories found'.
    """
    db_path = str(tmp_path / "failing_retrieval.db")
    manager = SibylClientManager(db_path=db_path)
    retriever = MemoryRetriever(manager)

    # Force the underlying client search to fail with an exception
    client = manager.get_client()

    def broken_search(*args, **kwargs):
        raise RuntimeError("Simulated SQLite disk I/O error")

    monkeypatch.setattr(client, "search_entities", broken_search)

    with pytest.raises(SibylServiceError) as excinfo:
        retriever.retrieve_context(location="Gate 1")

    assert "Sibyl Memory retrieval failed" in str(excinfo.value)
    manager.close()


def test_failure_mode_empty_retrieval_honesty(tmp_path):
    """
    Requirement 10: Honestly report 'No relevant historical memory found'
    when the database is healthy but has no matching location records.
    """
    db_path = str(tmp_path / "empty_store.db")
    manager = SibylClientManager(db_path=db_path)
    service = IncidentService(client_manager=manager)

    res = service.analyze_incident(IncidentCreate(
        raw_text="Routine observation at Sector 99.",
        location="Sector 99"
    ))

    # Must honestly report zero hits and exact explanation
    assert res.memory_influence.retrieval_count == 0
    assert "No relevant historical memory found" in res.explanation.what_was_retrieved
    assert res.memory_assessment.changed is False

    manager.close()
