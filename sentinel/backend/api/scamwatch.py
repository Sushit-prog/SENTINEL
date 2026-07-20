"""SCAMWatch API routes."""

import logging
from fastapi import APIRouter, HTTPException
from backend.models.scam_models import ScamAnalysisRequest, ScamAnalysisResponse, CitizenAlert
from backend.agents.scam_agent import run_scam_analysis
from backend.modules.scamwatch.patterns import SCAM_PATTERNS

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cache: analysis_id -> ScamAnalysisResponse dict + channel
_analysis_cache: dict = {}


@router.post("/analyze", response_model=ScamAnalysisResponse)
async def analyze_scam(request: ScamAnalysisRequest):
    """Analyze text for scam patterns and return risk assessment."""
    try:
        logger.info(f"SCAMWatch analysis request — channel: {request.channel}, language: {request.language}")
        result = run_scam_analysis(
            text=request.text,
            channel=request.channel or "unknown",
            language=request.language or "en",
        )
        # Cache result for alert generation
        _analysis_cache[result.analysis_id] = {
            "result": result,
            "channel": request.channel or "unknown",
            "language": request.language or "en",
        }
        return result
    except Exception as e:
        logger.error(f"SCAMWatch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def get_known_patterns():
    """Return list of known scam pattern categories."""
    return {
        "total_patterns": len(SCAM_PATTERNS),
        "patterns": [
            {
                "type": k,
                "description": v["description"],
                "severity": v["severity"],
                "typical_channel": v["typical_channel"]
            }
            for k, v in SCAM_PATTERNS.items()
        ]
    }


@router.post("/alert/{analysis_id}", response_model=CitizenAlert)
async def generate_citizen_alert(analysis_id: str):
    """
    Generate a structured citizen alert from a completed scam analysis.
    Returns a CitizenAlert with verdict, actions, emergency contacts,
    and MHA alert payload.
    """
    try:
        cached = _analysis_cache.get(analysis_id)
        if not cached:
            raise HTTPException(status_code=404, detail="Analysis not found. Run analysis first.")

        from backend.modules.scamwatch.citizen_alert import build_citizen_alert
        alert = build_citizen_alert(
            analysis=cached["result"],
            channel=cached["channel"],
            language=cached.get("language", "en"),
        )
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Citizen alert generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
