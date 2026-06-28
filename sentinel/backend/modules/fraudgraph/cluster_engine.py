import logging
from typing import List, Dict, Optional
import networkx as nx
from backend.models.fraud_models import Entity, Relationship, FraudCluster, RiskLevel

logger = logging.getLogger(__name__)

# Node colors for pyvis by entity type (SENTINEL dark theme)
NODE_COLORS = {
    "PHONE": "#FF6B6B",
    "ACCOUNT": "#FFD93D",
    "DEVICE": "#6BCB77",
    "VICTIM": "#4D96FF",
    "LOCATION": "#C77DFF",
}

DEFAULT_COLOR = "#AAAAAA"


class ClusterEngine:
    """
    Loads entities and relationships into networkx.
    Runs connected components analysis to find fraud rings.
    Computes betweenness centrality to find hub nodes.
    Generates pyvis HTML for Streamlit rendering.
    """

    def __init__(self):
        self.G = nx.DiGraph()

    def build_graph(self, entities: List[Entity], relationships: List[Relationship]):
        """Load entities and relationships into networkx DiGraph."""
        self.G.clear()

        for entity in entities:
            self.G.add_node(
                entity.id,
                label=f"{entity.type.value}\n{entity.value[:20]}",
                type=entity.type.value,
                value=entity.value
            )

        for rel in relationships:
            if rel.from_id in self.G.nodes and rel.to_id in self.G.nodes:
                self.G.add_edge(
                    rel.from_id,
                    rel.to_id,
                    rel_type=rel.rel_type,
                    weight=rel.weight
                )

    def analyze_clusters(self, entities: List[Entity]) -> List[FraudCluster]:
        """
        Find connected components (treated as fraud rings).
        Score each cluster by size, victim count, and connectivity.
        """
        if len(self.G.nodes) == 0:
            return []

        # Build entity lookup
        entity_map = {e.id: e for e in entities}

        # Find connected components (undirected view)
        undirected = self.G.to_undirected()
        components = list(nx.connected_components(undirected))

        # Betweenness centrality for hub detection
        try:
            centrality = nx.betweenness_centrality(self.G)
        except Exception:
            centrality = {node: 0.0 for node in self.G.nodes}

        clusters = []
        for i, component in enumerate(components):
            nodes_list = list(component)

            # Find hub (highest centrality in this component)
            hub_node = max(nodes_list, key=lambda n: centrality.get(n, 0), default=None)

            # Count victims in this cluster
            victim_count = sum(
                1 for nid in nodes_list
                if entity_map.get(nid) and entity_map[nid].type.value == "VICTIM"
            )

            # Risk score formula:
            account_count = sum(
                1 for nid in nodes_list
                if entity_map.get(nid) and entity_map[nid].type.value == "ACCOUNT"
            )
            total_nodes = max(len(self.G.nodes), 1)
            risk_score = min(
                (len(nodes_list) / total_nodes) * 0.5
                + victim_count * 0.2
                + account_count * 0.1,
                1.0
            )

            clusters.append(FraudCluster(
                cluster_id=i,
                nodes=nodes_list,
                size=len(nodes_list),
                hub_node=hub_node,
                victim_count=victim_count,
                risk_score=round(risk_score, 3)
            ))

        # Sort by risk score descending
        clusters.sort(key=lambda c: c.risk_score, reverse=True)
        return clusters

    def compute_risk_level(self, clusters: List[FraudCluster]) -> tuple:
        """
        Compute overall risk level from cluster analysis.
        Returns (RiskLevel, float risk_score)
        """
        if not clusters:
            return RiskLevel.LOW, 0.0

        max_score = max(c.risk_score for c in clusters)
        total_victims = sum(c.victim_count for c in clusters)
        large_clusters = sum(1 for c in clusters if c.size >= 3)

        adjusted = min(max_score + (large_clusters * 0.05) + (total_victims * 0.05), 1.0)

        if adjusted >= 0.8:
            return RiskLevel.CRITICAL, adjusted
        elif adjusted >= 0.6:
            return RiskLevel.HIGH, adjusted
        elif adjusted >= 0.35:
            return RiskLevel.MEDIUM, adjusted
        else:
            return RiskLevel.LOW, adjusted

    def generate_pyvis_html(self) -> str:
        """
        Generate interactive pyvis network visualization.
        SENTINEL dark theme with color-coded entity types.
        Returns HTML string for Streamlit st.components.v1.html().
        """
        try:
            from pyvis.network import Network

            net = Network(
                height="520px",
                width="100%",
                bgcolor="#0E1117",
                font_color="#FAFAFA",
                directed=True
            )

            # Add nodes with color by type
            for node_id, data in self.G.nodes(data=True):
                node_type = data.get("type", "PHONE")
                color = NODE_COLORS.get(node_type, DEFAULT_COLOR)
                label = data.get("label", node_id[:20])
                net.add_node(
                    node_id,
                    label=label,
                    color=color,
                    title=f"Type: {node_type}\nValue: {data.get('value', node_id)}",
                    size=20,
                    font={"color": "#FAFAFA", "size": 12}
                )

            # Add edges
            for from_id, to_id, data in self.G.edges(data=True):
                rel_type = data.get("rel_type", "CONNECTED")
                weight = data.get("weight", 1.0)
                net.add_edge(
                    from_id,
                    to_id,
                    label=rel_type,
                    width=max(weight * 2, 1),
                    color="#555555",
                    font={"color": "#AAAAAA", "size": 10}
                )

            # Physics settings for clean layout
            net.set_options("""
            {
              "physics": {
                "enabled": true,
                "barnesHut": {
                  "gravitationalConstant": -8000,
                  "centralGravity": 0.3,
                  "springLength": 150
                }
              },
              "interaction": {
                "hover": true,
                "tooltipDelay": 200
              }
            }
            """)

            return net.generate_html()

        except Exception as e:
            logger.error(f"Pyvis HTML generation failed: {e}")
            node_count = len(self.G.nodes)
            edge_count = len(self.G.edges)
            return f"""
            <html><body style="background:#0E1117;color:#FAFAFA;font-family:sans-serif;padding:20px;">
            <h3>Network: {node_count} nodes, {edge_count} edges</h3>
            <p>Graph visualization unavailable. Install pyvis: pip install pyvis</p>
            </body></html>
            """
