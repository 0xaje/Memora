"""
Operational Fact Extractor.
Extracts structured facts (location, incident type, entities, indicators,
temporal references, duration, reported-by, entity attributes, and explicit unknowns)
from raw incident text.
Implements robust deterministic extraction rules with graceful fallbacks.
"""

import re
import uuid
from typing import List, Dict, Any, Optional
from memora.incidents.models import IncidentFacts


class FactExtractor:
    """
    Extracts operational facts deterministically from incoming incident text.
    Ensures zero hallucination and complete grounding in operator input.
    """

    LOCATION_PATTERNS = [
        re.compile(r"\b(Gate\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(Sector\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(Building\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(Perimeter\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(North|South|East|West)\s+(Wing|Entrance|Checkpoint|Gate|Perimeter)\b", re.IGNORECASE),
        re.compile(r"\b(Warehouse\s+\w+)\b", re.IGNORECASE),
        re.compile(r"\b(Loading\s+Dock\s*\w*)\b", re.IGNORECASE),
        re.compile(r"\b(Main\s+Entrance)\b", re.IGNORECASE),
        re.compile(r"\b(North\s+Lot|South\s+Lot|West\s+Lot|East\s+Lot)\b", re.IGNORECASE),
    ]

    ENTITY_PATTERNS = [
        ("delivery vehicle", ["delivery vehicle", "van", "truck", "courier van", "delivery truck", "delivery van", "maintenance truck"]),
        ("unauthorized vehicle", ["vehicle", "car", "sedan", "suv", "pickup"]),
        ("unidentified person", ["person", "individual", "trespasser", "intruder", "pedestrian", "subject"]),
        ("unattended package", ["package", "bag", "box", "briefcase", "container", "backpack"])
    ]

    INDICATOR_PATTERNS = [
        ("suspicious activity", ["suspicious", "unusual", "loitering", "unauthorized", "unattended", "lingering"]),
        ("repeat occurrence", ["again", "similar", "repeat", "recurrent", "second time", "third time", "seen earlier", "same "]),
        ("perimeter breach", ["breach", "fence", "barrier", "unauthorized entry", "climbing"]),
        ("surveillance avoidance", ["avoiding camera", "obscured plate", "blind spot", "hood up", "evading"])
    ]

    TIME_PATTERNS = [
        re.compile(r"\b(\d{1,2}:\d{2}(?:\s*(?:am|pm|hrs|hours))?)\b", re.IGNORECASE),
        re.compile(r"\b(?:approximately|around|at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", re.IGNORECASE),
        re.compile(r"\b(morning|afternoon|evening|night|midnight|dawn|dusk)\b", re.IGNORECASE)
    ]

    DURATION_PATTERNS = [
        re.compile(r"\b(?:for\s+)?(\d+\s*(?:minutes|hours|mins|seconds))\b", re.IGNORECASE),
        re.compile(r"\b(several\s+minutes|briefly|prolonged\s+period|few\s+minutes)\b", re.IGNORECASE)
    ]

    REPORTER_PATTERNS = [
        re.compile(r"\b(one\s+of\s+the\s+guards|security\s+guard|guard|patrol\s+officer|operator|dispatch|camera\s+operator|sensor|perimeter\s+alarm|field\s+officer)\b", re.IGNORECASE)
    ]

    COLOR_PATTERNS = ["white", "black", "silver", "gray", "grey", "red", "blue", "dark", "unmarked"]

    def extract(self, raw_text: str, explicit_location: str = None, explicit_type: str = None) -> IncidentFacts:
        text = raw_text.strip()
        lower_text = text.lower()

        # 1. Location extraction
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
        for entity_label, triggers in self.ENTITY_PATTERNS:
            if any(trigger in lower_text for trigger in triggers):
                entities.append(entity_label)

        # 3. Indicators
        indicators: List[str] = []
        for indicator_label, triggers in self.INDICATOR_PATTERNS:
            if any(trigger in lower_text for trigger in triggers):
                indicators.append(indicator_label)

        # 4. Temporal window
        approximate_time: Optional[str] = None
        for pattern in self.TIME_PATTERNS:
            match = pattern.search(text)
            if match:
                approximate_time = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
                break

        # 5. Duration
        duration: Optional[str] = None
        for pattern in self.DURATION_PATTERNS:
            match = pattern.search(text)
            if match:
                duration = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
                break

        # 6. Reporting source
        reported_by = "field_operator"
        for pattern in self.REPORTER_PATTERNS:
            match = pattern.search(text)
            if match:
                reported_by = match.group(1).lower()
                break

        # 7. Entity attributes
        entity_attributes: Dict[str, Any] = {}
        for color in self.COLOR_PATTERNS:
            if re.search(rf"\b{color}\b", lower_text):
                entity_attributes["color"] = color
                break
        if "van" in lower_text:
            entity_attributes["vehicle_type"] = "van"
        elif "truck" in lower_text:
            entity_attributes["vehicle_type"] = "truck"
        elif "sedan" in lower_text:
            entity_attributes["vehicle_type"] = "sedan"
        elif "car" in lower_text or "suv" in lower_text:
            entity_attributes["vehicle_type"] = "automobile"

        if any(w in lower_text for w in ["again", "same", "returned", "second time"]):
            entity_attributes["is_recurrent_mention"] = True

        # 8. Explicit Unknowns
        unknowns: List[str] = []
        if ("vehicle" in lower_text or "van" in lower_text or "truck" in lower_text):
            if not any(plate_word in lower_text for plate_word in ["plate", "license", "registration", "tag"]):
                unknowns.append("License plate / registration unverified")
            if not any(driver_word in lower_text for driver_word in ["driver identified", "driver known", "name:", "id:"]):
                unknowns.append("Driver / operator identity unverified")

        if not any(intent_word in lower_text for intent_word in ["authorized delivery", "work order", "scheduled", "permit"]):
            unknowns.append("Specific operational authorization unconfirmed")

        # 9. Incident Type
        incident_type = explicit_type
        if not incident_type:
            if "delivery vehicle" in entities or "vehicle" in lower_text or "truck" in lower_text:
                incident_type = "suspicious_vehicle"
            elif "unidentified person" in entities or "trespasser" in lower_text:
                incident_type = "unauthorized_person"
            elif "unattended package" in entities or "package" in lower_text:
                incident_type = "suspicious_package"
            else:
                incident_type = "security_observation"

        # Unique incident ID
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

        return IncidentFacts(
            incident_id=incident_id,
            location=location,
            incident_type=incident_type,
            summary=text,
            indicators=indicators,
            entities_involved=entities,
            approximate_time=approximate_time,
            duration=duration,
            reported_by=reported_by,
            entity_attributes=entity_attributes,
            unknowns=unknowns
        )
