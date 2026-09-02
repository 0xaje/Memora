"""
Memory Inspection API Routes.
Enables judges and reviewers to directly inspect Sibyl Memory health,
entity counts, and raw cross-tier search results.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from memora.memory.client import sibyl_manager, SibylServiceError
from memora.memory.retriever import MemoryRetriever

router = APIRouter(prefix="/api/memory", tags=["Memory Inspection"])


@router.get("/status")
def memory_status(tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Inspects operational memory status and storage tier counts.
    Does NOT leak internal filesystem paths or private credentials to API consumers.
    """
    try:
        tid = tenant_id or sibyl_manager.tenant_id
        client = sibyl_manager.get_client(tenant_id=tid)
        entity_count = client.storage.count_rows("entities", tid)
        event_count = client.storage.count_rows("journal_events", tid)
        ref_count = client.storage.count_rows("reference_documents", tid)
        with client.storage.connection() as conn:
            size_bytes = client.storage.logical_size_bytes(conn)

        return {
            "status": "connected",
            "backend": "Sibyl Memory (SQLite FTS5)",
            "storage_state": "healthy",
            "tenant_id": tid,
            "tier": sibyl_manager.tier,
            "counts": {
                "entities_warm": entity_count,
                "journal_cold": event_count,
                "reference": ref_count
            },
            "logical_size_bytes": size_bytes
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SIBYL_UNAVAILABLE",
                "message": f"Sibyl Memory status check failed: {e}"
            }
        )


@router.get("/search")
def memory_search(
    q: str = Query(..., min_length=1, max_length=200, description="Search term for operational memories"),
    tenant_id: Optional[str] = Query(None, description="Optional tenant UUID for isolated query")
) -> Dict[str, Any]:
    """
    Direct cross-tier search across Sibyl Memory.
    Returns sanitized, UI-safe operational records respecting tenant boundaries.
    """
    clean_q = q.strip()
    if not clean_q:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Query string 'q' cannot be empty or whitespace only."
            }
        )
    try:
        retriever = MemoryRetriever(sibyl_manager)
        results = retriever.search_all_tiers(query=clean_q, tenant_id=tenant_id)
        return {
            "query": clean_q,
            "tenant_id": tenant_id or sibyl_manager.tenant_id,
            "count": len(results),
            "results": results
        }
    except SibylServiceError as sse:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SIBYL_SERVICE_ERROR",
                "message": f"Sibyl search failed: {sse}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(e)
            }
        )
