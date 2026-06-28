from fastapi import APIRouter, HTTPException
import logging
from backend.models.fraud_models import FraudNetworkRequest, FraudNetworkResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=FraudNetworkResponse)
async def analyze_fraud_network(request: FraudNetworkRequest):
    """Build and analyze fraud network graph from provided identifiers."""
    try:
        raise HTTPException(status_code=501, detail="FRAUDGraph not yet implemented")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FRAUDGraph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
