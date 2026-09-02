"""
Baseline Assessment Engine.
Evaluates the incident strictly using current facts alone, with NO historical memory.
This provides the control baseline required for the deletion test and load-bearing proof.
"""

from memora.incidents.models import (
    IncidentFacts,
    BaselineAssessment,
    RiskLevel,
    RecommendationType
)


class BaselineEngine:
    """
    Assesses incidents in isolation based on current facts only.
    """

    def assess(self, facts: IncidentFacts) -> BaselineAssessment:
        factors = []
        risk = RiskLevel.LOW
        recommendation = RecommendationType.LOG_AND_PASS

        # Evaluate based purely on current observations
        has_suspicious = any("suspicious" in ind for ind in facts.indicators) or "suspicious" in facts.summary.lower()
        has_vehicle = "suspicious_vehicle" in facts.incident_type or any("vehicle" in e for e in facts.entities_involved)
        has_breach = any("breach" in ind for ind in facts.indicators)

        if has_breach:
            risk = RiskLevel.HIGH
            recommendation = RecommendationType.DISPATCH_PATROL
            factors.append("Active perimeter breach indicator observed.")
        elif has_suspicious and has_vehicle:
            # Standard single observation of suspicious vehicle at a gate
            risk = RiskLevel.MEDIUM
            recommendation = RecommendationType.MONITOR_AND_VERIFY
            factors.append("Single observation of suspicious delivery vehicle near gate.")
            factors.append("Standard security protocol: verify credentials and monitor area.")
        elif has_suspicious:
            risk = RiskLevel.MEDIUM
            recommendation = RecommendationType.MONITOR_AND_VERIFY
            factors.append("Unverified suspicious activity in security perimeter.")
        else:
            factors.append("Routine observation without explicit threat markers.")

        return BaselineAssessment(
            risk=risk,
            recommendation=recommendation,
            confidence=0.75,
            factors=factors
        )
