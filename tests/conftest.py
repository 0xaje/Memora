import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from memora.memory.client import SibylClientManager
from memora.incidents.service import IncidentService
from memora.api.app import app


@pytest.fixture
def temp_sibyl_manager(tmp_path):
    """Provides a temporary, clean Sibyl database for isolated testing."""
    db_file = tmp_path / "test_sibyl_memora.db"
    manager = SibylClientManager(db_path=str(db_file))
    yield manager
    manager.close()


@pytest.fixture
def temp_incident_service(temp_sibyl_manager):
    """Provides an IncidentService wired to the temporary Sibyl instance."""
    return IncidentService(client_manager=temp_sibyl_manager)


@pytest.fixture
def api_client(temp_sibyl_manager, monkeypatch):
    """Provides a TestClient with the Sibyl manager redirected to a temp DB."""
    import memora.memory.client as client_mod
    import memora.incidents.service as service_mod

    monkeypatch.setattr(client_mod, "sibyl_manager", temp_sibyl_manager)
    return TestClient(app)
