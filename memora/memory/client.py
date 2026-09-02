"""
Real Sibyl MemoryClient integration.
Provides a transparent wrapper around sibyl_memory_client.MemoryClient.
Fails honestly with descriptive exceptions if storage or connection fails.
"""

import logging
from pathlib import Path
from typing import Optional
from sibyl_memory_client import MemoryClient
from sibyl_memory_client.exceptions import StorageError, SibylMemoryError
from memora.config import settings

logger = logging.getLogger("memora.memory.client")


class SibylServiceError(Exception):
    """Raised when Sibyl Memory encounters a storage or connection failure."""
    pass


class SibylClientManager:
    """
    Manages the lifecycle and connection to the real Sibyl MemoryClient.
    Uses SQLite-backed persistent storage with FTS5 search.
    """

    def __init__(self, db_path: Optional[str] = None, tenant_id: Optional[str] = None, tier: Optional[str] = None):
        self.db_path = db_path or settings.resolved_db_path()
        self.tenant_id = tenant_id or settings.SIBYL_TENANT_ID
        self.tier = tier or settings.SIBYL_TIER
        self._client: Optional[MemoryClient] = None

    def get_client(self, tenant_id: Optional[str] = None) -> MemoryClient:
        """
        Returns an initialized MemoryClient instance.
        Ensures the target directory exists and the schema is validated.
        If a custom tenant_id is provided, sets it on the client for partition isolation.
        """
        target_tenant = tenant_id or self.tenant_id
        if self._client is None:
            try:
                db_file = Path(self.db_path)
                db_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

                logger.info("Initializing Sibyl MemoryClient at: %s (tenant: %s, tier: %s)",
                            self.db_path, target_tenant, self.tier)

                self._client = MemoryClient.local(
                    path=self.db_path,
                    tenant_id=target_tenant,
                    tier=self.tier
                )
            except Exception as e:
                logger.error("Failed to initialize Sibyl MemoryClient at %s: %s", self.db_path, e)
                raise SibylServiceError(f"Sibyl Memory initialization failed: {e}") from e
        else:
            if target_tenant != self._client.get_tenant():
                self._client.set_tenant(target_tenant)

        return self._client

    def is_healthy(self) -> bool:
        """Verifies that the Sibyl SQLite connection is active and responsive."""
        try:
            client = self.get_client()
            client.storage.count_rows("entities", self.tenant_id)
            return True
        except Exception as e:
            logger.warning("Sibyl health check failed: %s", e)
            return False

    def close(self):
        """Closes the underlying database connection if open."""
        if self._client is not None:
            try:
                self._client.storage.close()
            except Exception as e:
                logger.warning("Error closing Sibyl storage: %s", e)
            finally:
                self._client = None


# Default singleton instance using application settings
sibyl_manager = SibylClientManager()
