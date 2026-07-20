"""
Known Indian fraud/cybercrime/FICN hotspot locations.
Based on publicly reported NCRB/RBI/MHA hotspot regions.
Used by the GeoIntel module to geolocate intelligence events.
"""

import random
from typing import List, Dict, Any

HOTSPOTS: List[Dict[str, Any]] = [
    # Jharkhand — India's scam call capital
    {"name": "Jamtara, Jharkhand", "lat": 23.9567, "lng": 86.8428, "primary_type": "SCAM", "description": "India's largest digital arrest and phishing scam hub"},
    {"name": "Deoghar, Jharkhand", "lat": 24.4767, "lng": 86.6944, "primary_type": "SCAM", "description": "Emerging cyber fraud cluster"},

    # Haryana — Mewat/Nuh organized fraud belt
    {"name": "Nuh (Mewat), Haryana", "lat": 28.1071, "lng": 77.0287, "primary_type": "FRAUD", "description": "Organized fraud ring operations, mule account networks"},

    # Rajasthan
    {"name": "Bharatpur, Rajasthan", "lat": 27.2170, "lng": 77.4895, "primary_type": "SCAM", "description": "Telecom fraud and digital arrest scam origin"},

    # Delhi NCR — counterfeit currency + scam operations
    {"name": "Delhi NCR", "lat": 28.6139, "lng": 77.2090, "primary_type": "COUNTERFEIT", "description": "Major FICN distribution hub and scam call centres"},
    {"name": "Noida, UP", "lat": 28.5355, "lng": 77.3910, "primary_type": "SCAM", "description": "Cyber fraud operations, call centre scams"},

    # Maharashtra
    {"name": "Mumbai, Maharashtra", "lat": 19.0760, "lng": 72.8777, "primary_type": "COUNTERFEIT", "description": "FICN circulation hub, financial fraud"},
    {"name": "Thane, Maharashtra", "lat": 19.2183, "lng": 72.9781, "primary_type": "FRAUD", "description": "Money mule network operations"},

    # West Bengal
    {"name": "Kolkata, West Bengal", "lat": 22.5726, "lng": 88.3639, "primary_type": "COUNTERFEIT", "description": "Border-state FICN entry and distribution point"},

    # Karnataka
    {"name": "Bengaluru, Karnataka", "lat": 12.9716, "lng": 77.5946, "primary_type": "SCAM", "description": "Tech-enabled fraud, cryptocurrency scams"},

    # Telangana
    {"name": "Hyderabad, Telangana", "lat": 17.3850, "lng": 78.4867, "primary_type": "SCAM", "description": "Digital arrest scam call centres, investment fraud"},

    # Bihar — emerging scam origin
    {"name": "Patna, Bihar", "lat": 25.6093, "lng": 85.1376, "primary_type": "SCAM", "description": "Emerging phishing and vishing operations"},

    # Uttar Pradesh
    {"name": "Ghaziabad, UP", "lat": 28.6692, "lng": 77.4538, "primary_type": "SCAM", "description": "Digital arrest scam operations"},

    # Gujarat
    {"name": "Ahmedabad, Gujarat", "lat": 23.0225, "lng": 72.5714, "primary_type": "COUNTERFEIT", "description": "FICN smuggling corridor via western border"},

    # Assam — eastern corridor
    {"name": "Guwahati, Assam", "lat": 26.1445, "lng": 91.7362, "primary_type": "FRAUD", "description": "Cross-border fraud network operations"},
]

# Map scam types from different modules to hotspot primary_type
SCAM_TYPE_TO_HOTSPOT_TYPE = {
    "digital_arrest": "SCAM",
    "fake_kyc": "SCAM",
    "fake_investment": "SCAM",
    "fake_job": "SCAM",
    "fake_lottery": "SCAM",
    "impersonation": "SCAM",
    "romance_scam": "SCAM",
    "COUNTERFEIT": "COUNTERFEIT",
    "GENUINE": "COUNTERFEIT",
    "SUSPECT": "COUNTERFEIT",
    "FRAUD_NETWORK": "FRAUD",
}

# Risk level to numeric score
RISK_SCORES = {
    "LOW": 0.25,
    "MEDIUM": 0.50,
    "HIGH": 0.75,
    "CRITICAL": 1.0,
    "GENUINE": 0.1,
    "SUSPECT": 0.6,
    "COUNTERFEIT": 0.9,
    "INCONCLUSIVE": 0.3,
}


def get_hotspots() -> List[Dict[str, Any]]:
    """Return the full list of known hotspots."""
    return HOTSPOTS


def assign_hotspot(event_type: str, risk_level: str) -> Dict[str, Any]:
    """
    Given an event type and risk level, pick the most relevant hotspot
    and return jittered coordinates near it.
    """
    lookup_key = event_type.upper().replace(" ", "_")
    hotspot_type = SCAM_TYPE_TO_HOTSPOT_TYPE.get(lookup_key, "SCAM")

    matching = [h for h in HOTSPOTS if h["primary_type"] == hotspot_type]
    if not matching:
        matching = HOTSPOTS

    risk_score = RISK_SCORES.get(str(risk_level).upper(), 0.5)
    if random.random() < risk_score and len(matching) > 1:
        metros = {"Delhi NCR", "Mumbai, Maharashtra", "Kolkata, West Bengal",
                  "Bengaluru, Karnataka", "Hyderabad, Telangana"}
        rural = [h for h in matching if h["name"] not in metros]
        if rural:
            matching = rural

    base = random.choice(matching)

    # Jitter by up to ~0.1 degrees (~11 km)
    jitter_lat = base["lat"] + random.uniform(-0.12, 0.12)
    jitter_lng = base["lng"] + random.uniform(-0.12, 0.12)

    return {
        "lat": round(jitter_lat, 4),
        "lng": round(jitter_lng, 4),
        "location_name": base["name"],
    }
