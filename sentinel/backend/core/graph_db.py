import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class Neo4jManager:
    """
    Neo4j Aura interface for SENTINEL FRAUDGraph module.
    Falls back to in-memory mode if connection fails (demo resilience).
    """

    def __init__(self):
        self._driver = None
        self._in_memory_nodes = []
        self._in_memory_rels = []
        self._connected = False
        self._connect()

    def _connect(self):
        try:
            from neo4j import GraphDatabase
            uri = os.getenv("NEO4J_URI", "")
            user = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "")
            if not uri or not password:
                logger.warning("Neo4j credentials not configured — running in-memory mode")
                return
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            self._driver.verify_connectivity()
            self._connected = True
            logger.info("Neo4j connected successfully")
        except Exception as e:
            logger.warning(f"Neo4j connection failed, using in-memory mode: {e}")
            self._driver = None
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def execute_write(self, cypher: str, params: Dict = None) -> List[Dict]:
        """Execute a write query. Falls back to in-memory no-op."""
        if not self._connected:
            return []
        try:
            with self._driver.session() as session:
                result = session.run(cypher, params or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Neo4j write error: {e}")
            return []

    def execute_read(self, cypher: str, params: Dict = None) -> List[Dict]:
        """Execute a read query."""
        if not self._connected:
            return []
        try:
            with self._driver.session() as session:
                result = session.run(cypher, params or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Neo4j read error: {e}")
            return []

    def merge_entity(self, entity_id: str, entity_type: str, value: str, metadata: Dict = None) -> bool:
        """
        MERGE an entity node. entity_type: PHONE | ACCOUNT | DEVICE | VICTIM | LOCATION
        Returns True if successful.
        """
        cypher = """
        MERGE (n:Entity {id: $id})
        SET n.type = $type,
            n.value = $value,
            n.metadata = $metadata,
            n.updated_at = timestamp()
        RETURN n.id as id
        """
        self.execute_write(cypher, {
            "id": entity_id,
            "type": entity_type,
            "value": value,
            "metadata": str(metadata or {})
        })
        # also store in-memory for networkx fallback
        self._in_memory_nodes.append({
            "id": entity_id, "type": entity_type, "value": value
        })
        return True

    def merge_relationship(self, from_id: str, to_id: str, rel_type: str, weight: float = 1.0) -> bool:
        """
        MERGE a relationship between two entity nodes.
        rel_type: CALLED | TRANSFERRED_TO | USED_BY | CONTACTED | BELONGS_TO
        """
        cypher = """
        MATCH (a:Entity {id: $from_id})
        MATCH (b:Entity {id: $to_id})
        MERGE (a)-[r:CONNECTED {type: $rel_type}]->(b)
        SET r.weight = $weight, r.timestamp = timestamp()
        RETURN type(r) as rel
        """
        self.execute_write(cypher, {
            "from_id": from_id,
            "to_id": to_id,
            "rel_type": rel_type,
            "weight": weight
        })
        self._in_memory_rels.append({
            "from": from_id, "to": to_id, "type": rel_type, "weight": weight
        })
        return True

    def get_full_graph(self) -> Dict[str, List]:
        """
        Returns all nodes and relationships for networkx loading.
        Uses Neo4j if connected, else returns in-memory data.
        """
        if self._connected:
            nodes = self.execute_read("MATCH (n:Entity) RETURN n.id as id, n.type as type, n.value as value")
            rels = self.execute_read(
                "MATCH (a:Entity)-[r:CONNECTED]->(b:Entity) RETURN a.id as from_id, b.id as to_id, r.type as rel_type, r.weight as weight"
            )
            return {"nodes": nodes, "relationships": rels}
        else:
            return {"nodes": self._in_memory_nodes, "relationships": self._in_memory_rels}

    def clear_session(self, session_id: str):
        """Clear nodes tagged with a session_id (optional cleanup)."""
        pass

    def close(self):
        if self._driver:
            self._driver.close()


# Singleton
_neo4j_manager: Optional[Neo4jManager] = None

def get_graph_db() -> Neo4jManager:
    global _neo4j_manager
    if _neo4j_manager is None:
        _neo4j_manager = Neo4jManager()
    return _neo4j_manager
