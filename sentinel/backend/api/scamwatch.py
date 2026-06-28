"""SCAMWatch API routes."""

import logging
from fastapi import APIRouter, HTTPException
from backend.models.scam_models import ScamAnalysisRequest, ScamAnalysisResponse
from backend.agents.scam_agent import run_scam_analysis
from backend.modules.scamwatch.patterns import SCAM_PATTERNS

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=ScamAnalysisResponse)
async def analyze_scam(request: ScamAnalysisRequest):
    """Analyze text for scam patterns and return risk assessment."""
    try:
        logger.info(f"SCAMWatch analysis request — channel: {request.channel}")
        result = run_scam_analysis(
            text=request.text,
            channel=request.channel or "unknown"
        )
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
