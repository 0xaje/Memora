import pytest
from pydantic import ValidationError
from memora.incidents.models import IncidentCreate, OutcomeCreate


def test_incident_create_validation_empty_text():
    with pytest.raises(ValidationError):
        IncidentCreate(raw_text="")

    with pytest.raises(ValidationError):
        IncidentCreate(raw_text="   ")


def test_incident_create_validation_valid():
    inc = IncidentCreate(
        raw_text="Suspicious delivery vehicle observed near Gate 3.",
        location="Gate 3"
    )
    assert inc.location == "Gate 3"
    assert "Gate 3" in inc.raw_text
    assert inc.memory_enabled is True


def test_outcome_create_validation_missing_fields():
    with pytest.raises(ValidationError):
        OutcomeCreate(
            incident_id="INC-001",
            action_taken="",  # min_length 3
            observed_result="Vehicle remained parked",
            is_resolved=False
        )
