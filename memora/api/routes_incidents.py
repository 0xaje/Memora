"""
Incident API Routes.
Exposes endpoints to create, analyze, and test operational incidents.
"""

from fastapi import APIRouter, HTTPException, Depends
from memora.incidents.models import IncidentCreate, IncidentAnalysisResult
from memora.incidents.service import IncidentService
from memora.memory.client import SibylServiceError

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


def get_incident_service() -> IncidentService:
    return IncidentService()


@router.post("/analyze", response_model=IncidentAnalysisResult)
def analyze_incident(
    payload: IncidentCreate,
    service: IncidentService = Depends(get_incident_service)
):
    """
    Intake and analyze an operational incident.
    Executes load-bearing Sibyl Memory retrieval, baseline assessment,
    comparison, memory-informed decision, and operational knowledge persistence.
    """
    try:
        result = service.analyze_incident(payload)
        return result
    except SibylServiceError as sse:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SIBYL_UNAVAILABLE",
                "message": f"Sibyl Memory unavailable or storage error: {sse}"
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
