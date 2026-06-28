from fastapi import APIRouter, HTTPException, UploadFile, File
import logging
from backend.models.currency_models import CurrencyAnalysisResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=CurrencyAnalysisResponse)
async def analyze_currency(file: UploadFile = File(...)):
    """Analyze uploaded currency note image for authenticity."""
    try:
        raise HTTPException(status_code=501, detail="CURRENCYGuard not yet implemented")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CURRENCYGuard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
