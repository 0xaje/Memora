"""
Operational Fact Extractor.
Extracts structured facts (location, incident type, entities, indicators) from raw text.
Implements deterministic extraction rules with fallback normalization.
"""

import re
import uuid
from typing import List, Tuple
from memora.incidents.models import IncidentFacts


class FactExtractor:
    """
    Extracts operational facts deterministically from incoming incident text.
    """

    LOCATION_PATTERNS = [
        re.compile(r"\b(Gate\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(Sector\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(Building\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(Perimeter\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(North|South|East|West)\s+(Wing|Entrance|Checkpoint|Gate)\b", re.IGNORECASE),
        re.compile(r"\b(Warehouse\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(Loading\s+Dock\s*\w*)\b", re.IGNORECASE)
    ]

    ENTITY_PATTERNS = [
        ("delivery vehicle", ["delivery vehicle", "van", "truck", "courier van", "delivery truck"]),
        ("unauthorized vehicle", ["vehicle", "car", "sedan", "suv"]),
        ("unidentified person", ["person", "individual", "trespasser", "intruder", "pedestrian"]),
        ("unattended package", ["package", "bag", "box", "briefcase", "container"])
    ]

    INDICATOR_PATTERNS = [
        ("suspicious activity", ["suspicious", "unusual", "loitering", "unauthorized", "unattended"]),
        ("repeat occurrence", ["again", "similar", "repeat", "recurrent", "second time", "multiple times"]),
        ("perimeter breach", ["breach", "fence", "barrier", "unauthorized entry"]),
        ("surveillance avoidance", ["avoiding camera", "obscured plate", "blind spot", "hood up"])
    ]

    def extract(self, raw_text: str, explicit_location: str = None, explicit_type: str = None) -> IncidentFacts:
        text = raw_text.strip()

        # 1. Location
        location = explicit_location
        if not location:
            for pattern in self.LOCATION_PATTERNS:
                match = pattern.search(text)
                if match:
                    location = match.group(1).title()
                    break
            if not location:
                location = "Unknown Facility Location"

        # 2. Entities involved
        entities: List[str] = []
        lower_text = text.lower()
        for entity_label, triggers in self.ENTITY_PATTERNS:
            if any(trigger in lower_text for trigger in triggers):
                entities.append(entity_label)

        # 3. Indicators
        indicators: List[str] = []
        for indicator_label, triggers in self.INDICATOR_PATTERNS:
            if any(trigger in lower_text for trigger in triggers):
                indicators.append(indicator_label)

        # 4. Incident Type
        incident_type = explicit_type
        if not incident_type:
            if "delivery vehicle" in entities or "vehicle" in lower_text:
                incident_type = "suspicious_vehicle"
            elif "unidentified person" in entities or "trespasser" in lower_text:
                incident_type = "unauthorized_person"
            elif "unattended package" in entities or "package" in lower_text:
                incident_type = "suspicious_package"
            else:
                incident_type = "security_observation"

        # Generate unique incident ID
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

        return IncidentFacts(
            incident_id=incident_id,
            location=location,
            incident_type=incident_type,
            summary=text,
            indicators=indicators,
            entities_involved=entities
        )
