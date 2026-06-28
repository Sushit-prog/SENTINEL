"""CURRENCYGuard LangGraph agent — currency authentication pipeline."""

import logging
import uuid
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.llm import get_llm
from backend.core.intelligence_store import get_intelligence_store
from backend.modules.currencyguard.opencv_analyzer import analyze_currency_image
from backend.modules.currencyguard.report_builder import generate_currency_report
from backend.models.currency_models import (
    CurrencyAnalysisResponse, FeatureCheckResult, AuthenticityVerdict
)

logger = logging.getLogger(__name__)


class CurrencyAnalysisState(TypedDict):
    image_bytes: bytes
    denomination: str
    opencv_result: dict
    llm_reasoning: str
    final_verdict: str
    final_confidence: float
    pdf_bytes: bytes
    analysis_id: str


def opencv_analysis_node(state: CurrencyAnalysisState) -> CurrencyAnalysisState:
    """Run OpenCV feature checks on the currency image."""
    logger.info("CURRENCYGuard: Running OpenCV analysis")
    result = analyze_currency_image(
        state["image_bytes"],
        state["denomination"]
    )
    state["opencv_result"] = result
    state["denomination"] = result["denomination"]
    state["analysis_id"] = str(uuid.uuid4())[:8]
    return state


def llm_synthesis_node(state: CurrencyAnalysisState) -> CurrencyAnalysisState:
    """LLM synthesizes OpenCV results into final verdict with reasoning."""
    logger.info("CURRENCYGuard: Running LLM synthesis")
    llm = get_llm(temperature=0.05)
    result = state["opencv_result"]

    checks_summary = "\n".join([
        f"- {c['feature_name']}: {'PASS' if c['passed'] else 'FAIL'} "
        f"(confidence: {c['confidence']:.2f}) — {c['details']}"
        for c in result["feature_checks"]
    ])

    system_prompt = """You are an expert RBI currency authentication specialist with 20 years of experience.
You are analyzing computer vision results from automated currency verification checks.

Your job is to synthesize the technical findings into a clear, authoritative verdict.

Respond in this exact format:
VERDICT: [GENUINE/SUSPECT/COUNTERFEIT/INCONCLUSIVE]
CONFIDENCE: [0.0-1.0]
REASONING: [2-3 sentences explaining the verdict based on the checks]
KEY_CONCERN: [The single most important finding, or NONE if genuine]
RECOMMENDATION: [Action for the bank teller or field officer]"""

    user_message = f"""Denomination: Rs.{result['denomination']}
OpenCV Verdict: {result['opencv_verdict']}
Overall Score: {result['overall_score']}
Checks Passed: {result['checks_passed']}/{result['checks_total']}
Image: {result['image_shape']}

Feature Check Results:
{checks_summary}

Synthesize these findings into a final authentication verdict."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ])

    content = response.content
    state["llm_reasoning"] = content

    def extract(label):
        for line in content.split("\n"):
            if line.strip().startswith(f"{label}:"):
                return line.split(":", 1)[1].strip()
        return ""

    verdict_str = extract("VERDICT").upper()
    valid_verdicts = ["GENUINE", "SUSPECT", "COUNTERFEIT", "INCONCLUSIVE"]
    state["final_verdict"] = verdict_str if verdict_str in valid_verdicts else result["opencv_verdict"]

    try:
        state["final_confidence"] = float(extract("CONFIDENCE"))
    except Exception:
        state["final_confidence"] = result["overall_score"]

    return state


def generate_report_node(state: CurrencyAnalysisState) -> CurrencyAnalysisState:
    """Generate PDF report."""
    logger.info("CURRENCYGuard: Generating PDF report")
    try:
        pdf_bytes = generate_currency_report(
            analysis_id=state["analysis_id"],
            denomination=state["denomination"],
            verdict=state["final_verdict"],
            confidence=state["final_confidence"],
            feature_checks=state["opencv_result"]["feature_checks"],
            ai_reasoning=state["llm_reasoning"],
        )
        state["pdf_bytes"] = pdf_bytes
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        state["pdf_bytes"] = b""
    return state


def store_intelligence_node(state: CurrencyAnalysisState) -> CurrencyAnalysisState:
    """Store counterfeit events in shared intelligence store."""
    logger.info("CURRENCYGuard: Storing intelligence")
    try:
        if state["final_verdict"] in ["COUNTERFEIT", "SUSPECT"]:
            store = get_intelligence_store()
            description = (
                f"Counterfeit/suspect Rs.{state['denomination']} note detected. "
                f"Verdict: {state['final_verdict']}. "
                f"Confidence: {state['final_confidence']:.2f}. "
                f"Checks passed: {state['opencv_result']['checks_passed']}/"
                f"{state['opencv_result']['checks_total']}."
            )
            store.add_currency_event(
                event_id=state["analysis_id"],
                description=description,
                metadata={
                    "denomination": state["denomination"],
                    "verdict": state["final_verdict"],
                    "confidence": state["final_confidence"],
                }
            )
    except Exception as e:
        logger.warning(f"Intelligence store update failed: {e}")
    return state


def build_currency_agent():
    graph = StateGraph(CurrencyAnalysisState)
    graph.add_node("opencv_analysis", opencv_analysis_node)
    graph.add_node("llm_synthesis", llm_synthesis_node)
    graph.add_node("generate_report", generate_report_node)
    graph.add_node("store_intelligence", store_intelligence_node)
    graph.set_entry_point("opencv_analysis")
    graph.add_edge("opencv_analysis", "llm_synthesis")
    graph.add_edge("llm_synthesis", "generate_report")
    graph.add_edge("generate_report", "store_intelligence")
    graph.add_edge("store_intelligence", END)
    return graph.compile()


currency_agent = build_currency_agent()


def run_currency_analysis(image_bytes: bytes, denomination: str = "unknown") -> tuple:
    """
    Main entry point for CURRENCYGuard.
    Returns (CurrencyAnalysisResponse, pdf_bytes)
    """
    initial_state: CurrencyAnalysisState = {
        "image_bytes": image_bytes,
        "denomination": denomination,
        "opencv_result": {},
        "llm_reasoning": "",
        "final_verdict": "INCONCLUSIVE",
        "final_confidence": 0.0,
        "pdf_bytes": b"",
        "analysis_id": "",
    }

    final_state = currency_agent.invoke(initial_state)

    def extract(label):
        for line in final_state["llm_reasoning"].split("\n"):
            if line.strip().startswith(f"{label}:"):
                return line.split(":", 1)[1].strip()
        return ""

    feature_checks = [
        FeatureCheckResult(
            feature_name=c["feature_name"],
            passed=c["passed"],
            confidence=c["confidence"],
            details=c["details"]
        )
        for c in final_state["opencv_result"].get("feature_checks", [])
    ]

    response = CurrencyAnalysisResponse(
        verdict=AuthenticityVerdict(final_state["final_verdict"]),
        confidence=final_state["final_confidence"],
        denomination=final_state["denomination"],
        feature_checks=feature_checks,
        ai_reasoning=extract("REASONING") or final_state["llm_reasoning"][:300],
        risk_summary=extract("KEY_CONCERN") or "See full report",
        analysis_id=final_state["analysis_id"],
        report_available=len(final_state["pdf_bytes"]) > 0,
    )

    return response, final_state["pdf_bytes"]
