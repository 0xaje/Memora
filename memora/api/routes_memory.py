"""
Memory Inspection API Routes.
Enables judges and reviewers to directly inspect Sibyl Memory health,
entity counts, and raw cross-tier search results.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from memora.memory.client import sibyl_manager, SibylServiceError
from memora.memory.retriever import MemoryRetriever

router = APIRouter(prefix="/api/memory", tags=["Memory Inspection"])


@router.get("/status")
def memory_status() -> Dict[str, Any]:
    """Inspects Sibyl Memory connection, file path, and tier counts."""
    try:
        client = sibyl_manager.get_client()
        tid = sibyl_manager.tenant_id
        entity_count = client.storage.count_rows("entities", tid)
        event_count = client.storage.count_rows("journal_events", tid)
        ref_count = client.storage.count_rows("reference_documents", tid)
        with client.storage.connection() as conn:
            size_bytes = client.storage.logical_size_bytes(conn)

        return {
            "status": "connected",
            "backend": "Sibyl-Memory (SQLite FTS5)",
            "db_path": sibyl_manager.db_path,
            "tenant_id": sibyl_manager.tenant_id,
            "tier": sibyl_manager.tier,
            "counts": {
                "entities_warm": entity_count,
                "journal_cold": event_count,
                "reference": ref_count
            },
            "logical_size_bytes": size_bytes
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Sibyl Memory status check failed: {e}")


@router.get("/search")
def memory_search(q: str = Query(..., min_length=1)) -> Dict[str, Any]:
    """Direct cross-tier search across Sibyl Memory."""
    try:
        retriever = MemoryRetriever(sibyl_manager)
        results = retriever.search_all_tiers(query=q)
        return {
            "query": q,
            "count": len(results),
            "results": results
        }
    except SibylServiceError as sse:
        raise HTTPException(status_code=503, detail=str(sse))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
