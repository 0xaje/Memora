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
        state_count = client.storage.count_rows("state_documents", tid)
        archive_count = client.storage.count_rows("archived_entities", tid)
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
                "reference": ref_count,
                "state_hot": state_count,
                "archived": archive_count,
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


@router.get("/tier")
def get_tier_status(tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Exposes official Sibyl storage tier status, soft cap consumption,
    and tier capabilities directly from the Sibyl SDK.
    """
    try:
        tid = tenant_id or sibyl_manager.tenant_id
        client = sibyl_manager.get_client(tenant_id=tid)
        status = client.free_tier_status()
        current_tier = client.get_tier()
        
        tier_capabilities = {
            "free": {
                "name": "Sibyl Community Free",
                "storage_limit": "5 MB Local SQLite Cap",
                "fts5_indexing": True,
                "multi_tier_architecture": True,
                "cold_audit_journal": True,
                "distributed_clustering": False
            },
            "pro": {
                "name": "Sibyl Professional",
                "storage_limit": "Uncapped Local / Cloud Persistent",
                "fts5_indexing": True,
                "multi_tier_architecture": True,
                "cold_audit_journal": True,
                "distributed_clustering": False
            },
            "enterprise": {
                "name": "Sibyl Enterprise Fleet",
                "storage_limit": "Uncapped Multi-Site Cluster",
                "fts5_indexing": True,
                "multi_tier_architecture": True,
                "cold_audit_journal": True,
                "distributed_clustering": True
            }
        }

        return {
            "current_tier": current_tier,
            "status": status,
            "tenant_id": tid,
            "capabilities": tier_capabilities.get(current_tier, tier_capabilities["free"])
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SIBYL_SERVICE_ERROR",
                "message": f"Failed querying Sibyl tier status: {e}"
            }
        )


@router.post("/tier")
def set_tier(payload: Dict[str, str], tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Escalates or switches the operational Sibyl storage tier.
    """
    requested_tier = payload.get("tier", "free").strip().lower()
    valid_tiers = ("free", "pro", "enterprise", "stake", "team", "lifetime")
    if requested_tier not in valid_tiers:
        raise HTTPException(
            status_code=422,
            detail={"code": "VALIDATION_ERROR", "message": f"Tier must be one of: {', '.join(valid_tiers)}."}
        )
    try:
        tid = tenant_id or sibyl_manager.tenant_id
        client = sibyl_manager.get_client(tenant_id=tid)
        client.set_tier(requested_tier)
        sibyl_manager.tier = requested_tier
        return {
            "status": "success",
            "active_tier": client.get_tier(),
            "message": f"Sibyl storage tier updated to '{requested_tier}'."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "TIER_UPDATE_ERROR", "message": str(e)}
        )


@router.get("/state/{key}")
def get_memory_state(key: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves transient active operational state from Sibyl's native HOT state tier.
    """
    try:
        tid = tenant_id or sibyl_manager.tenant_id
        client = sibyl_manager.get_client(tenant_id=tid)
        state_doc = client.get_state(key=key)
        if not state_doc:
            raise HTTPException(status_code=404, detail={"code": "STATE_NOT_FOUND", "message": f"Key '{key}' not found in HOT state tier."})
        return {"key": key, "tenant_id": tid, "state": state_doc}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "STATE_ERROR", "message": str(e)})


@router.post("/state/{key}")
def set_memory_state(key: str, payload: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Persists transient active operational state into Sibyl's native HOT state tier.
    """
    try:
        tid = tenant_id or sibyl_manager.tenant_id
        client = sibyl_manager.get_client(tenant_id=tid)
        result = client.set_state(key=key, body=payload)
        return {"status": "success", "key": key, "tenant_id": tid, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "STATE_ERROR", "message": str(e)})


@router.get("/reference/{key}")
def get_memory_reference(key: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves operational reference protocol document from Sibyl's native REFERENCE tier.
    """
    try:
        tid = tenant_id or sibyl_manager.tenant_id
        client = sibyl_manager.get_client(tenant_id=tid)
        ref_doc = client.get_reference(key=key)
        if not ref_doc:
            raise HTTPException(status_code=404, detail={"code": "REFERENCE_NOT_FOUND", "message": f"Reference '{key}' not found."})
        return {"key": key, "tenant_id": tid, "reference": ref_doc}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "REFERENCE_ERROR", "message": str(e)})


@router.post("/reference/{key}")
def set_memory_reference(key: str, payload: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Persists operational protocol document into Sibyl's native REFERENCE tier.
    """
    try:
        tid = tenant_id or sibyl_manager.tenant_id
        client = sibyl_manager.get_client(tenant_id=tid)
        result = client.set_reference(key=key, body=payload)
        return {"status": "success", "key": key, "tenant_id": tid, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "REFERENCE_ERROR", "message": str(e)})


@router.post("/archive")
def archive_memory_entity(payload: Dict[str, str], tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Moves an entity into Sibyl's native ARCHIVE tier (recoverable, kept out of active set).
    """
    category = payload.get("category")
    name = payload.get("name")
    if not category or not name:
        raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR", "message": "Both 'category' and 'name' are required."})
    try:
        tid = tenant_id or sibyl_manager.tenant_id
        client = sibyl_manager.get_client(tenant_id=tid)
        result = client.archive_entity(category=category, name=name)
        return {"status": "archived", "category": category, "name": name, "tenant_id": tid, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "ARCHIVE_ERROR", "message": str(e)})


@router.get("/lint")
def lint_memory(tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes Sibyl's native memory linter (requires paid/staker tier).
    Analyzes database size, tier counts, and memory health findings.
    """
    try:
        tid = tenant_id or sibyl_manager.tenant_id
        client = sibyl_manager.get_client(tenant_id=tid)
        report = client.lint()
        return {
            "tenant_id": report.tenant_id,
            "db_size_bytes": report.db_size_bytes,
            "counts": report.counts,
            "findings": report.findings,
            "started_at": report.started_at,
            "completed_at": report.completed_at
        }
    except Exception as e:
        # If free tier, provide honest diagnostic message
        if "requires a paid tier" in str(e):
            return {
                "tenant_id": tenant_id or sibyl_manager.tenant_id,
                "tier": "free",
                "linter_available": False,
                "message": "Sibyl memory linter requires a paid or staker tier ('stake', 'team', 'enterprise'). Free tier retains full 5-tier local storage and FTS5 search."
            }
        raise HTTPException(status_code=500, detail={"code": "LINT_ERROR", "message": str(e)})

