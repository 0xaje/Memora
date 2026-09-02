"""
Outcome API Routes.
Exposes endpoints to record follow-up results and store operational lessons.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from memora.incidents.models import OutcomeCreate
from memora.incidents.service import IncidentService
from memora.memory.client import SibylServiceError

router = APIRouter(prefix="/api/outcomes", tags=["Outcomes"])


def get_incident_service() -> IncidentService:
    return IncidentService()


@router.post("", response_model=Dict[str, Any])
def record_outcome(
    payload: OutcomeCreate,
    service: IncidentService = Depends(get_incident_service)
):
    """
    Record an incident outcome.
    If the incident is unresolved, persists an UnresolvedRiskMemory and OperationalLesson into Sibyl.
    """
    try:
        result = service.record_outcome(payload)
        return result
    except SibylServiceError as sse:
        raise HTTPException(
            status_code=503,
            detail=f"Sibyl Memory storage failure: {sse}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
