import uuid
import time
import logging
from typing import TypedDict, List, Optional, Dict, Any

from langgraph.graph import StateGraph, END
from backend.models.fraud_models import (
    Entity, Relationship, FraudCluster, RiskLevel,
    FraudAnalysisRequest, FraudAnalysisResponse
)
from backend.modules.fraudgraph.graph_builder import GraphBuilder
from backend.modules.fraudgraph.cluster_engine import ClusterEngine
from backend.modules.fraudgraph.report_builder import generate_fraud_report
from backend.core.llm import get_llm
from backend.core.intelligence_store import get_intelligence_store
from backend.core.graph_db import get_graph_db

logger = logging.getLogger(__name__)

# ── STATE ────────────────────────────────────────────────────────────────────

class FraudGraphState(TypedDict):
    session_id: str
    phones: List[str]
    accounts: List[str]
    devices: List[str]
    victim_statement: str
    entities: List[Entity]
    relationships: List[Relationship]
    clusters: List[FraudCluster]
    risk_level: str
    risk_score: float
    llm_summary: str
    graph_html: str
    pdf_path: str
    neo4j_connected: bool
    related_threats: List[Dict]
    error: Optional[str]

# ── NODES ────────────────────────────────────────────────────────────────────

def extract_entities_node(state: FraudGraphState) -> FraudGraphState:
    """Node 1: Parse structured inputs + LLM entity extraction from victim statement."""
    try:
        builder = GraphBuilder()
        entities, relationships = builder.build(
            phones=state["phones"],
            accounts=state["accounts"],
            devices=state["devices"],
            victim_statement=state["victim_statement"]
        )
        return {**state, "entities": entities, "relationships": relationships, "neo4j_connected": builder.graph_db.is_connected}
    except Exception as e:
        logger.error(f"extract_entities_node failed: {e}")
        return {**state, "error": str(e), "entities": [], "relationships": [], "neo4j_connected": False}


def build_graph_node(state: FraudGraphState) -> FraudGraphState:
    """Node 2: Build networkx graph + generate pyvis HTML."""
    try:
        engine = ClusterEngine()
        engine.build_graph(state["entities"], state["relationships"])
        graph_html = engine.generate_pyvis_html()
        return {**state, "graph_html": graph_html}
    except Exception as e:
        logger.error(f"build_graph_node failed: {e}")
        return {**state, "error": str(e), "graph_html": ""}


def cluster_node(state: FraudGraphState) -> FraudGraphState:
    """Node 3: Cluster analysis - fraud rings, hub nodes, risk scoring."""
    try:
        engine = ClusterEngine()
        engine.build_graph(state["entities"], state["relationships"])
        clusters = engine.analyze_clusters(state["entities"])
        risk_level, risk_score = engine.compute_risk_level(clusters)
        return {**state, "clusters": clusters, "risk_level": risk_level.value, "risk_score": risk_score}
    except Exception as e:
        logger.error(f"cluster_node failed: {e}")
        return {**state, "error": str(e), "clusters": [], "risk_level": "LOW", "risk_score": 0.0}


def llm_summary_node(state: FraudGraphState) -> FraudGraphState:
    """Node 4: Groq LLM generates intelligence summary."""
    try:
        llm = get_llm()

        entity_summary = "\n".join(
            f"- {e.type.value}: {e.value}" for e in state["entities"]
        )
        cluster_summary = "\n".join(
            f"- Ring {c.cluster_id+1}: {c.size} entities, {c.victim_count} victims, risk {c.risk_score:.1%}"
            for c in state["clusters"]
        )
        phone_count = sum(1 for e in state["entities"] if e.type.value == "PHONE")
        account_count = sum(1 for e in state["entities"] if e.type.value == "ACCOUNT")
        victim_count = sum(c.victim_count for c in state["clusters"])

        prompt = f"""You are a senior fraud intelligence analyst writing a classified report for Indian law enforcement.

CASE DATA:
Risk Level: {state['risk_level']}
Risk Score: {state['risk_score']:.1%}
Total Entities: {len(state['entities'])}
Phone Numbers: {phone_count}
Bank Accounts: {account_count}
Total Victims: {victim_count}
Fraud Rings Detected: {len(state['clusters'])}

ENTITIES:
{entity_summary if entity_summary else "None provided"}

FRAUD RINGS:
{cluster_summary if cluster_summary else "No rings detected"}

VICTIM STATEMENT:
{state['victim_statement'][:500] if state['victim_statement'] else "Not provided"}

Write a 3-paragraph intelligence summary covering:
1. Nature and scope of the fraud network
2. Key risk indicators and most suspicious entities/clusters
3. Recommended immediate actions for law enforcement

Use precise, professional language. Reference specific entities where relevant.
Keep each paragraph 3-4 sentences. Write for a law enforcement audience."""

        response = llm.invoke(prompt)
        summary = response.content.strip()
        return {**state, "llm_summary": summary}

    except Exception as e:
        logger.error(f"llm_summary_node failed: {e}")
        fallback = (
            f"SENTINEL has detected a {state.get('risk_level', 'UNKNOWN')} risk fraud network "
            f"comprising {len(state.get('entities', []))} entities across {len(state.get('clusters', []))} "
            f"fraud rings. LLM analysis unavailable. Manual review recommended."
        )
        return {**state, "llm_summary": fallback}


def report_node(state: FraudGraphState) -> FraudGraphState:
    """Node 5: Generate ReportLab PDF intelligence package."""
    try:
        pdf_path = generate_fraud_report(
            session_id=state["session_id"],
            entities=state["entities"],
            relationships=state["relationships"],
            clusters=state["clusters"],
            risk_level=RiskLevel(state["risk_level"]),
            risk_score=state["risk_score"],
            llm_summary=state["llm_summary"],
            neo4j_connected=state["neo4j_connected"]
        )
        return {**state, "pdf_path": pdf_path}
    except Exception as e:
        logger.error(f"report_node failed: {e}")
        return {**state, "pdf_path": "", "error": str(e)}


def store_intelligence_node(state: FraudGraphState) -> FraudGraphState:
    """Node 6: Store network signature in ChromaDB for cross-module correlation."""
    try:
        store = get_intelligence_store()

        # Store fraud network signature
        if state["risk_level"] in ("HIGH", "CRITICAL") or len(state["entities"]) > 0:
            entity_values = [e.value for e in state["entities"]]
            signature_text = (
                f"FRAUD NETWORK [{state['risk_level']}] "
                f"Entities: {', '.join(entity_values[:10])} "
                f"Rings: {len(state['clusters'])} "
                f"Summary: {state['llm_summary'][:300]}"
            )
            store.add_fraud_network(
                network_id=state["session_id"],
                description=signature_text,
                metadata={
                    "session_id": state["session_id"],
                    "risk_level": state["risk_level"],
                    "risk_score": state["risk_score"],
                    "entity_count": len(state["entities"]),
                    "cluster_count": len(state["clusters"]),
                }
            )

        # Query for related prior threats (cross-module — may find SCAMWatch hits)
        related = []
        try:
            query_text = " ".join(e.value for e in state["entities"][:5]) or "fraud network"
            scam_results = store.query_similar_scams(query_text, n_results=3)
            if scam_results and scam_results.get("ids"):
                for i, doc_id in enumerate(scam_results["ids"][0]):
                    related.append({
                        "id": doc_id,
                        "content": scam_results["documents"][0][i] if scam_results.get("documents") else "",
                        "metadata": scam_results["metadatas"][0][i] if scam_results.get("metadatas") else {},
                    })
        except Exception as e:
            logger.warning(f"Cross-module query failed: {e}")

        return {**state, "related_threats": related}

    except Exception as e:
        logger.error(f"store_intelligence_node failed: {e}")
        return {**state, "related_threats": []}


# ── GRAPH ────────────────────────────────────────────────────────────────────

def build_fraud_agent():
    graph = StateGraph(FraudGraphState)

    graph.add_node("extract_entities", extract_entities_node)
    graph.add_node("build_graph", build_graph_node)
    graph.add_node("cluster", cluster_node)
    graph.add_node("llm_summary", llm_summary_node)
    graph.add_node("report", report_node)
    graph.add_node("store_intelligence", store_intelligence_node)

    graph.set_entry_point("extract_entities")
    graph.add_edge("extract_entities", "build_graph")
    graph.add_edge("build_graph", "cluster")
    graph.add_edge("cluster", "llm_summary")
    graph.add_edge("llm_summary", "report")
    graph.add_edge("report", "store_intelligence")
    graph.add_edge("store_intelligence", END)

    return graph.compile()


fraud_agent = build_fraud_agent()


def run_fraud_analysis(request: FraudAnalysisRequest) -> FraudAnalysisResponse:
    """Entry point called by FastAPI."""
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    initial_state: FraudGraphState = {
        "session_id": session_id,
        "phones": request.phones,
        "accounts": request.accounts,
        "devices": request.devices,
        "victim_statement": request.victim_statement,
        "entities": [],
        "relationships": [],
        "clusters": [],
        "risk_level": "LOW",
        "risk_score": 0.0,
        "llm_summary": "",
        "graph_html": "",
        "pdf_path": "",
        "neo4j_connected": False,
        "related_threats": [],
        "error": None,
    }

    final_state = fraud_agent.invoke(initial_state)
    processing_time = int((time.time() - start_time) * 1000)

    return FraudAnalysisResponse(
        session_id=session_id,
        status="error" if final_state.get("error") else "success",
        entities=final_state["entities"],
        relationships=final_state["relationships"],
        clusters=final_state["clusters"],
        risk_level=RiskLevel(final_state["risk_level"]),
        risk_score=final_state["risk_score"],
        llm_summary=final_state["llm_summary"],
        graph_html=final_state["graph_html"],
        pdf_available=bool(final_state["pdf_path"]),
        neo4j_connected=final_state["neo4j_connected"],
        related_threats=final_state["related_threats"],
        processing_time_ms=processing_time,
    )
