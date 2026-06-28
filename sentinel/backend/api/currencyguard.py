"""CURRENCYGuard API routes."""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from backend.models.currency_models import CurrencyAnalysisResponse
from backend.agents.currency_agent import run_currency_analysis

router = APIRouter()
logger = logging.getLogger(__name__)

_pdf_store = {}


@router.post("/analyze", response_model=CurrencyAnalysisResponse)
async def analyze_currency(
    file: UploadFile = File(...),
    denomination: str = Form(default="unknown")
):
    """Analyze uploaded currency note image for authenticity."""
    try:
        if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(
                status_code=400,
                detail="Only JPG and PNG images are supported."
            )

        image_bytes = await file.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large. Max 10MB.")

        logger.info(f"CURRENCYGuard: analyzing {file.filename}, denomination={denomination}")
        response, pdf_bytes = run_currency_analysis(image_bytes, denomination)

        if pdf_bytes:
            _pdf_store[response.analysis_id] = pdf_bytes

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CURRENCYGuard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{analysis_id}")
async def download_report(analysis_id: str):
    """Download PDF report for a completed analysis."""
    pdf_bytes = _pdf_store.get(analysis_id)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="Report not found or expired.")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=SENTINEL_{analysis_id}.pdf"}
    )
