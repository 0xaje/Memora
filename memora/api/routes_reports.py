"""
Shift Handover & Operational Digest Routes.
Generates structured shift briefs from persistent Sibyl Memory.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from memora.memory.client import sibyl_manager
from memora.memory.models import MemoryCategory

router = APIRouter(prefix="/api/reports", tags=["Reports"])


class ShiftHandoverDigest(BaseModel):
    shift_period_hours: int
    generated_at: str
    tenant_id: str
    threat_level: str
    total_incidents_recorded: int
    active_unresolved_threats: List[Dict[str, Any]]
    failed_mitigations_to_avoid: List[Dict[str, Any]]
    operational_rules_active: List[Dict[str, Any]]
    supervisor_directives: List[str]


@router.get("/shift-handover", response_model=ShiftHandoverDigest)
def get_shift_handover_report(
    hours: int = Query(default=24, ge=1, le=720, description="Hours to look back"),
    tenant_id: Optional[str] = Query(default=None, description="Optional tenant identifier")
) -> ShiftHandoverDigest:
    """
    Generates a consolidated operational shift handover briefing.
    Queries Sibyl Memory for incidents, unresolved risks, failed mitigations,
    and synthesized lessons within the requested time window.
    """
    client = sibyl_manager.get_client(tenant_id=tenant_id)
    target_tenant = tenant_id or sibyl_manager.tenant_id
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    cutoff_iso = cutoff_time.isoformat()

    # 1. Retrieve all incidents
    all_incidents = client.list_entities(category=MemoryCategory.INCIDENTS.value, limit=100)
    shift_incidents = []
    for inc in all_incidents:
        body = inc.get("body", {})
        ts_str = body.get("timestamp") or inc.get("updated_at")
        if ts_str:
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt >= cutoff_time:
                    shift_incidents.append(body)
            except Exception:
                shift_incidents.append(body)
        else:
            shift_incidents.append(body)

    # 2. Retrieve unresolved risks
    all_risks = client.list_entities(category=MemoryCategory.UNRESOLVED_RISKS.value, limit=50)
    active_risks = []
    for r in all_risks:
        body = r.get("body", {})
        if body.get("status") in ("open", "unresolved") or r.get("status") in ("open", "unresolved"):
            active_risks.append({
                "risk_id": body.get("risk_id", r.get("name")),
                "location": body.get("location", "Perimeter"),
                "severity": body.get("severity", "HIGH"),
                "description": body.get("description", "Active hazard")
            })

    # 3. Retrieve outcomes and filter for failed mitigations
    all_outcomes = client.list_entities(category=MemoryCategory.OUTCOMES.value, limit=50)
    failed_mitigations = []
    for out in all_outcomes:
        body = out.get("body", {})
        if not body.get("is_resolved", True):
            failed_mitigations.append({
                "outcome_id": body.get("outcome_id", out.get("name")),
                "incident_id": body.get("incident_id"),
                "failed_action": body.get("action_taken"),
                "observed_result": body.get("observed_result"),
                "unresolved_reason": body.get("unresolved_reason")
            })

    # 4. Retrieve operational lessons
    all_lessons = client.list_entities(category=MemoryCategory.OPERATIONAL_LESSONS.value, limit=50)
    active_lessons = []
    for les in all_lessons:
        body = les.get("body", {})
        active_lessons.append({
            "lesson_id": body.get("lesson_id", les.get("name")),
            "location": body.get("location"),
            "operational_rule": body.get("operational_rule")
        })

    # 5. Directives & threat level
    threat_level = "CRITICAL" if len(active_risks) >= 3 else ("ELEVATED" if len(active_risks) > 0 else "NOMINAL")
    directives = []
    if active_risks:
        directives.append(f"Immediate physical inspection required at: {', '.join(set(r['location'] for r in active_risks))}.")
    if failed_mitigations:
        directives.append("Do NOT repeat passive monitoring for recurring unverified vehicles. Require physical escort or supervisory intercept.")
    if not directives:
        directives.append("Standard perimeter patrol schedule in effect. All previous shift mitigations verified resolved.")

    return ShiftHandoverDigest(
        shift_period_hours=hours,
        generated_at=datetime.now(timezone.utc).isoformat(),
        tenant_id=target_tenant,
        threat_level=threat_level,
        total_incidents_recorded=len(shift_incidents),
        active_unresolved_threats=active_risks,
        failed_mitigations_to_avoid=failed_mitigations,
        operational_rules_active=active_lessons,
        supervisor_directives=directives
    )
