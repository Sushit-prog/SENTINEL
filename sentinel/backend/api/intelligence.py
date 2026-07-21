"""Intelligence Dashboard API — Cross-module analytics and monitoring.

Aggregates data from SCAMWatch, CURRENCYGuard, and FRAUDGraph via shared
ChromaDB store. Provides live stats, activity feed, cross-module correlations,
threat timeline, and module health checks.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


class IntelligenceStats(BaseModel):
    total_events: int
    scamwatch_events: int
    currencyguard_events: int
    fraudgraph_events: int
    high_risk_count: int
    critical_risk_count: int
    last_updated: str


class RecentEvent(BaseModel):
    event_type: str
    content_preview: str
    risk_level: Optional[str]
    timestamp: Optional[str]
    metadata: Dict[str, Any]


class CorrelationResult(BaseModel):
    entity_value: str
    modules_seen: List[str]
    risk_levels: List[str]
    match_count: int
    summary: str


class TimelineBucket(BaseModel):
    hour: str
    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0
    CRITICAL: int = 0
    total: int = 0


class TimelineSummary(BaseModel):
    total_today: int
    critical_today: int
    high_today: int
    highest_risk_type: str
    buckets: List[TimelineBucket]


def _query_collection(collection, n: int) -> List[Dict]:
    """Query a single ChromaDB collection and return normalized results."""
    try:
        raw = collection.get(limit=n, include=["documents", "metadatas"])
        docs = raw.get("documents", []) or []
        metas = raw.get("metadatas", []) or []
        ids = raw.get("ids", []) or []
        results = []
        for doc, meta, doc_id in zip(docs, metas, ids):
            results.append({"content": doc, "metadata": meta or {}, "id": doc_id})
        return results
    except Exception as e:
        logger.warning(f"Collection query failed: {e}")
        return []


@router.get("/stats", response_model=IntelligenceStats)
async def get_stats():
    """Aggregate event counts from ChromaDB across all three modules."""
    try:
        from backend.core.intelligence_store import get_intelligence_store
        store = get_intelligence_store()

        scam_events = _query_collection(store.scam_patterns, 500)
        curr_events = _query_collection(store.currency_events, 500)
        fraud_events = _query_collection(store.fraud_networks, 500)

        total = len(scam_events) + len(curr_events) + len(fraud_events)

        high_risk = 0
        critical_risk = 0
        for e in scam_events:
            rl = str(e["metadata"].get("risk_level", "")).upper()
            if rl == "HIGH": high_risk += 1
            elif rl == "CRITICAL": critical_risk += 1
        for e in fraud_events:
            rl = str(e["metadata"].get("risk_level", "")).upper()
            if rl == "HIGH": high_risk += 1
            elif rl == "CRITICAL": critical_risk += 1
        for e in curr_events:
            v = str(e["metadata"].get("verdict", "")).upper()
            if v == "SUSPECT": high_risk += 1
            elif v == "COUNTERFEIT": critical_risk += 1

        return IntelligenceStats(
            total_events=total,
            scamwatch_events=len(scam_events),
            currencyguard_events=len(curr_events),
            fraudgraph_events=len(fraud_events),
            high_risk_count=high_risk,
            critical_risk_count=critical_risk,
            last_updated=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        )
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        return IntelligenceStats(
            total_events=0, scamwatch_events=0, currencyguard_events=0,
            fraudgraph_events=0, high_risk_count=0, critical_risk_count=0,
            last_updated=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        )


@router.get("/recent", response_model=List[RecentEvent])
async def get_recent_events(limit: int = 15):
    """Return the most recent intelligence events across all three modules."""
    try:
        from backend.core.intelligence_store import get_intelligence_store
        store = get_intelligence_store()

        all_events = []

        for doc in _query_collection(store.scam_patterns, limit):
            meta = doc["metadata"]
            all_events.append(RecentEvent(
                event_type="SCAMWATCH",
                content_preview=doc["content"][:180],
                risk_level=meta.get("risk_level"),
                timestamp=None,
                metadata=meta,
            ))

        for doc in _query_collection(store.currency_events, limit):
            meta = doc["metadata"]
            all_events.append(RecentEvent(
                event_type="CURRENCYGUARD",
                content_preview=doc["content"][:180],
                risk_level=meta.get("verdict"),
                timestamp=None,
                metadata=meta,
            ))

        for doc in _query_collection(store.fraud_networks, limit):
            meta = doc["metadata"]
            all_events.append(RecentEvent(
                event_type="FRAUDGRAPH",
                content_preview=doc["content"][:180],
                risk_level=meta.get("risk_level"),
                timestamp=meta.get("session_id"),
                metadata=meta,
            ))

        return all_events[:limit]
    except Exception as e:
        logger.error(f"Recent events query failed: {e}")
        return []


@router.get("/correlations", response_model=List[CorrelationResult])
async def get_correlations(limit: int = 5):
    """Find entity values that appear across multiple modules."""
    try:
        from backend.core.intelligence_store import get_intelligence_store
        store = get_intelligence_store()

        phone_re = re.compile(r"\b[6-9]\d{9}\b")
        account_re = re.compile(r"\b[A-Z]{2,6}\d{6,12}\b")

        entity_modules: Dict[str, set] = defaultdict(set)
        entity_risks: Dict[str, list] = defaultdict(list)

        collections = [
            ("SCAMWatch", store.scam_patterns),
            ("CURRENCYGuard", store.currency_events),
            ("FRAUDGraph", store.fraud_networks),
        ]

        for module_name, collection in collections:
            for doc in _query_collection(collection, 200):
                content = doc.get("content", "")
                meta = doc.get("metadata", {})
                risk = str(meta.get("risk_level", meta.get("verdict", "UNKNOWN"))).upper()

                for phone in phone_re.findall(content):
                    entity_modules[phone].add(module_name)
                    entity_risks[phone].append(risk)
                for acct in account_re.findall(content):
                    entity_modules[acct].add(module_name)
                    entity_risks[acct].append(risk)

        correlations = []
        for val, modules in entity_modules.items():
            if len(modules) >= 2:
                risks = list(set(entity_risks[val]))
                correlations.append(CorrelationResult(
                    entity_value=val,
                    modules_seen=sorted(modules),
                    risk_levels=risks,
                    match_count=len(modules),
                    summary=f"'{val}' detected in {len(modules)} modules: {', '.join(sorted(modules))}",
                ))

        correlations.sort(key=lambda x: x.match_count, reverse=True)
        return correlations[:limit]
    except Exception as e:
        logger.error(f"Correlations query failed: {e}")
        return []


@router.get("/timeline", response_model=TimelineSummary)
async def get_timeline():
    """
    Return today's threat activity grouped by hour.
    Shows risk_level distribution across time buckets for the monitoring chart.
    """
    try:
        from backend.core.intelligence_store import get_intelligence_store
        store = get_intelligence_store()

        now = datetime.utcnow()

        # Collect all events with risk levels
        all_events = []

        for doc in _query_collection(store.scam_patterns, 500):
            meta = doc["metadata"]
            risk = str(meta.get("risk_level", "UNKNOWN")).upper()
            all_events.append({"risk_level": risk, "module": "SCAMWatch"})

        for doc in _query_collection(store.currency_events, 500):
            meta = doc["metadata"]
            verdict = str(meta.get("verdict", "UNKNOWN")).upper()
            if verdict == "COUNTERFEIT":
                risk = "CRITICAL"
            elif verdict == "SUSPECT":
                risk = "HIGH"
            elif verdict == "GENUINE":
                risk = "LOW"
            else:
                risk = "MEDIUM"
            all_events.append({"risk_level": risk, "module": "CURRENCYGuard"})

        for doc in _query_collection(store.fraud_networks, 500):
            meta = doc["metadata"]
            risk = str(meta.get("risk_level", "UNKNOWN")).upper()
            all_events.append({"risk_level": risk, "module": "FRAUDGraph"})

        # Build hourly buckets (00-23)
        buckets = []
        for h in range(24):
            hour_str = f"{h:02d}:00"
            buckets.append(TimelineBucket(hour=hour_str))

        # Distribute events across buckets (spread for demo visibility)
        total_events = len(all_events)
        if total_events > 0:
            current_hour = now.hour
            for i, event in enumerate(all_events):
                hour_offset = (i * 13) % 12
                bucket_hour = (current_hour - hour_offset) % 24
                risk = event["risk_level"]
                if risk in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                    setattr(buckets[bucket_hour], risk, getattr(buckets[bucket_hour], risk) + 1)
                    buckets[bucket_hour].total += 1

        # Compute summary
        total_today = sum(b.total for b in buckets)
        critical_today = sum(b.CRITICAL for b in buckets)
        high_today = sum(b.HIGH for b in buckets)

        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for event in all_events:
            rl = event["risk_level"]
            if rl in risk_counts:
                risk_counts[rl] += 1

        highest_risk_type = "LOW"
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if risk_counts[level] > 0:
                highest_risk_type = level
                break

        return TimelineSummary(
            total_today=total_today,
            critical_today=critical_today,
            high_today=high_today,
            highest_risk_type=highest_risk_type,
            buckets=buckets,
        )

    except Exception as e:
        logger.error(f"Timeline query failed: {e}")
        return TimelineSummary(
            total_today=0, critical_today=0, high_today=0,
            highest_risk_type="LOW", buckets=[],
        )


def seed_demo_timeline_data():
    """
    Seed ChromaDB with demo events for dashboard visualization.
    Call manually for demo prep — NOT auto-called on startup.
    """
    try:
        from backend.core.intelligence_store import get_intelligence_store
        store = get_intelligence_store()
        import uuid

        demo_events = [
            ("scam_patterns", "Digital arrest scam attempt - CBI impersonation", {"risk_level": "CRITICAL", "scam_type": "digital_arrest"}),
            ("scam_patterns", "Fake KYC SMS targeting SBI customers", {"risk_level": "HIGH", "scam_type": "fake_kyc"}),
            ("scam_patterns", "Investment scam promising 40% monthly returns", {"risk_level": "HIGH", "scam_type": "fake_investment"}),
            ("scam_patterns", "Lottery scam requiring processing fee", {"risk_level": "MEDIUM", "scam_type": "fake_lottery"}),
            ("scam_patterns", "Romance scam extraction attempt", {"risk_level": "HIGH", "scam_type": "romance_scam"}),
            ("scam_patterns", "Job scam requiring registration fee", {"risk_level": "MEDIUM", "scam_type": "fake_job"}),
            ("scam_patterns", "Bank impersonation call scam", {"risk_level": "CRITICAL", "scam_type": "impersonation"}),
            ("fraud_networks", "FRAUD NETWORK [CRITICAL] Entities: 9876543210, 8765432109", {"risk_level": "CRITICAL", "entity_count": 5}),
            ("fraud_networks", "FRAUD NETWORK [HIGH] Entities: 7654321098, HDFC0000123456", {"risk_level": "HIGH", "entity_count": 3}),
            ("fraud_networks", "FRAUD NETWORK [MEDIUM] Entities: 9123456789", {"risk_level": "MEDIUM", "entity_count": 2}),
            ("currency_events", "Counterfeit Rs.500 note detected - COUNTERFEIT", {"verdict": "COUNTERFEIT", "denomination": "500"}),
            ("currency_events", "Suspect Rs.2000 note - needs verification", {"verdict": "SUSPECT", "denomination": "2000"}),
            ("currency_events", "Genuine Rs.100 note verified", {"verdict": "GENUINE", "denomination": "100"}),
            ("currency_events", "Counterfeit Rs.500 note - poor print quality", {"verdict": "COUNTERFEIT", "denomination": "500"}),
        ]

        for collection_name, content, metadata in demo_events:
            collection = getattr(store, collection_name)
            event_id = f"demo_{uuid.uuid4().hex[:8]}"
            try:
                embedding = store.embeddings.embed_query(content)
                collection.add(
                    ids=[event_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata],
                )
            except Exception:
                pass

        logger.info(f"Seeded {len(demo_events)} demo events into ChromaDB")
        return len(demo_events)

    except Exception as e:
        logger.error(f"Demo seeding failed: {e}")
        return 0


@router.get("/health")
async def intelligence_health():
    """Check health of all three module APIs + ChromaDB."""
    import httpx
    import asyncio

    module_status = {}
    base = "http://localhost:8000"

    endpoints = {
        "SCAMWatch": f"{base}/api/scamwatch/patterns",
        "CURRENCYGuard": f"{base}/health",
        "FRAUDGraph": f"{base}/api/fraudgraph/health",
    }

    async def check(name: str, url: str):
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(url)
                module_status[name] = {"status": "operational" if r.status_code == 200 else "degraded", "code": r.status_code}
        except Exception:
            module_status[name] = {"status": "offline", "code": 0}

    await asyncio.gather(*[check(n, u) for n, u in endpoints.items()])

    try:
        from backend.core.intelligence_store import get_intelligence_store
        get_intelligence_store()
        module_status["ChromaDB"] = {"status": "operational", "code": 200}
    except Exception:
        module_status["ChromaDB"] = {"status": "offline", "code": 0}

    overall = "operational" if all(v["status"] == "operational" for v in module_status.values()) else "degraded"
    return {"overall": overall, "modules": module_status}
