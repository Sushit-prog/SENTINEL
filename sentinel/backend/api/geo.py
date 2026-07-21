"""GeoIntel API — Geospatial fraud intelligence and hotspot mapping.

Visualizes fraud, scam, and counterfeit incidents on an interactive map of India.
Uses 15 NCRB/RBI/MHA reported hotspot locations with smart geolocation assignment.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.geo_hotspots import get_hotspots, assign_hotspot, RISK_SCORES
from backend.core.intelligence_store import get_intelligence_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/geo", tags=["geo"])


class GeoIncident(BaseModel):
    id: str
    module: str
    type: str
    risk_level: str
    lat: float
    lng: float
    location_name: str
    timestamp: Optional[str] = None


class GeoHotspot(BaseModel):
    location_name: str
    lat: float
    lng: float
    count: int
    dominant_type: str
    risk_score: float


def _query_collection(collection, n: int) -> List[Dict]:
    """Query a single ChromaDB collection safely."""
    try:
        raw = collection.get(limit=n, include=["documents", "metadatas"])
        docs = raw.get("documents", []) or []
        metas = raw.get("metadatas", []) or []
        ids = raw.get("ids", []) or []
        return [{"id": doc_id, "content": doc, "metadata": meta or {}}
                for doc, meta, doc_id in zip(docs, metas, ids)]
    except Exception as e:
        logger.warning(f"Geo query collection failed: {e}")
        return []


@router.get("/incidents", response_model=List[GeoIncident])
async def get_incidents(limit: int = 100):
    """
    Recent incidents across all 3 modules, each assigned to a geolocated hotspot.
    Without real coordinates from users, events are placed near the most relevant
    known hotspot based on incident type.
    """
    try:
        store = get_intelligence_store()
        incidents = []

        # SCAMWatch events
        for doc in _query_collection(store.scam_patterns, limit):
            meta = doc["metadata"]
            risk = str(meta.get("risk_level", "UNKNOWN")).upper()
            scam_type = str(meta.get("scam_type", "SCAM")).upper()
            geo = assign_hotspot(scam_type, risk)
            incidents.append(GeoIncident(
                id=doc["id"],
                module="SCAMWatch",
                type=scam_type,
                risk_level=risk,
                lat=geo["lat"],
                lng=geo["lng"],
                location_name=geo["location_name"],
                timestamp=None,
            ))

        # CURRENCYGuard events
        for doc in _query_collection(store.currency_events, limit):
            meta = doc["metadata"]
            verdict = str(meta.get("verdict", "UNKNOWN")).upper()
            geo = assign_hotspot(verdict, verdict)
            incidents.append(GeoIncident(
                id=doc["id"],
                module="CURRENCYGuard",
                type=verdict,
                risk_level=verdict,
                lat=geo["lat"],
                lng=geo["lng"],
                location_name=geo["location_name"],
                timestamp=None,
            ))

        # FRAUDGraph events
        for doc in _query_collection(store.fraud_networks, limit):
            meta = doc["metadata"]
            risk = str(meta.get("risk_level", "UNKNOWN")).upper()
            geo = assign_hotspot("FRAUD_NETWORK", risk)
            incidents.append(GeoIncident(
                id=doc["id"],
                module="FRAUDGraph",
                type="FRAUD_NETWORK",
                risk_level=risk,
                lat=geo["lat"],
                lng=geo["lng"],
                location_name=geo["location_name"],
                timestamp=meta.get("session_id"),
            ))

        return incidents[:limit]

    except Exception as e:
        logger.error(f"Geo incidents query failed: {e}")
        return []


@router.get("/heatmap", response_model=List[GeoHotspot])
async def get_heatmap():
    """
    Aggregated incident counts per hotspot location.
    Returns data for heatmap visualization.
    """
    try:
        incidents = await get_incidents(limit=500)

        # Aggregate by location_name
        location_data = defaultdict(lambda: {"count": 0, "types": [], "risks": [], "lat": 0, "lng": 0})

        for inc in incidents:
            loc = inc.location_name
            location_data[loc]["count"] += 1
            location_data[loc]["types"].append(inc.type)
            location_data[loc]["risks"].append(inc.risk_level)
            location_data[loc]["lat"] = inc.lat
            location_data[loc]["lng"] = inc.lng

        heatspots = []
        for loc_name, data in location_data.items():
            # Dominant type = most frequent
            type_counts = defaultdict(int)
            for t in data["types"]:
                type_counts[t] += 1
            dominant_type = max(type_counts, key=type_counts.get) if type_counts else "UNKNOWN"

            # Risk score = max risk seen
            risk_score = max((RISK_SCORES.get(r, 0.0) for r in data["risks"]), default=0.0)

            heatspots.append(GeoHotspot(
                location_name=loc_name,
                lat=data["lat"],
                lng=data["lng"],
                count=data["count"],
                dominant_type=dominant_type,
                risk_score=round(risk_score, 3),
            ))

        heatspots.sort(key=lambda x: x.count, reverse=True)
        return heatspots

    except Exception as e:
        logger.error(f"Geo heatmap query failed: {e}")
        return []
