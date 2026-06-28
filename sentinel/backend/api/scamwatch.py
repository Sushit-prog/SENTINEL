from fastapi import APIRouter, HTTPException
import logging
from backend.models.scam_models import ScamAnalysisRequest, ScamAnalysisResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=ScamAnalysisResponse)
async def analyze_scam(request: ScamAnalysisRequest):
    """Analyze text for scam patterns and return risk assessment."""
    try:
        # Agent will be wired here in Phase 1
        raise HTTPException(status_code=501, detail="SCAMWatch agent not yet implemented")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SCAMWatch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns")
async def get_known_patterns():
    """Return list of known scam pattern categories."""
    return {"patterns": [], "status": "Phase 1 pending"}
