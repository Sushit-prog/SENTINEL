import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.models.fraud_models import FraudAnalysisRequest, FraudAnalysisResponse
from backend.agents.fraud_agent import run_fraud_analysis

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session store: session_id -> pdf_path
_session_pdfs: dict = {}


@router.post("/analyze", response_model=FraudAnalysisResponse)
async def analyze_fraud_network(request: FraudAnalysisRequest):
    """
    POST /api/fraudgraph/analyze
    Body: {
        "phones": ["9876543210", "8765432109"],
        "accounts": ["ACC123456", "ACC789012"],
        "devices": ["IMEI:123456789"],
        "victim_statement": "I received a call from..."
    }
    Returns full fraud analysis with pyvis graph HTML, cluster data, PDF availability.
    """
    try:
        if not any([request.phones, request.accounts, request.devices, request.victim_statement]):
            raise HTTPException(
                status_code=400,
                detail="At least one of phones, accounts, devices, or victim_statement must be provided."
            )
        result = run_fraud_analysis(request)
        if result.pdf_available and result.session_id:
            pdf_filename = f"SENTINEL_FRAUD_INTELLIGENCE_{result.session_id[:8].upper()}.pdf"
            pdf_path = os.path.join("reports", pdf_filename)
            _session_pdfs[result.session_id] = pdf_path
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FRAUDGraph analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/report/{session_id}")
async def download_report(session_id: str):
    """
    GET /api/fraudgraph/report/{session_id}
    Returns the PDF intelligence package for the given session.
    """
    pdf_path = _session_pdfs.get(session_id)
    if not pdf_path or not os.path.exists(pdf_path):
        pdf_filename = f"SENTINEL_FRAUD_INTELLIGENCE_{session_id[:8].upper()}.pdf"
        pdf_path = os.path.join("reports", pdf_filename)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="Report not found. Run analysis first.")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(pdf_path)
    )


@router.get("/health")
async def fraudgraph_health():
    """Health check - verifies Neo4j connection status."""
    from backend.core.graph_db import get_graph_db
    db = get_graph_db()
    return {
        "module": "FRAUDGraph",
        "status": "operational",
        "neo4j_connected": db.is_connected,
        "neo4j_mode": "aura" if db.is_connected else "in-memory"
    }
