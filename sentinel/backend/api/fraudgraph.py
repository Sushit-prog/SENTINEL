"""FRAUDGraph API — Graph AI fraud network mapping and evidence packaging.

Analyses phone numbers, bank accounts, device fingerprints, and victim statements
to map coordinated fraud campaigns. Generates interactive network graphs,
court-admissible PDF reports, and ZIP evidence kits.
"""

import os
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from backend.models.fraud_models import FraudAnalysisRequest, FraudAnalysisResponse
from backend.agents.fraud_agent import run_fraud_analysis

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session store: session_id -> pdf_path
_session_pdfs: dict = {}

# In-memory cache for full analysis results (needed for evidence kit)
_session_results: dict = {}


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

        # Cache full result for evidence kit retrieval
        _session_results[result.session_id] = {
            "entities": result.entities,
            "relationships": result.relationships,
            "clusters": result.clusters,
            "risk_level": result.risk_level.value,
            "risk_score": result.risk_score,
            "llm_summary": result.llm_summary,
            "graph_html": result.graph_html,
            "neo4j_connected": result.neo4j_connected,
            "timestamp": datetime.utcnow().isoformat(),
        }

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


@router.get("/evidence-kit/{session_id}")
async def download_evidence_kit(session_id: str):
    """
    GET /api/fraudgraph/evidence-kit/{session_id}
    Returns a ZIP bundle containing PDF report, graph HTML, entity CSV,
    analysis JSON, and manifest -- court-admissible evidence package.
    """
    try:
        from backend.modules.fraudgraph.report_builder import build_evidence_kit

        cached = _session_results.get(session_id)
        if not cached:
            pdf_filename = f"SENTINEL_FRAUD_INTELLIGENCE_{session_id[:8].upper()}.pdf"
            pdf_path = os.path.join("reports", pdf_filename)
            if not os.path.exists(pdf_path) and session_id not in _session_pdfs:
                raise HTTPException(status_code=404, detail="Analysis not found. Run analysis first.")
            cached = {
                "entities": [],
                "relationships": [],
                "clusters": [],
                "risk_level": "UNKNOWN",
                "risk_score": 0.0,
                "llm_summary": "LLM summary not available in cache.",
                "graph_html": "",
                "neo4j_connected": False,
                "timestamp": datetime.utcnow().isoformat(),
            }

        zip_bytes = build_evidence_kit(
            session_id=session_id,
            entities=cached["entities"],
            relationships=cached["relationships"],
            clusters=cached["clusters"],
            risk_level=cached["risk_level"],
            risk_score=cached["risk_score"],
            llm_summary=cached["llm_summary"],
            graph_html=cached.get("graph_html", ""),
            neo4j_connected=cached.get("neo4j_connected", False),
        )

        return StreamingResponse(
            iter([zip_bytes]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=evidence_kit_{session_id[:8].upper()}.zip"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evidence kit generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evidence kit failed: {str(e)}")


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
