"""SCAMWatch LangGraph agent — scam detection and risk assessment."""

import logging
import uuid
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.llm import get_llm
from backend.core.intelligence_store import get_intelligence_store
from backend.modules.scamwatch.classifier import ScamClassifier
from backend.modules.scamwatch.risk_scorer import RiskScorer
from backend.models.scam_models import (
    ScamAnalysisResponse, ScamIndicator, RiskLevel
)

logger = logging.getLogger(__name__)

classifier = ScamClassifier()
scorer = RiskScorer()


class ScamAnalysisState(TypedDict):
    text: str
    channel: str
    classification: dict
    llm_assessment: str
    llm_indicators: list
    risk_result: dict
    similar_patterns: int
    analysis_id: str


def classify_node(state: ScamAnalysisState) -> ScamAnalysisState:
    """Rule-based classification — fast, no API call."""
    logger.info("SCAMWatch: Running classifier")
    result = classifier.classify(state["text"])
    state["classification"] = result
    state["analysis_id"] = str(uuid.uuid4())[:8]
    return state


def llm_analysis_node(state: ScamAnalysisState) -> ScamAnalysisState:
    """LLM deep analysis of the text."""
    logger.info("SCAMWatch: Running LLM analysis")
    llm = get_llm(temperature=0.1)

    classification = state["classification"]
    pre_classification = classification.get("matched_scam_type", "unknown")
    keywords_found = classification.get("matched_keywords", [])
    urgency_signals = classification.get("urgency_signals", [])
    authority_signals = classification.get("authority_signals", [])

    system_prompt = """You are an expert cybercrime analyst specializing in Indian digital fraud.
Your job is to analyze text for scam patterns.

Known Indian scam types:
- Digital Arrest: Impersonating CBI/ED/Police, claiming victim is under digital arrest
- Fake KYC: Claiming bank KYC expired, account will be blocked
- Fake Investment: Promising guaranteed high returns
- Fake Job: Offering work from home jobs requiring registration fee
- Fake Lottery: Claiming victim won prize, requiring processing fee
- Impersonation: Pretending to be bank/government official
- Romance Scam: Building fake relationship to extract money

Respond in this exact format:
ASSESSMENT: [one paragraph analysis]
SCAM_TYPE: [specific type or LEGITIMATE]
RISK_LEVEL: [LOW/MEDIUM/HIGH/CRITICAL]
INDICATORS:
- [indicator 1]: [severity] — [explanation]
- [indicator 2]: [severity] — [explanation]
VERDICT: [one sentence verdict]
RECOMMENDED_ACTION: [specific action for the victim]"""

    user_message = f"""Analyze this text for scam patterns:

TEXT: {state["text"]}
CHANNEL: {state["channel"]}
PRE-CLASSIFICATION: {pre_classification}
KEYWORDS DETECTED: {keywords_found}
URGENCY SIGNALS: {urgency_signals}
AUTHORITY SIGNALS: {authority_signals}

Provide your expert analysis."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ])

    state["llm_assessment"] = response.content
    return state


def parse_llm_output_node(state: ScamAnalysisState) -> ScamAnalysisState:
    """Parse LLM response into structured indicators."""
    logger.info("SCAMWatch: Parsing LLM output")
    content = state["llm_assessment"]
    indicators = []

    lines = content.split("\n")
    in_indicators = False

    for line in lines:
        line = line.strip()
        if line.startswith("INDICATORS:"):
            in_indicators = True
            continue
        if in_indicators and line.startswith("- "):
            indicator_text = line[2:]
            if ":" in indicator_text and "—" in indicator_text:
                try:
                    name_part, rest = indicator_text.split(":", 1)
                    severity_part, explanation = rest.split("—", 1)
                    severity = severity_part.strip().upper()
                    if severity not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                        severity = "MEDIUM"
                    indicators.append({
                        "indicator": name_part.strip(),
                        "severity": severity,
                        "explanation": explanation.strip()
                    })
                except Exception:
                    indicators.append({
                        "indicator": indicator_text,
                        "severity": "MEDIUM",
                        "explanation": "Detected by AI analysis"
                    })
        elif in_indicators and line and not line.startswith("-"):
            if any(line.startswith(k) for k in ["VERDICT:", "RECOMMENDED_ACTION:"]):
                in_indicators = False

    state["llm_indicators"] = indicators
    return state


def score_node(state: ScamAnalysisState) -> ScamAnalysisState:
    """Calculate final risk score."""
    logger.info("SCAMWatch: Scoring risk")
    result = scorer.score(state["classification"], state["llm_assessment"])
    state["risk_result"] = result
    return state


def intelligence_store_node(state: ScamAnalysisState) -> ScamAnalysisState:
    """Store pattern in shared intelligence store if high risk."""
    logger.info("SCAMWatch: Updating intelligence store")
    try:
        risk_level = state["risk_result"]["risk_level"]
        if risk_level in ["HIGH", "CRITICAL"]:
            store = get_intelligence_store()
            store.add_scam_pattern(
                pattern_id=state["analysis_id"],
                text=state["text"],
                metadata={
                    "scam_type": state["classification"].get("matched_scam_type", "unknown"),
                    "risk_level": risk_level,
                    "risk_score": state["risk_result"]["risk_score"],
                    "channel": state["channel"],
                }
            )
            logger.info(f"Pattern stored in intelligence store: {state['analysis_id']}")

        result = store.query_similar_scams(state["text"], n_results=3)
        state["similar_patterns"] = len(result.get("ids", [[]])[0])
    except Exception as e:
        logger.warning(f"Intelligence store update failed: {e}")
        state["similar_patterns"] = 0

    return state


def build_scam_agent():
    """Build and compile the SCAMWatch LangGraph agent."""
    graph = StateGraph(ScamAnalysisState)

    graph.add_node("classify", classify_node)
    graph.add_node("llm_analysis", llm_analysis_node)
    graph.add_node("parse_output", parse_llm_output_node)
    graph.add_node("score", score_node)
    graph.add_node("store_intelligence", intelligence_store_node)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "llm_analysis")
    graph.add_edge("llm_analysis", "parse_output")
    graph.add_edge("parse_output", "score")
    graph.add_edge("score", "store_intelligence")
    graph.add_edge("store_intelligence", END)

    return graph.compile()


scam_agent = build_scam_agent()


def run_scam_analysis(text: str, channel: str = "unknown", language: str = "en") -> ScamAnalysisResponse:
    """Main entry point for SCAMWatch analysis."""
    initial_state: ScamAnalysisState = {
        "text": text,
        "channel": channel,
        "classification": {},
        "llm_assessment": "",
        "llm_indicators": [],
        "risk_result": {},
        "similar_patterns": 0,
        "analysis_id": "",
    }

    final_state = scam_agent.invoke(initial_state)

    content = final_state["llm_assessment"]

    def extract_field(label: str) -> str:
        for line in content.split("\n"):
            if line.strip().startswith(f"{label}:"):
                return line.split(":", 1)[1].strip()
        return ""

    scam_type = extract_field("SCAM_TYPE")
    verdict = extract_field("VERDICT")
    recommended_action = extract_field("RECOMMENDED_ACTION")

    indicators = [
        ScamIndicator(
            indicator=ind["indicator"],
            severity=RiskLevel(ind["severity"]) if ind["severity"] in RiskLevel._value2member_map_ else RiskLevel.MEDIUM,
            explanation=ind["explanation"]
        )
        for ind in final_state["llm_indicators"]
    ]

    response = ScamAnalysisResponse(
        risk_level=RiskLevel(final_state["risk_result"]["risk_level"]),
        risk_score=final_state["risk_result"]["risk_score"],
        scam_type=scam_type if scam_type != "LEGITIMATE" else None,
        indicators=indicators,
        verdict=verdict or "Analysis complete",
        recommended_action=recommended_action or "Exercise caution",
        similar_patterns_found=final_state["similar_patterns"],
        analysis_id=final_state["analysis_id"],
    )

    # Translate if non-English language requested
    if language and language != "en":
        try:
            from backend.core.translation import translate_verdict
            translated = translate_verdict(
                one_line_verdict=verdict,
                recommended_actions=[recommended_action],
                target_language=language,
            )
            response.translated_verdict = translated["translated_verdict"]
            response.translated_actions = translated["translated_actions"]
            response.target_language = language
        except Exception as e:
            logger.warning(f"Translation failed, falling back to English: {e}")
            response.target_language = "en"

    return response
